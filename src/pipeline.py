"""Single entry point for a clean-room project rebuild."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Stage:
    name: str
    command: tuple[str, ...]
    outputs: tuple[str, ...]


STAGES = (
    Stage("download", ("-m", "src.download_sources"), ("data/metadata/source_manifest.json",)),
    Stage("audit", ("src/audit_stats19.py",), ("data/processed/audit_summary.json",)),
    Stage("transform", ("src/build_week2_pipeline.py",), ("data/intermediate/int_collision_context.parquet",)),
    Stage("match-aadf", ("src/match_collisions_to_aadf.py",), ("data/intermediate/int_collision_aadf_match.parquet",)),
    Stage("powerbi-marts", ("src/build_powerbi_marts.py",), ("data/powerbi/model_contract.json",)),
    Stage("public-insights", ("src/build_public_insights.py",), ("data/public/annual_exposure_adjusted_ksi.csv",)),
    Stage("validate-week2", ("src/validate_week2_models.py",), ("data/processed/week2_qa_summary.json",)),
    Stage("validate-powerbi", ("src/validate_powerbi_marts.py",), ("data/powerbi/fact_collision.parquet",)),
)


def selected_stages(skip_download: bool) -> tuple[Stage, ...]:
    return tuple(stage for stage in STAGES if not (skip_download and stage.name == "download"))


def run_stage(stage: Stage) -> None:
    started = time.monotonic()
    command = (sys.executable, *stage.command)
    print(f"\n[{stage.name}] {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)
    missing = [output for output in stage.outputs if not (ROOT / output).exists()]
    if missing:
        raise RuntimeError(f"Stage {stage.name} did not create: {missing}")
    print(f"[{stage.name}] complete in {time.monotonic() - started:.1f}s", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-download", action="store_true", help="Reuse already verified raw files.")
    parser.add_argument("--list", action="store_true", help="Print the ordered stage plan without executing it.")
    args = parser.parse_args()
    stages = selected_stages(args.skip_download)
    if args.list:
        print("\n".join(stage.name for stage in stages))
        return
    for stage in stages:
        run_stage(stage)
    print("\nFull pipeline completed successfully.")


if __name__ == "__main__":
    main()
