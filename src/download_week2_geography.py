"""Download the authoritative ONS 2011-to-2021 LSOA best-fit lookup."""
from __future__ import annotations
import json
import urllib.parse
import urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/auxiliary/ons_lsoa11_lsoa21_lad22_best_fit_v2.csv"
SERVICE = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA11_LSOA21_LAD22_EW_LU_v2/FeatureServer/0/query"

def request(params):
    url = SERVICE + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)

def main():
    count = request({"where":"1=1","returnCountOnly":"true","f":"json"})["count"]
    rows = []
    page_size = 1000
    for offset in range(0, count, page_size):
        payload = request({"where":"1=1","outFields":"LSOA11CD,LSOA11NM,LSOA21CD,LSOA21NM,LAD22CD,LAD22NM","returnGeometry":"false","resultOffset":offset,"resultRecordCount":page_size,"orderByFields":"ObjectId","f":"json"})
        rows.extend(feature["attributes"] for feature in payload["features"])
    frame = pd.DataFrame(rows).drop_duplicates()
    if len(frame) != count or frame["LSOA11CD"].duplicated().any():
        raise RuntimeError(f"Unexpected lookup grain: service={count}, downloaded={len(frame)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT, index=False)
    print(f"Downloaded {len(frame):,} rows to {OUT}")

if __name__ == "__main__": main()
