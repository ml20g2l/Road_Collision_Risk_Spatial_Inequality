import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_source_manifest_has_unique_names_and_checksums() -> None:
    payload = json.loads((ROOT / "data/metadata/source_manifest.json").read_text(encoding="utf-8"))
    sources = payload["sources"]
    names = [source.get("name", source["file"]) for source in sources]
    assert len(names) == len(set(names))
    assert all(len(source["sha256"]) == 64 for source in sources)


def test_model_contract_declares_three_fact_grains() -> None:
    contract = json.loads((ROOT / "data/powerbi/model_contract.json").read_text(encoding="utf-8"))
    assert set(contract["grain"]) == {
        "fact_collision",
        "fact_local_authority_year_risk",
        "fact_exposure_sensitivity",
    }


def test_exposure_guardrail_restricts_aadf() -> None:
    contract = json.loads((ROOT / "data/powerbi/model_contract.json").read_text(encoding="utf-8"))
    assert "do not expose" in contract["guardrail"].lower()


def test_public_annual_series_has_one_row_per_year() -> None:
    frame = pd.read_csv(ROOT / "data/public/annual_exposure_adjusted_ksi.csv")
    assert frame.collision_year.tolist() == [2021, 2022, 2023, 2024, 2025]
    assert not frame.collision_year.duplicated().any()


def test_deprivation_summary_has_all_deciles() -> None:
    frame = pd.read_csv(ROOT / "data/public/deprivation_decile_summary.csv")
    assert set(frame.imd_decile) == set(range(1, 11))
    assert frame.collisions_per_100k_resident_years.gt(0).all()


def test_deprivation_gap_is_positive_and_finite() -> None:
    frame = pd.read_csv(ROOT / "data/public/deprivation_gap_by_year.csv")
    assert frame.most_to_least_ratio.between(1, 10).all()


def test_speed_limit_output_uses_expected_categories() -> None:
    frame = pd.read_csv(ROOT / "data/public/severity_by_speed_limit.csv")
    assert set(frame.speed_limit) == {20, 30, 40, 50, 60, 70}


def test_urban_rural_output_rates_are_bounded() -> None:
    frame = pd.read_csv(ROOT / "data/public/severity_by_urban_rural.csv")
    assert frame.adjusted_ksi_per_100_collisions.between(0, 100).all()
