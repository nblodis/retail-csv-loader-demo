import csv
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path
FILE = Path(__file__).resolve().parents[1] / "src" / "loader.py"
spec = importlib.util.spec_from_file_location("loader", FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class LoaderTests(unittest.TestCase):
    def test_replay_and_update(self):
        with tempfile.TemporaryDirectory() as temp:
            source, db = Path(temp) / "data.csv", Path(temp) / "data.db"
            def write(qty):
                with source.open("w", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["sku", "location", "quantity", "as_of_date"])
                    w.writerow(["SYN-1", "STORE-A", qty, "2026-01-01"])
            write(2)
            self.assertEqual(module.ingest(source, db)["inserted"], 1)
            self.assertEqual(module.ingest(source, db)["inserted"], 0)
            write(3)
            self.assertEqual(module.ingest(source, db)["updated"], 1)
            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0], 1)

    def test_rejects_invalid_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            source, db = Path(temp) / "data.csv", Path(temp) / "data.db"
            source.write_text("sku,location,quantity,as_of_date\nSYN-1,A,-3,2026-01-01\n")
            self.assertEqual(module.ingest(source, db)["rejected"], 1)
