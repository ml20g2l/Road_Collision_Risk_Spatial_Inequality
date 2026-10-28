"""Build small, publication-ready extracts for the portfolio analysis."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
POWERBI = ROOT / "data" / "powerbi"
OUTPUT = ROOT / "data" / "public"


def build_deprivation_outputs(collisions: pd.DataFrame, lsoas: pd.DataFrame) -> None:
    """Summarise collision burden and severity by deprivation decile."""
    england = collisions.merge(
        lsoas[["lsoa_code_2021", "population_mid_2022"]],
        on="lsoa_code_2021",
        how="inner",
        validate="many_to_one",
    )
    england = england[england["imd_decile"].notna()].copy()

    summary = (
        england.groupby("imd_decile", observed=True)
        .agg(
            collisions=("collision_index", "size"),
            raw_ksi=("is_fatal_or_serious_raw", "sum"),
            adjusted_expected_ksi=("expected_adjusted_ksi", "sum"),
        )
        .reset_index()
    )
    population = (
        lsoas[lsoas["imd_decile"].notna()]
        .groupby("imd_decile", observed=True)["population_mid_2022"]
        .sum()
        .rename("population_mid_2022")
        .reset_index()
    )
    summary = summary.merge(population, on="imd_decile", validate="one_to_one")
    summary["collisions_per_100k_resident_years"] = (
        summary["collisions"] / (summary["population_mid_2022"] * 5) * 100_000
    )
    summary["adjusted_ksi_per_100_collisions"] = summary["adjusted_expected_ksi"] / summary["collisions"] * 100
    summary.to_csv(OUTPUT / "deprivation_decile_summary.csv", index=False)

    annual = (
        england.groupby(["collision_year", "imd_decile"], observed=True)
        .size()
        .rename("collisions")
        .reset_index()
        .merge(population, on="imd_decile", validate="many_to_one")
    )
    annual["collisions_per_100k_residents"] = annual["collisions"] / annual["population_mid_2022"] * 100_000
    gap = annual[annual["imd_decile"].isin([1, 10])].pivot(
        index="collision_year",
        columns="imd_decile",
        values="collisions_per_100k_residents",
    )
    gap = gap.rename(columns={1: "most_deprived", 10: "least_deprived"}).reset_index()
    gap["most_to_least_ratio"] = gap["most_deprived"] / gap["least_deprived"]
    gap.to_csv(OUTPUT / "deprivation_gap_by_year.csv", index=False)


def build_severity_outputs(collisions: pd.DataFrame) -> None:
    """Summarise adjusted expected severity by road context."""
    collisions = collisions.copy()
    collisions["area_type"] = collisions["urban_or_rural_area"].map({1: "Urban", 2: "Rural", 3: "Unallocated"})
    urban_rural = (
        collisions.groupby(["collision_year", "area_type"], observed=True)
        .agg(
            collisions=("collision_index", "size"),
            adjusted_expected_ksi=("expected_adjusted_ksi", "sum"),
        )
        .reset_index()
    )
    urban_rural["adjusted_ksi_per_100_collisions"] = (
        urban_rural["adjusted_expected_ksi"] / urban_rural["collisions"] * 100
    )
    urban_rural.to_csv(OUTPUT / "severity_by_urban_rural.csv", index=False)

    speed = (
        collisions[collisions["speed_limit"].isin([20, 30, 40, 50, 60, 70])]
        .groupby("speed_limit", observed=True)
        .agg(
            collisions=("collision_index", "size"),
            adjusted_expected_ksi=("expected_adjusted_ksi", "sum"),
        )
        .reset_index()
    )
    speed["adjusted_ksi_per_100_collisions"] = speed["adjusted_expected_ksi"] / speed["collisions"] * 100
    speed.to_csv(OUTPUT / "severity_by_speed_limit.csv", index=False)


def build_exposure_output(risk: pd.DataFrame) -> None:
    """Create the national annual raw-versus-adjusted exposure summary."""
    covered = risk[risk["exposure_available"]].copy()
    annual = (
        covered.groupby("collision_year", observed=True)
        .agg(
            raw_ksi=("raw_ksi", "sum"),
            adjusted_expected_ksi=("adjusted_expected_ksi", "sum"),
            annual_vehicle_miles=("annual_vehicle_miles", "sum"),
        )
        .reset_index()
    )
    annual["raw_ksi_per_billion_vehicle_miles"] = annual["raw_ksi"] / annual["annual_vehicle_miles"] * 1_000_000_000
    annual["adjusted_ksi_per_billion_vehicle_miles"] = (
        annual["adjusted_expected_ksi"] / annual["annual_vehicle_miles"] * 1_000_000_000
    )
    annual["adjustment_percent"] = (
        annual["adjusted_ksi_per_billion_vehicle_miles"] / annual["raw_ksi_per_billion_vehicle_miles"] - 1
    ) * 100
    annual.to_csv(OUTPUT / "annual_exposure_adjusted_ksi.csv", index=False)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    collisions = pd.read_parquet(POWERBI / "fact_collision.parquet")
    lsoas = pd.read_parquet(POWERBI / "dim_lsoa.parquet")
    risk = pd.read_parquet(POWERBI / "fact_local_authority_year_risk.parquet")

    build_deprivation_outputs(collisions, lsoas)
    build_severity_outputs(collisions)
    build_exposure_output(risk)
    print("Wrote public analytical extracts")


if __name__ == "__main__":
    main()
