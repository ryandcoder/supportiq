"""Container start-up decisions (no database or Docker needed: the database is replaced by simple fakes)."""
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data_pipeline.bootstrap import run  # noqa: E402

RAW = Path(__file__).resolve().parents[2] / "data"
pytestmark = pytest.mark.skipif(not (RAW / "tickets.csv").exists(), reason="CSV files not in data/")


class Fake:
    def __init__(self, has_data):
        self.has_data, self.loaded = has_data, []

    def db_has_data(self):
        return self.has_data

    def replace(self, a, m, t):
        self.loaded.append((len(a), len(m), len(t)))


def go(db, report, force=False, data_dir=RAW):
    return run(data_dir=data_dir, report_path=report, force=force, db_has_data=db.db_has_data, replace=db.replace)


def test_empty_database_is_loaded_and_report_written():
    with tempfile.TemporaryDirectory() as d:
        report, db = Path(d) / "sub" / "report.json", Fake(False)
        assert go(db, report) == "loaded"
        assert db.loaded == [(20, 112, 2057)]
        assert report.exists() and '"tickets": 2057' in report.read_text()


def test_existing_data_is_not_overwritten():
    with tempfile.TemporaryDirectory() as d:
        report = Path(d) / "report.json"
        report.write_text("{}")
        db = Fake(True)
        assert go(db, report) == "skipped"
        assert db.loaded == [] and report.read_text() == "{}"


def test_missing_report_is_rebuilt_without_touching_the_data():
    with tempfile.TemporaryDirectory() as d:
        report, db = Path(d) / "report.json", Fake(True)
        assert go(db, report) == "report-only"
        assert db.loaded == [] and report.exists()


def test_reload_data_forces_a_reload():
    with tempfile.TemporaryDirectory() as d:
        report = Path(d) / "report.json"
        report.write_text("{}")
        db = Fake(True)
        assert go(db, report, force=True) == "loaded" and len(db.loaded) == 1


def test_missing_csv_on_first_start_gives_a_clear_error():
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(FileNotFoundError) as e:
            go(Fake(False), Path(d) / "report.json", data_dir=Path(d))
        assert "tickets.csv" in str(e.value) and "./data" in str(e.value)


def test_missing_csv_is_tolerated_when_data_is_already_loaded():
    with tempfile.TemporaryDirectory() as d:
        assert go(Fake(True), Path(d) / "report.json", data_dir=Path(d)) == "skipped"
