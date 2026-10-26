"""Build Week 2 staging/intermediate/mart datasets and a QA report."""
from __future__ import annotations
import hashlib, json, zipfile
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, AUX = ROOT / "data/raw", ROOT / "data/raw/auxiliary"
STAGING, INTERMEDIATE, MARTS = ROOT / "data/staging", ROOT / "data/intermediate", ROOT / "data/marts"
PROCESSED = ROOT / "data/processed"
MISSING_CODES = {-1: "unknown", -2: "not_applicable", -3: "self_reported_or_untraced"}

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1048576), b""): h.update(block)
    return h.hexdigest()

def clean_code(df, col):
    s = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    df[f"{col}_missing_reason"] = s.map(MISSING_CODES).astype("string")
    df[col] = s.mask(s.isin(MISSING_CODES))

def read_zip_csv(path):
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1: raise ValueError(f"Expected one CSV in {path}: {names}")
        with z.open(names[0]) as f: return pd.read_csv(f, low_memory=False)

def main():
    for p in (STAGING, INTERMEDIATE, MARTS, PROCESSED): p.mkdir(parents=True, exist_ok=True)
    collision_path = RAW / "dft-road-casualty-statistics-collision-last-5-years.csv"
    c = pd.read_csv(collision_path, low_memory=False)
    c["collision_date"] = pd.to_datetime(c["date"], format="%d/%m/%Y", errors="coerce")
    c["collision_year"] = pd.to_numeric(c["collision_year"], errors="coerce").astype("Int64")
    for col in ["collision_severity","road_type","speed_limit","junction_detail","junction_control","light_conditions","weather_conditions","road_surface_conditions","urban_or_rural_area","trunk_road_flag"]: clean_code(c, col)
    c.to_parquet(STAGING / "stg_stats19_collisions.parquet", index=False)

    iod0 = pd.read_csv(AUX / "iod2025_file7_v2.csv", low_memory=False)
    iod = iod0.rename(columns={"LSOA code (2021)":"lsoa_code","LSOA name (2021)":"lsoa_name","Local Authority District code (2024)":"lad_code_2024","Local Authority District name (2024)":"lad_name_2024","Index of Multiple Deprivation (IMD) Score":"imd_score","Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)":"imd_rank","Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)":"imd_decile","Total population: mid 2022":"population_mid_2022"})[["lsoa_code","lsoa_name","lad_code_2024","lad_name_2024","imd_score","imd_rank","imd_decile","population_mid_2022"]]
    iod.to_parquet(STAGING / "stg_iod2025_lsoa.parquet", index=False)
    lookup = pd.read_csv(AUX / "ons_lsoa11_lsoa21_lad22_best_fit_v2.csv", dtype="string")
    lookup.to_parquet(STAGING / "stg_ons_lsoa11_lsoa21_best_fit.parquet", index=False)
    traffic = pd.read_csv(AUX / "local_authority_traffic.csv").rename(columns={"all_motor_vehicles":"annual_vehicle_miles"})
    traffic.to_parquet(STAGING / "stg_dft_local_authority_traffic.parquet", index=False)
    cp, aadf = read_zip_csv(AUX / "count_points.zip"), read_zip_csv(AUX / "dft_traffic_counts_aadf.zip")
    aadf5 = aadf[aadf.year.between(2021, 2025)].copy()
    cp.to_parquet(STAGING / "stg_dft_count_points_2025.parquet", index=False)
    aadf5.to_parquet(STAGING / "stg_dft_aadf_2021_2025.parquet", index=False)

    england = c.lsoa_of_accident_location.astype("string").str.startswith("E", na=False)
    lsoa_map = lookup.set_index("LSOA11CD")["LSOA21CD"]
    direct = c.lsoa_of_accident_location.isin(set(iod.lsoa_code))
    c["lsoa_code_2021"] = c.lsoa_of_accident_location.where(direct, c.lsoa_of_accident_location.map(lsoa_map))
    c["lsoa_mapping_method"] = "not_applicable"
    c.loc[england & direct, "lsoa_mapping_method"] = "direct_2021_code"
    c.loc[england & ~direct & c.lsoa_code_2021.notna(), "lsoa_mapping_method"] = "ons_best_fit_2011_to_2021"
    c.loc[england & c.lsoa_code_2021.isna(), "lsoa_mapping_method"] = "unmatched"
    # DfT traffic retains legacy Sheffield/Barnsley codes in 2025. Historical
    # STATS19 highway codes are preferred; only the two 2025 boundary codes need recoding.
    c["traffic_join_code"] = c.local_authority_highway.astype("string").replace({"E08000038":"E08000016", "E08000039":"E08000019"})
    e = c.merge(iod, how="left", left_on="lsoa_code_2021", right_on="lsoa_code", validate="many_to_one")
    e = e.merge(traffic[["local_authority_code","year","annual_vehicle_miles"]], how="left", left_on=["traffic_join_code","collision_year"], right_on=["local_authority_code","year"], validate="many_to_one")
    e["is_fatal_or_serious"] = e.collision_severity.isin([1,2])
    e.to_parquet(INTERMEDIATE / "int_collision_context.parquet", index=False)
    lm = e[england].groupby(["collision_year","lsoa_code","imd_decile"], dropna=False).agg(collisions=("collision_index","size"),fatal_or_serious=("is_fatal_or_serious","sum")).reset_index()
    lm["fatal_or_serious_share"] = lm.fatal_or_serious / lm.collisions
    lm.to_parquet(MARTS / "mart_lsoa_collision_inequality.parquet", index=False)
    am = e.groupby(["collision_year","local_authority_highway_current"], dropna=False).agg(collisions=("collision_index","size"),fatal_or_serious=("is_fatal_or_serious","sum"),annual_vehicle_miles=("annual_vehicle_miles","first")).reset_index()
    am["collisions_per_billion_vehicle_miles"] = am.collisions / am.annual_vehicle_miles * 1e9
    am["fatal_or_serious_per_billion_vehicle_miles"] = am.fatal_or_serious / am.annual_vehicle_miles * 1e9
    am.to_parquet(MARTS / "mart_local_authority_collision_risk.parquet", index=False)

    iod_ok = e.loc[england,"imd_decile"].notna(); traffic_ok = e.annual_vehicle_miles.notna()
    by_year = e.loc[england].groupby("collision_year").agg(rows=("collision_index","size"),iod_joined=("imd_decile",lambda s:int(s.notna().sum())),traffic_joined=("annual_vehicle_miles",lambda s:int(s.notna().sum()))).reset_index()
    by_year["iod_join_rate"] = by_year.iod_joined / by_year.rows
    by_year["traffic_join_rate"] = by_year.traffic_joined / by_year.rows
    by_year.to_csv(PROCESSED / "week2_join_coverage_by_year.csv", index=False)
    qa = {"build_status":"complete","period":"2021-2025","grains":{"stats19_collision":"collision_index","iod2025":"lsoa_code (2021)","lsoa_lookup":"one row per LSOA11CD (best fit)","local_authority_traffic":"local_authority_code + year","aadf":"count_point_id + year"},"row_counts":{"collisions":len(c),"iod_lsoa":len(iod),"lsoa_lookup":len(lookup),"local_authority_traffic":len(traffic),"count_points":len(cp),"aadf_2021_2025":len(aadf5),"lsoa_mart":len(lm),"la_mart":len(am)},"uniqueness":{"collision_duplicate_keys":int(c.collision_index.duplicated().sum()),"iod_duplicate_lsoa":int(iod.lsoa_code.duplicated().sum()),"lsoa_lookup_duplicate_2011":int(lookup.LSOA11CD.duplicated().sum()),"la_traffic_duplicate_key":int(traffic.duplicated(["local_authority_code","year"]).sum()),"aadf_duplicate_key":int(aadf.duplicated(["count_point_id","year"]).sum()),"count_points_duplicate_id":int(cp.count_point_id.duplicated().sum())},"join_coverage":{"england_collision_rows":int(england.sum()),"england_to_iod_joined_rows":int(iod_ok.sum()),"england_to_iod_join_rate":round(float(iod_ok.mean()),6),"collision_to_la_traffic_joined_rows":int(traffic_ok.sum()),"collision_to_la_traffic_join_rate":round(float(traffic_ok.mean()),6)},"validity":{"iod_decile_outside_1_10":int((~iod.imd_decile.between(1,10)).sum()),"aadf_nonpositive_motor_vehicle_flow":int((aadf5.all_motor_vehicles<=0).sum()),"aadf_missing_coordinates":int(aadf5[["latitude","longitude"]].isna().any(axis=1).sum()),"aadf_estimated_share":round(float(aadf5.estimation_method.eq("Estimated").mean()),6)},"source_files":[{"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size,"sha256":sha256(p)} for p in [collision_path,AUX/"iod2025_file7_v2.csv",AUX/"ons_lsoa11_lsoa21_lad22_best_fit_v2.csv",AUX/"count_points.zip",AUX/"dft_traffic_counts_aadf.zip",AUX/"local_authority_traffic.csv"]]}
    (PROCESSED / "week2_qa_summary.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    print(json.dumps(qa, indent=2))

if __name__ == "__main__": main()
