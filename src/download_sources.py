"""Download every official input required by the reproducible pipeline.

Files are downloaded atomically and checked against the pinned 2026-10-26
snapshot. A changed upstream file therefore fails loudly instead of silently
changing the published analysis.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "metadata" / "source_manifest.json"


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    relative_path: str
    sha256: str
    publisher: str
    licence: str = "Open Government Licence v3.0"

    @property
    def path(self) -> Path:
        return ROOT / self.relative_path


SOURCES = (
    Source(
        "stats19_collision_2025",
        "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-2025.csv",
        "data/raw/dft-road-casualty-statistics-collision-2025.csv",
        "e699c19bdb82e47e449b6f3381ac87631865f6a31cef118c9955ba80ca870e2b",
        "Department for Transport",
    ),
    Source(
        "stats19_vehicle_2025",
        "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-2025.csv",
        "data/raw/dft-road-casualty-statistics-vehicle-2025.csv",
        "dbeadb9745a8821ab8132f0dde59c246159e23059ab5db2c9a4381d44141a430",
        "Department for Transport",
    ),
    Source(
        "stats19_casualty_2025",
        "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-2025.csv",
        "data/raw/dft-road-casualty-statistics-casualty-2025.csv",
        "b343039991f63f526bbcac0a5e6102e3a6e4c0b65d077e3ae37dbd53d1a7319a",
        "Department for Transport",
    ),
    Source(
        "stats19_data_guide_2025",
        "https://assets.publishing.service.gov.uk/media/6ab2a71d997a4b2950cced58/dft-road-casualty-statistics-road-safety-open-dataset-data-guide-2025.xlsx",
        "data/metadata/dft-road-safety-open-dataset-data-guide-2025.xlsx",
        "51b08606ef3dad1ae5d4c8726241b022fc8e4bbdc910ef0e5cc2fb92b054fc12",
        "Department for Transport",
    ),
    Source(
        "stats19_collision_2021_2025",
        "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-last-5-years.csv",
        "data/raw/dft-road-casualty-statistics-collision-last-5-years.csv",
        "06a03c0e5504175e23ed98e3e0b4767ac61d396c073405a1bddab9339c18f948",
        "Department for Transport",
    ),
    Source(
        "stats19_vehicle_2021_2025",
        "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-last-5-years.csv",
        "data/raw/dft-road-casualty-statistics-vehicle-last-5-years.csv",
        "05453dca2651ad8a27b4ac0e6a0450a852c506e4d495111ffca398f3d311e26a",
        "Department for Transport",
    ),
    Source(
        "stats19_casualty_2021_2025",
        "https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-last-5-years.csv",
        "data/raw/dft-road-casualty-statistics-casualty-last-5-years.csv",
        "870be5a934ae10baf5c52163d59eccba0ab2f40327ffa6b2bd354d2e7ee6b108",
        "Department for Transport",
    ),
    Source(
        "iod2025_file7_v2",
        "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv",
        "data/raw/auxiliary/iod2025_file7_v2.csv",
        "b1b716aa2e476449f987b9de3e08255b4794eabfd270626de5de18b2f5eff3ef",
        "Ministry of Housing, Communities and Local Government",
    ),
    Source(
        "dft_count_points",
        "https://storage.googleapis.com/dft-statistics/road-traffic/downloads/data-gov-uk/count_points.zip",
        "data/raw/auxiliary/count_points.zip",
        "4772abb13761694f35c7aba6d83915c5c168e94a0d25ae401e4b7e84ef7fcff2",
        "Department for Transport",
    ),
    Source(
        "dft_aadf",
        "https://storage.googleapis.com/dft-statistics/road-traffic/downloads/data-gov-uk/dft_traffic_counts_aadf.zip",
        "data/raw/auxiliary/dft_traffic_counts_aadf.zip",
        "5273cf63da4ca8b317bfe972d8a345e7932db0fff7a7789998a890f0081232b6",
        "Department for Transport",
    ),
    Source(
        "dft_local_authority_traffic",
        "https://storage.googleapis.com/dft-statistics/road-traffic/downloads/data-gov-uk/local_authority_traffic.csv",
        "data/raw/auxiliary/local_authority_traffic.csv",
        "058a61b9f6f7d07a9363c339829c6723fdecc4270f500611d1790eae6da7b9fc",
        "Department for Transport",
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(source: Source, *, retries: int = 3) -> dict[str, object]:
    source.path.parent.mkdir(parents=True, exist_ok=True)
    if source.path.exists() and sha256(source.path) == source.sha256:
        status = "reused"
    else:
        temporary = source.path.with_suffix(source.path.suffix + ".part")
        for attempt in range(1, retries + 1):
            try:
                request = urllib.request.Request(
                    source.url, headers={"User-Agent": "road-risk-reproducible-pipeline/1.0"}
                )
                with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
                    while chunk := response.read(1024 * 1024):
                        output.write(chunk)
                actual = sha256(temporary)
                if actual != source.sha256:
                    raise ValueError(f"Checksum mismatch for {source.name}: expected {source.sha256}, got {actual}")
                temporary.replace(source.path)
                status = "downloaded"
                break
            except Exception:
                temporary.unlink(missing_ok=True)
                if attempt == retries:
                    raise
                time.sleep(2**attempt)
    return {
        "name": source.name,
        "publisher": source.publisher,
        "url": source.url,
        "file": source.relative_path,
        "bytes": source.path.stat().st_size,
        "sha256": sha256(source.path),
        "licence": source.licence,
        "status": status,
    }


def write_manifest(records: list[dict[str, object]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "snapshot": "Pinned 2021-2025 official-source build",
        "snapshot_date": "2026-10-26",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "sources": records,
    }
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    records = [download(source) for source in SOURCES]
    # The ONS lookup is paginated and has its own grain validation.
    from src.download_week2_geography import main as download_geography

    download_geography()
    lookup_path = ROOT / "data/raw/auxiliary/ons_lsoa11_lsoa21_lad22_best_fit_v2.csv"
    records.append(
        {
            "name": "ons_lsoa11_lsoa21_best_fit_v2",
            "publisher": "Office for National Statistics",
            "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA11_LSOA21_LAD22_EW_LU_v2/FeatureServer/0/query",
            "file": str(lookup_path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": lookup_path.stat().st_size,
            "sha256": sha256(lookup_path),
            "licence": "Open Government Licence v3.0",
            "status": "downloaded_or_reused",
        }
    )
    write_manifest(records)
    print(json.dumps({"sources_verified": len(records), "manifest": str(MANIFEST_PATH)}, indent=2))


if __name__ == "__main__":
    main()
