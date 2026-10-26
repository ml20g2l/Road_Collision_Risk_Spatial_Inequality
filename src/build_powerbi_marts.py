"""Build Power BI-ready star-schema tables and exposure sensitivity outputs."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/powerbi"
OUT.mkdir(parents=True, exist_ok=True)

def main():
    context = pd.read_parquet(ROOT / "data/intermediate/int_collision_context.parquet")
    match = pd.read_parquet(ROOT / "data/intermediate/int_collision_aadf_match.parquet")
    traffic = pd.read_parquet(ROOT / "data/staging/stg_dft_local_authority_traffic.parquet")
    iod = pd.read_parquet(ROOT / "data/staging/stg_iod2025_lsoa.parquet")

    match = match.rename(columns={"estimation_method":"aadf_estimation_method"})
    fact = context.merge(match, on=["collision_index","collision_year"], how="left", validate="one_to_one")
    fact.loc[~fact.lsoa_code_2021.astype("string").str.startswith("E", na=False), "lsoa_code_2021"] = pd.NA
    fact["date_key"] = pd.to_datetime(fact.collision_date).dt.strftime("%Y%m%d").astype("Int64")
    fact["is_fatal"] = fact.collision_severity.eq(1)
    fact["is_fatal_or_serious_raw"] = fact.collision_severity.isin([1,2])
    fact["expected_adjusted_ksi"] = fact.is_fatal.astype(float) + fact.collision_adjusted_severity_serious.astype(float)
    fact["aadf_match_tier"] = np.select(
        [fact.distance_m.le(100), fact.distance_m.le(250)],
        ["high_confidence_100m", "sensitivity_250m"], default="not_eligible")
    fact["aadf_counted_high_confidence"] = fact.distance_m.le(100) & fact.aadf_estimation_method.eq("Counted")
    fact_columns = [
        "collision_index","date_key","collision_year","local_authority_highway_current","lsoa_code_2021",
        "imd_decile","longitude","latitude","collision_severity","is_fatal","is_fatal_or_serious_raw",
        "expected_adjusted_ksi","speed_limit","road_type","urban_or_rural_area","light_conditions",
        "weather_conditions","road_surface_conditions","count_point_id","distance_m","aadf_all_motor_vehicles",
        "aadf_estimation_method","aadf_match_tier","aadf_counted_high_confidence","lsoa_mapping_method",
    ]
    fact[fact_columns].to_parquet(OUT / "fact_collision.parquet", index=False)

    dates = pd.DataFrame({"date":pd.date_range(context.collision_date.min(), context.collision_date.max(), freq="D")})
    dates["date_key"] = dates.date.dt.strftime("%Y%m%d").astype(int)
    dates["year"], dates["quarter"], dates["month"] = dates.date.dt.year, dates.date.dt.quarter, dates.date.dt.month
    dates["month_name"], dates["day_of_week"] = dates.date.dt.month_name(), dates.date.dt.day_name()
    dates["is_weekend"] = dates.date.dt.dayofweek.ge(5)
    dates.to_parquet(OUT / "dim_date.parquet", index=False)
    iod.rename(columns={"lsoa_code":"lsoa_code_2021"}).to_parquet(OUT / "dim_lsoa.parquet", index=False)

    authority_names = traffic[["local_authority_code","local_authority_name"]].drop_duplicates("local_authority_code")
    dim_la = context[["local_authority_highway_current","traffic_join_code"]].drop_duplicates()
    dim_la = dim_la.merge(authority_names, left_on="traffic_join_code", right_on="local_authority_code", how="left")
    dim_la = dim_la.drop(columns="local_authority_code").drop_duplicates("local_authority_highway_current")
    dim_la.to_parquet(OUT / "dim_local_authority.parquet", index=False)

    risk = fact.groupby(["collision_year","local_authority_highway_current"], dropna=False).agg(
        collisions=("collision_index","size"), fatalities=("is_fatal","sum"),
        raw_ksi=("is_fatal_or_serious_raw","sum"), adjusted_expected_ksi=("expected_adjusted_ksi","sum"),
        annual_vehicle_miles=("annual_vehicle_miles","first"),
        aadf_100m_matches=("distance_m",lambda s:int(s.le(100).sum())),
        aadf_250m_matches=("distance_m",lambda s:int(s.le(250).sum())),
    ).reset_index()
    risk["exposure_available"] = risk.annual_vehicle_miles.notna() & risk.annual_vehicle_miles.gt(0)
    for numerator, output in [("collisions","collisions_per_billion_vehicle_miles"),("raw_ksi","raw_ksi_per_billion_vehicle_miles"),("adjusted_expected_ksi","adjusted_ksi_per_billion_vehicle_miles")]:
        risk[output] = risk[numerator] / risk.annual_vehicle_miles * 1e9
    risk.to_parquet(OUT / "fact_local_authority_year_risk.parquet", index=False)

    eligible = fact.road_name_normalized.notna() if "road_name_normalized" in fact else context.first_road_class.isin([1,2,3,4])
    rows = []
    for year, group in fact.groupby("collision_year"):
        eligible_year = group.first_road_class.isin([1,2,3,4]) & group.first_road_number.gt(0) if "first_road_class" in group else pd.Series(True,index=group.index)
        denominator = int(eligible_year.sum())
        scenarios = [
            ("la_vehicle_miles","Authority-year vehicle miles",group.annual_vehicle_miles.notna()),
            ("aadf_100m_all","Same road AADF ≤100m",group.distance_m.le(100)),
            ("aadf_100m_counted","Counted AADF ≤100m",group.distance_m.le(100) & group.aadf_estimation_method.eq("Counted")),
            ("aadf_250m_all","Same road AADF ≤250m",group.distance_m.le(250)),
        ]
        for key, label, mask in scenarios:
            base = len(group) if key == "la_vehicle_miles" else denominator
            rows.append({"collision_year":int(year),"scenario_key":key,"scenario_label":label,"covered_collisions":int(mask.sum()),"eligible_collisions":int(base),"coverage_rate":float(mask.sum()/base) if base else None,"supports_absolute_rate":key=="la_vehicle_miles"})
    sensitivity = pd.DataFrame(rows)
    sensitivity.to_parquet(OUT / "fact_exposure_sensitivity.parquet", index=False)
    sensitivity[["scenario_key","scenario_label","supports_absolute_rate"]].drop_duplicates().to_parquet(OUT / "dim_exposure_scenario.parquet", index=False)

    contract = {
      "model":"Road Collision Risk & Spatial Inequality","grain":{"fact_collision":"collision_index","fact_local_authority_year_risk":"collision_year + local_authority_highway_current","fact_exposure_sensitivity":"collision_year + scenario_key"},
      "relationships":[
        {"from":"fact_collision.date_key","to":"dim_date.date_key","cardinality":"many-to-one"},
        {"from":"fact_collision.lsoa_code_2021","to":"dim_lsoa.lsoa_code_2021","cardinality":"many-to-one"},
        {"from":"fact_collision.local_authority_highway_current","to":"dim_local_authority.local_authority_highway_current","cardinality":"many-to-one"},
        {"from":"fact_exposure_sensitivity.scenario_key","to":"dim_exposure_scenario.scenario_key","cardinality":"many-to-one"}],
      "certified_metrics":{"Collision Count":"COUNTROWS(fact_collision)","Raw KSI":"SUM(fact_collision[is_fatal_or_serious_raw])","Adjusted Expected KSI":"SUM(fact_collision[expected_adjusted_ksi])","Raw KSI per Billion Vehicle Miles":"DIVIDE(SUMX(FILTER(fact_local_authority_year_risk, fact_local_authority_year_risk[exposure_available]), fact_local_authority_year_risk[raw_ksi]),SUM(fact_local_authority_year_risk[annual_vehicle_miles]))*1000000000","Adjusted KSI per Billion Vehicle Miles":"DIVIDE(SUMX(FILTER(fact_local_authority_year_risk, fact_local_authority_year_risk[exposure_available]), fact_local_authority_year_risk[adjusted_expected_ksi]),SUM(fact_local_authority_year_risk[annual_vehicle_miles]))*1000000000"},
      "guardrail":"AADF scenarios are coverage/sensitivity diagnostics only until road-segment geometry matching is implemented; do not expose them as absolute risk rates."
    }
    (OUT / "model_contract.json").write_text(json.dumps(contract,indent=2),encoding="utf-8")
    print(json.dumps({"fact_collision":len(fact),"risk_rows":len(risk),"sensitivity_rows":len(sensitivity)},indent=2))

if __name__ == "__main__": main()
