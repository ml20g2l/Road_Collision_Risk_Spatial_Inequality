"""Download the pinned 2025 DfT STATS19 open-data snapshot."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
META_DIR = ROOT / "data" / "metadata"

SOURCES = {
    "dft-road-casualty-statistics-collision-2025.csv": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-2025.csv",
    "dft-road-casualty-statistics-vehicle-2025.csv": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-2025.csv",
    "dft-road-casualty-statistics-casualty-2025.csv": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-2025.csv",
    "dft-road-safety-open-dataset-data-guide-2025.xlsx": "https://assets.publishing.service.gov.uk/media/6ab2a71d997a4b2950cced58/dft-road-casualty-statistics-road-safety-open-dataset-data-guide-2025.xlsx",
    "dft-road-casualty-statistics-collision-last-5-years.csv": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-last-5-years.csv",
    "dft-road-casualty-statistics-vehicle-last-5-years.csv": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-last-5-years.csv",
    "dft-road-casualty-statistics-casualty-last-5-years.csv": "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-last-5-years.csv",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for filename, url in SOURCES.items():
        target = META_DIR / filename if filename.endswith(".xlsx") else RAW_DIR / filename
        if not target.exists():
            urllib.request.urlretrieve(url, target)
        manifest.append(
            {
                "file": str(target.relative_to(ROOT)),
                "url": url,
                "bytes": target.stat().st_size,
                "sha256": sha256(target),
            }
        )
    payload = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot": "DfT STATS19 2025 final",
        "license": "Open Government Licence v3.0",
        "sources": manifest,
    }
    (META_DIR / "source_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
