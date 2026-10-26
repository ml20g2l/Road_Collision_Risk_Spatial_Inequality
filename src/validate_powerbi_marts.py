"""Validate Power BI star-schema grains, relationships, and metric contracts."""
import json
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/powerbi"
fact = pd.read_parquet(P / "fact_collision.parquet")
date = pd.read_parquet(P / "dim_date.parquet")
lsoa = pd.read_parquet(P / "dim_lsoa.parquet")
la = pd.read_parquet(P / "dim_local_authority.parquet")
risk = pd.read_parquet(P / "fact_local_authority_year_risk.parquet")
sensitivity = pd.read_parquet(P / "fact_exposure_sensitivity.parquet")
contract = json.loads((P / "model_contract.json").read_text())
assert len(fact) == 513801 and not fact.collision_index.duplicated().any()
assert not date.date_key.duplicated().any() and fact.date_key.isin(date.date_key).all()
assert not lsoa.lsoa_code_2021.duplicated().any()
assert fact.loc[fact.lsoa_code_2021.notna(),"lsoa_code_2021"].isin(lsoa.lsoa_code_2021).all()
assert not la.local_authority_highway_current.duplicated().any()
assert fact.local_authority_highway_current.astype(str).isin(la.local_authority_highway_current.astype(str)).all()
assert not risk.duplicated(["collision_year","local_authority_highway_current"]).any()
assert int(risk.collisions.sum()) == len(fact)
assert not sensitivity.duplicated(["collision_year","scenario_key"]).any()
assert sensitivity.coverage_rate.between(0,1).all()
assert set(sensitivity.loc[sensitivity.supports_absolute_rate,"scenario_key"]) == {"la_vehicle_miles"}
assert "AADF scenarios are coverage/sensitivity diagnostics" in contract["guardrail"]
print("Power BI mart validation passed")
