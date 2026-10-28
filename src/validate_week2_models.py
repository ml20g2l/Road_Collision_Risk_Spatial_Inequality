"""Fail fast on stable Week 2 data contracts."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
qa = json.loads((ROOT / "data/processed/week2_qa_summary.json").read_text())
assert qa["build_status"] == "complete"
assert all(v == 0 for v in qa["uniqueness"].values())
assert qa["validity"]["iod_decile_outside_1_10"] == 0
assert qa["join_coverage"]["england_to_iod_join_rate"] == 1.0
assert qa["join_coverage"]["collision_to_la_traffic_join_rate"] >= 0.999
context = pd.read_parquet(ROOT / "data/intermediate/int_collision_context.parquet")
mart = pd.read_parquet(ROOT / "data/marts/mart_local_authority_collision_risk.parquet")
assert len(context) == qa["row_counts"]["collisions"]
assert int(mart["collisions"].sum()) == len(context)
assert (mart["fatal_or_serious"] <= mart["collisions"]).all()
match_qa = json.loads((ROOT / "data/processed/week2_aadf_match_summary.json").read_text())
assert match_qa["within_100m"] <= match_qa["within_250m"] <= match_qa["same_road_candidate_matches"]
matches = pd.read_parquet(ROOT / "data/intermediate/int_collision_aadf_match.parquet")
assert not matches["collision_index"].duplicated().any()
assert (matches["aadf_all_motor_vehicles"] > 0).all()
print("Week 2 model validation passed")
