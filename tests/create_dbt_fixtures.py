"""Create deterministic Parquet fixtures for CI dbt builds."""

from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "fixtures" / "powerbi"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    years = list(range(2021, 2026))
    collision_rows = []
    for index, decile in enumerate(range(1, 11), start=1):
        year = years[(index - 1) % len(years)]
        collision_rows.append(
            {
                "collision_index": f"C{index:03d}",
                "date_key": int(f"{year}0101"),
                "collision_year": year,
                "local_authority_highway_current": "E00000001" if index % 2 else "E00000002",
                "lsoa_code_2021": f"E010000{index:02d}",
                "imd_decile": decile,
                "collision_severity": 1 if index == 1 else (2 if index % 3 == 0 else 3),
                "expected_adjusted_ksi": 1.0 if index == 1 else (0.7 if index % 3 == 0 else 0.0),
                "is_fatal_or_serious_raw": index == 1 or index % 3 == 0,
                "aadf_match_tier": "high_confidence_100m" if index % 2 else "not_eligible",
                "urban_or_rural_area_label": "Urban" if index % 2 else "Rural",
            }
        )
    fact = pd.DataFrame(collision_rows)
    fact.to_parquet(OUT / "fact_collision.parquet", index=False)

    dates = pd.DataFrame({"date": pd.to_datetime([f"{year}-01-01" for year in years])})
    dates["date_key"] = dates.date.dt.strftime("%Y%m%d").astype(int)
    dates.to_parquet(OUT / "dim_date.parquet", index=False)
    pd.DataFrame({"collision_year": years, "year_label": [str(y) for y in years]}).to_parquet(
        OUT / "dim_year.parquet", index=False
    )
    pd.DataFrame(
        {
            "lsoa_code_2021": [f"E010000{i:02d}" for i in range(1, 11)],
            "imd_decile": list(range(1, 11)),
            "population_mid_2022": [10_000] * 10,
        }
    ).to_parquet(OUT / "dim_lsoa.parquet", index=False)
    pd.DataFrame({"local_authority_highway_current": ["E00000001", "E00000002"]}).to_parquet(
        OUT / "dim_local_authority.parquet", index=False
    )

    risk_rows = []
    for year in years:
        for authority in ("E00000001", "E00000002"):
            group = fact[(fact.collision_year == year) & (fact.local_authority_highway_current == authority)]
            risk_rows.append(
                {
                    "collision_year": year,
                    "local_authority_highway_current": authority,
                    "collisions": len(group),
                    "raw_ksi": int(group.is_fatal_or_serious_raw.sum()),
                    "adjusted_expected_ksi": float(group.expected_adjusted_ksi.sum()),
                    "annual_vehicle_miles": 100_000_000.0,
                    "exposure_available": True,
                }
            )
    pd.DataFrame(risk_rows).to_parquet(OUT / "fact_local_authority_year_risk.parquet", index=False)

    scenarios = [
        ("la_vehicle_miles", "Authority-year vehicle miles", True, 2),
        ("aadf_100m_all", "Same road AADF <=100m", False, 1),
        ("aadf_100m_counted", "Counted AADF <=100m", False, 1),
        ("aadf_250m_all", "Same road AADF <=250m", False, 2),
    ]
    sensitivity_rows = []
    for year in years:
        for key, label, supports, covered in scenarios:
            sensitivity_rows.append(
                {
                    "collision_year": year,
                    "scenario_key": key,
                    "scenario_label": label,
                    "covered_collisions": covered,
                    "eligible_collisions": 2,
                    "coverage_rate": covered / 2,
                    "supports_absolute_rate": supports,
                }
            )
    pd.DataFrame(sensitivity_rows).to_parquet(OUT / "fact_exposure_sensitivity.parquet", index=False)
    pd.DataFrame(
        [
            {"scenario_key": key, "scenario_label": label, "supports_absolute_rate": supports}
            for key, label, supports, _ in scenarios
        ]
    ).to_parquet(OUT / "dim_exposure_scenario.parquet", index=False)


if __name__ == "__main__":
    main()
