"""Match numbered-road collisions to same-road DfT AADF count points."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/intermediate/int_collision_aadf_match.parquet"
SUMMARY = ROOT / "data/processed/week2_aadf_match_summary.json"

def main():
    usecols = ["collision_index","collision_year","location_easting_osgr","location_northing_osgr","first_road_class","first_road_number"]
    c = pd.read_csv(ROOT / "data/raw/dft-road-casualty-statistics-collision-last-5-years.csv", usecols=usecols, low_memory=False)
    road_class = pd.to_numeric(c.first_road_class, errors="coerce").astype("Int64")
    road_number = pd.to_numeric(c.first_road_number, errors="coerce").astype("Int64")
    c["road_name_normalized"] = pd.Series(pd.NA, index=c.index, dtype="string")
    for cls, prefix, suffix in [(1,"M",""),(2,"A","(M)"),(3,"A",""),(4,"B","")]:
        mask = road_class.eq(cls) & road_number.gt(0)
        c.loc[mask,"road_name_normalized"] = prefix + road_number[mask].astype("string") + suffix
    eligible = c[c.road_name_normalized.notna() & c.location_easting_osgr.notna() & c.location_northing_osgr.notna()].copy()
    a = pd.read_parquet(ROOT / "data/staging/stg_dft_aadf_2021_2025.parquet")
    a = a[a.all_motor_vehicles.gt(0) & a.easting.notna() & a.northing.notna()].copy()
    a["road_name_key"] = a.road_name.astype("string").str.upper()
    candidate_groups = {(int(year), str(road)): frame.reset_index(drop=True) for (year, road), frame in a.groupby(["year","road_name_key"], sort=False)}
    outputs = []
    for (year, road), group in eligible.groupby(["collision_year","road_name_normalized"], sort=False):
        candidates = candidate_groups.get((int(year), str(road).upper()))
        if candidates is None: continue
        tree = cKDTree(candidates[["easting","northing"]].to_numpy(float))
        distance, position = tree.query(group[["location_easting_osgr","location_northing_osgr"]].to_numpy(float), k=1)
        matched = candidates.iloc[position].reset_index(drop=True)
        out = group[["collision_index","collision_year","road_name_normalized"]].reset_index(drop=True)
        out["count_point_id"] = matched.count_point_id.to_numpy()
        out["distance_m"] = distance
        out["aadf_all_motor_vehicles"] = matched.all_motor_vehicles.to_numpy()
        out["estimation_method"] = matched.estimation_method.to_numpy()
        outputs.append(out)
    result = pd.concat(outputs, ignore_index=True) if outputs else pd.DataFrame()
    result["match_band"] = pd.cut(result.distance_m, [-1,50,100,250,500,1000,np.inf], labels=["<=50m","51-100m","101-250m","251-500m","501-1000m",">1000m"])
    result.to_parquet(OUT, index=False)
    eligible_count = len(eligible)
    summary = {
        "grain":"one row per eligible collision with a same-year, same-road AADF candidate",
        "eligible_numbered_road_collisions":eligible_count,
        "same_road_candidate_matches":len(result),
        "same_road_candidate_rate":round(len(result)/eligible_count,6),
        "within_50m":int((result.distance_m<=50).sum()),
        "within_100m":int((result.distance_m<=100).sum()),
        "within_250m":int((result.distance_m<=250).sum()),
        "within_500m":int((result.distance_m<=500).sum()),
        "within_100m_rate_of_eligible":round(float((result.distance_m<=100).sum()/eligible_count),6),
        "within_250m_rate_of_eligible":round(float((result.distance_m<=250).sum()/eligible_count),6),
        "counted_share_within_250m":round(float(result.loc[result.distance_m<=250,"estimation_method"].eq("Counted").mean()),6),
        "median_distance_m":round(float(result.distance_m.median()),1),
        "p90_distance_m":round(float(result.distance_m.quantile(.9)),1),
        "recommended_high_confidence_rule":"same year + same normalized road + distance <=100m + positive AADF",
        "recommended_sensitivity_rule":"same year + same normalized road + distance <=250m + positive AADF; split Counted vs Estimated",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__": main()
