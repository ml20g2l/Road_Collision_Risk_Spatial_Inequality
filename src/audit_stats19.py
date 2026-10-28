"""Profile the pinned STATS19 snapshot and save inspectable audit outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
META_DIR = ROOT / "data" / "metadata"
OUT_DIR = ROOT / "data" / "processed"

FILES = {
    "collision": RAW_DIR / "dft-road-casualty-statistics-collision-2025.csv",
    "vehicle": RAW_DIR / "dft-road-casualty-statistics-vehicle-2025.csv",
    "casualty": RAW_DIR / "dft-road-casualty-statistics-casualty-2025.csv",
}

MULTIYEAR_FILES = {
    "collision": RAW_DIR / "dft-road-casualty-statistics-collision-last-5-years.csv",
    "vehicle": RAW_DIR / "dft-road-casualty-statistics-vehicle-last-5-years.csv",
    "casualty": RAW_DIR / "dft-road-casualty-statistics-casualty-last-5-years.csv",
}

KEYS = {
    "collision": ["collision_index"],
    "vehicle": ["collision_index", "vehicle_reference"],
    "casualty": ["collision_index", "casualty_reference"],
}


def pct(value: int, denominator: int) -> float:
    return round(100 * value / denominator, 4) if denominator else 0.0


def normalize_code(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return re.sub(r"\.0$", "", text)


def profile_table(name: str, df: pd.DataFrame) -> dict:
    key = KEYS[name]
    duplicate_key_rows = int(df.duplicated(key, keep=False).sum())
    null_key_rows = int(df[key].isna().any(axis=1).sum())
    nulls = (
        pd.DataFrame(
            {
                "table": name,
                "column": df.columns,
                "dtype": [str(x) for x in df.dtypes],
                "null_count": [int(df[c].isna().sum()) for c in df.columns],
                "null_pct": [pct(int(df[c].isna().sum()), len(df)) for c in df.columns],
                "distinct_count": [int(df[c].nunique(dropna=True)) for c in df.columns],
            }
        )
        .sort_values(["null_pct", "column"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return {
        "summary": {
            "table": name,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "candidate_key": key,
            "duplicate_full_rows": int(df.duplicated().sum()),
            "duplicate_key_rows": duplicate_key_rows,
            "null_key_rows": null_key_rows,
        },
        "columns": nulls,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = {name: pd.read_csv(path, low_memory=False) for name, path in FILES.items()}
    multiyear = {name: pd.read_csv(path, low_memory=False) for name, path in MULTIYEAR_FILES.items()}
    profiles = {name: profile_table(name, df) for name, df in frames.items()}

    collisions = frames["collision"]
    vehicles = frames["vehicle"]
    casualties = frames["casualty"]
    collision_ids = set(collisions["collision_index"])

    vehicle_orphans = ~vehicles["collision_index"].isin(collision_ids)
    casualty_orphans = ~casualties["collision_index"].isin(collision_ids)

    vehicle_counts = vehicles.groupby("collision_index").size()
    casualty_counts = casualties.groupby("collision_index").size()
    stated_vehicle_counts = collisions.set_index("collision_index")["number_of_vehicles"]
    stated_casualty_counts = collisions.set_index("collision_index")["number_of_casualties"]

    date_parsed = pd.to_datetime(collisions["date"], format="%d/%m/%Y", errors="coerce")
    time_parsed = pd.to_datetime(collisions["time"], format="%H:%M", errors="coerce")
    valid_coords = collisions["longitude"].between(-9, 3) & collisions["latitude"].between(49, 61)

    casualty_vehicle_keys = vehicles[["collision_index", "vehicle_reference"]].drop_duplicates()
    casualty_vehicle_check = casualties.merge(
        casualty_vehicle_keys.assign(_vehicle_match=True),
        on=["collision_index", "vehicle_reference"],
        how="left",
    )

    collision_quality = {
        "invalid_date_rows": int(date_parsed.isna().sum()),
        "invalid_time_rows": int(time_parsed.isna().sum()),
        "missing_coordinate_rows": int(collisions[["longitude", "latitude"]].isna().any(axis=1).sum()),
        "out_of_gb_coordinate_rows": int(
            (~valid_coords & collisions[["longitude", "latitude"]].notna().all(axis=1)).sum()
        ),
        "unexpected_collision_severity_rows": int((~collisions["collision_severity"].isin([1, 2, 3])).sum()),
        "vehicle_count_mismatch_collisions": int(
            stated_vehicle_counts.ne(vehicle_counts.reindex(stated_vehicle_counts.index, fill_value=0)).sum()
        ),
        "casualty_count_mismatch_collisions": int(
            stated_casualty_counts.ne(casualty_counts.reindex(stated_casualty_counts.index, fill_value=0)).sum()
        ),
    }

    multiyear_profiles = {name: profile_table(name, df) for name, df in multiyear.items()}
    multiyear_collision_ids = set(multiyear["collision"]["collision_index"])
    multiyear_integrity = {
        "vehicle_rows_without_collision": int(
            (~multiyear["vehicle"]["collision_index"].isin(multiyear_collision_ids)).sum()
        ),
        "casualty_rows_without_collision": int(
            (~multiyear["casualty"]["collision_index"].isin(multiyear_collision_ids)).sum()
        ),
    }
    multiyear_counts = pd.concat(
        [
            df.groupby("collision_year").size().rename("rows").reset_index().assign(table=name)
            for name, df in multiyear.items()
        ],
        ignore_index=True,
    )[["table", "collision_year", "rows"]]

    annual_collision_quality = (
        multiyear["collision"]
        .assign(
            serious_or_fatal=lambda x: x["collision_severity"].isin([1, 2]),
            missing_coordinates=lambda x: x[["longitude", "latitude"]].isna().any(axis=1),
        )
        .groupby("collision_year")
        .agg(
            collisions=("collision_index", "size"),
            serious_or_fatal=("serious_or_fatal", "sum"),
            missing_coordinates=("missing_coordinates", "sum"),
        )
        .assign(serious_or_fatal_share=lambda x: x["serious_or_fatal"] / x["collisions"])
        .reset_index()
    )

    snapshot_reconciliation = {}
    for name in frames:
        subset = multiyear[name].loc[multiyear[name]["collision_year"].eq(2025)].copy()
        standalone = frames[name].copy()
        same_columns = list(subset.columns) == list(standalone.columns)
        if same_columns:
            key = KEYS[name]
            subset = subset.sort_values(key).reset_index(drop=True)
            standalone = standalone.sort_values(key).reset_index(drop=True)
            exact_match = subset.equals(standalone)
        else:
            exact_match = False
        snapshot_reconciliation[name] = {
            "same_columns": same_columns,
            "standalone_2025_rows": int(len(standalone)),
            "multiyear_2025_rows": int(len(subset)),
            "exact_row_and_value_match": exact_match,
        }

    integrity = {
        "vehicle_rows_without_collision": int(vehicle_orphans.sum()),
        "casualty_rows_without_collision": int(casualty_orphans.sum()),
        "casualty_rows_without_matching_vehicle_reference": int(casualty_vehicle_check["_vehicle_match"].isna().sum()),
    }

    severity_counts = collisions.groupby("collision_severity", dropna=False).size().rename("collisions").reset_index()
    local_authority_summary = (
        collisions.assign(serious_or_fatal=collisions["collision_severity"].isin([1, 2]))
        .groupby("local_authority_highway_current", dropna=False)
        .agg(collisions=("collision_index", "size"), serious_or_fatal=("serious_or_fatal", "sum"))
        .assign(serious_or_fatal_share=lambda x: x["serious_or_fatal"] / x["collisions"])
        .sort_values("collisions", ascending=False)
        .reset_index()
    )

    column_profile = pd.concat([profiles[n]["columns"] for n in profiles], ignore_index=True)
    table_summary = pd.DataFrame([profiles[n]["summary"] for n in profiles])
    table_summary["candidate_key"] = table_summary["candidate_key"].apply(lambda x: "+".join(x))
    table_summary.to_csv(OUT_DIR / "table_profile.csv", index=False)
    column_profile.to_csv(OUT_DIR / "column_profile.csv", index=False)
    severity_counts.to_csv(OUT_DIR / "collision_severity_counts.csv", index=False)
    local_authority_summary.to_csv(OUT_DIR / "local_authority_summary_2025.csv", index=False)
    multiyear_counts.to_csv(OUT_DIR / "multiyear_row_counts.csv", index=False)
    annual_collision_quality.to_csv(OUT_DIR / "annual_collision_quality.csv", index=False)

    guide_path = META_DIR / "dft-road-safety-open-dataset-data-guide-2025.xlsx"
    guide = pd.read_excel(guide_path, sheet_name="2024_code_list")
    guide.columns = [str(c).strip().lower().replace(" ", "_").replace("/", "_") for c in guide.columns]
    guide.to_csv(META_DIR / "stats19_2025_code_list.csv", index=False)

    unknown_codes = guide.loc[
        guide["label"]
        .astype(str)
        .str.contains(r"unknown|no data|not known|data missing", case=False, regex=True, na=False),
        ["table", "field_name", "code_format", "label"],
    ].copy()
    coded_missingness_rows = []
    for (table, field), rows in unknown_codes.groupby(["table", "field_name"]):
        if table not in multiyear or field not in multiyear[table].columns:
            continue
        codes = {normalize_code(x) for x in rows["code_format"] if normalize_code(x)}
        values = multiyear[table][field].map(normalize_code)
        missing_count = int(values.isin(codes).sum())
        coded_missingness_rows.append(
            {
                "table": table,
                "column": field,
                "unknown_codes": "|".join(sorted(codes)),
                "unknown_labels": "|".join(sorted(set(rows["label"].astype(str)))),
                "coded_missing_count": missing_count,
                "coded_missing_pct": pct(missing_count, len(values)),
            }
        )
    coded_missingness = pd.DataFrame(coded_missingness_rows).sort_values(
        ["coded_missing_pct", "table", "column"], ascending=[False, True, True]
    )
    coded_missingness.to_csv(OUT_DIR / "coded_missingness.csv", index=False)

    report = {
        "snapshot": "DfT STATS19 2025 final",
        "tables": {name: profiles[name]["summary"] for name in profiles},
        "integrity": integrity,
        "collision_quality": collision_quality,
        "date_min": str(date_parsed.min().date()),
        "date_max": str(date_parsed.max().date()),
        "severity_counts": severity_counts.to_dict(orient="records"),
        "multiyear": {
            "tables": {name: multiyear_profiles[name]["summary"] for name in multiyear_profiles},
            "integrity": multiyear_integrity,
            "years": sorted(int(x) for x in multiyear["collision"]["collision_year"].unique()),
            "snapshot_reconciliation": snapshot_reconciliation,
            "annual_collision_quality": annual_collision_quality.to_dict(orient="records"),
            "highest_coded_missingness": coded_missingness.head(12).to_dict(orient="records"),
        },
    }
    (OUT_DIR / "audit_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
