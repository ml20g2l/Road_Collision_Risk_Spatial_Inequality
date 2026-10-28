"""Download the authoritative ONS 2011-to-2021 LSOA best-fit lookup."""

from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/auxiliary/ons_lsoa11_lsoa21_lad22_best_fit_v2.csv"
EXPECTED_SHA256 = "2fb490d5193a30be0bbcd2c1963c5e131584b14145e3a78eafc33129adcc5f72"
SERVICE = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA11_LSOA21_LAD22_EW_LU_v2/FeatureServer/0/query"


def request(params):
    url = SERVICE + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    if OUT.exists() and sha256(OUT) == EXPECTED_SHA256:
        print(f"Reused verified ONS lookup at {OUT}")
        return
    count = request({"where": "1=1", "returnCountOnly": "true", "f": "json"})["count"]
    rows = []
    page_size = 1000
    for offset in range(0, count, page_size):
        payload = request(
            {
                "where": "1=1",
                "outFields": "LSOA11CD,LSOA11NM,LSOA21CD,LSOA21NM,LAD22CD,LAD22NM",
                "returnGeometry": "false",
                "resultOffset": offset,
                "resultRecordCount": page_size,
                "orderByFields": "ObjectId",
                "f": "json",
            }
        )
        rows.extend(feature["attributes"] for feature in payload["features"])
    frame = pd.DataFrame(rows).drop_duplicates()
    if len(frame) != count or frame["LSOA11CD"].duplicated().any():
        raise RuntimeError(f"Unexpected lookup grain: service={count}, downloaded={len(frame)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUT.with_suffix(".csv.part")
    # Fix the line terminator so the generated snapshot has the same checksum
    # on Windows and Linux runners.
    frame.to_csv(temporary, index=False, lineterminator="\n")
    actual = sha256(temporary)
    if actual != EXPECTED_SHA256:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"ONS lookup checksum changed: expected {EXPECTED_SHA256}, got {actual}")
    temporary.replace(OUT)
    print(f"Downloaded {len(frame):,} rows to {OUT}")


if __name__ == "__main__":
    main()
