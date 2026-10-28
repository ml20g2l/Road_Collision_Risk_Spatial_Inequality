from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest

from src.build_week2_pipeline import clean_code, read_zip_csv


def test_clean_code_separates_sentinel_reason() -> None:
    frame = pd.DataFrame({"code": [1, -1, -2, -3, None]})
    clean_code(frame, "code")
    assert frame.code.tolist()[:4] == [1, pd.NA, pd.NA, pd.NA]
    assert frame.code_missing_reason.tolist()[:4] == [pd.NA, "unknown", "not_applicable", "self_reported_or_untraced"]


def test_read_zip_csv_reads_single_csv(tmp_path: Path) -> None:
    path = tmp_path / "one.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("data.csv", "id,value\n1,2\n")
    result = read_zip_csv(path)
    assert result.to_dict("records") == [{"id": 1, "value": 2}]


def test_read_zip_csv_rejects_ambiguous_archive(tmp_path: Path) -> None:
    path = tmp_path / "two.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("a.csv", "id\n1\n")
        archive.writestr("b.csv", "id\n2\n")
    with pytest.raises(ValueError, match="Expected one CSV"):
        read_zip_csv(path)
