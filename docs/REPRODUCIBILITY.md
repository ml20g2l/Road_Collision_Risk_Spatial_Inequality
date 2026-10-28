# Reproducibility Guide

## Reproducibility target

The project rebuilds the analytical data products from pinned official releases. A successful clean-room run must:

1. download and checksum every required source;
2. preserve the one-row-per-collision grain;
3. conform 2011 and 2021 LSOA geography without unmatched English collisions;
4. retain at least 99.9% collision-to-authority traffic coverage;
5. produce the Power BI star-schema Parquet files and public analytical extracts;
6. pass Python unit and contract tests; and
7. pass all dbt schema and singular tests.

The `.pbix` report is a versioned presentation artifact. Power BI Desktop does not provide a supported headless Linux build interface, so the automated boundary ends at the validated Parquet semantic-model inputs, DAX source, theme, and model contract. The committed PBIX and PDF exports are not regenerated in CI.

## Local clean-room run

Python 3.11 or 3.12 is recommended.

```powershell
git clone https://github.com/ml20g2l/Road_Collision_Risk_Spatial_Inequality.git
cd Road_Collision_Risk_Spatial_Inequality
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
python -m src.pipeline
dbt build --profiles-dir .
```

Run the same pipeline without network access after a verified first download:

```powershell
python -m src.pipeline --skip-download
dbt build --profiles-dir .
```

Run fast checks only:

```powershell
ruff check src tests_py tests/create_dbt_fixtures.py
pytest --cov=src.download_sources --cov=src.pipeline --cov-report=term-missing
python tests/create_dbt_fixtures.py
dbt build --profiles-dir . --target ci --vars '{powerbi_dir: tests/fixtures/powerbi}'
```

## GitHub Actions

`CI` runs on every pull request and push to `main`. It uses deterministic synthetic Parquet fixtures, so it tests code and contracts without downloading hundreds of megabytes.

`Full official-source rebuild` is a manual workflow. It downloads the pinned public sources, executes the complete transformation pipeline, runs dbt, generates lineage documentation, and uploads manifests, QA results, public extracts, and dbt run evidence as a workflow artifact.

## Source pinning and drift

The download registry records the official URL, publisher, local path, byte size, and SHA-256 checksum. A checksum difference stops the build. This is intentional: an upstream revision requires a reviewed snapshot update and analytical comparison, not an unrecorded refresh.

The ONS best-fit lookup is obtained from the official ArcGIS service and checked for row-count and key uniqueness. Its retrieved checksum is written to the source manifest.

## Expected outputs

| Layer | Main outputs | Grain |
|---|---|---|
| Staging | `data/staging/*.parquet` | Source-specific |
| Intermediate | `int_collision_context`, `int_collision_aadf_match` | Collision |
| Analytical marts | inequality and authority-risk marts | LSOA-year or authority-year |
| Power BI | dimensions, facts, model contract | Declared in `model_contract.json` |
| Public evidence | five small CSV extracts | Chart-specific |
| dbt | DuckDB database and `target/run_results.json` | Model-specific |

Generated raw, intermediate, warehouse, and large Parquet files are intentionally excluded from Git. They can be recreated from the pinned inputs.

## Failure interpretation

- A checksum failure means the publisher changed a pinned source or the download is incomplete.
- A Python contract failure means a grain, join, metric, or output invariant changed.
- A dbt relationship failure means a fact key no longer resolves to its conformed dimension.
- An exposure test failure prevents an AADF sensitivity measure from being presented as an absolute risk rate.
- A reconciliation failure means the authority-year fact no longer sums to the collision fact.
