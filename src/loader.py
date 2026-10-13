"""Synthetic inventory CSV ingestion demo."""
import argparse
import csv
import datetime as dt
import json
import sqlite3
from pathlib import Path

FIELDS = ("sku", "location", "quantity", "as_of_date")

def validate(row):
    sku = (row.get("sku") or "").strip()
    location = (row.get("location") or "").strip()
    if not sku or not location:
        raise ValueError("sku and location are required")
    try:
        quantity = int(row.get("quantity", ""))
    except (ValueError, TypeError) as exc:
        raise ValueError("quantity must be an integer") from exc
    if quantity < 0:
        raise ValueError("quantity must be nonnegative")
    try:
        day = dt.date.fromisoformat((row.get("as_of_date") or "").strip())
    except ValueError as exc:
        raise ValueError("as_of_date must be YYYY-MM-DD") from exc
    return (sku, location, str(day), quantity)

def ingest(csv_path, db_path, batch_size=500):
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    counts = {"read": 0, "inserted": 0, "updated": 0, "rejected": 0}
    with sqlite3.connect(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT NOT NULL,
            location TEXT NOT NULL,
            as_of_date TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            PRIMARY KEY(sku, location, as_of_date)
        )""")
        with Path(csv_path).open(newline="", encoding="utf-8-sig") as source:
            reader = csv.DictReader(source)
            if not reader.fieldnames or set(reader.fieldnames) != set(FIELDS):
                raise ValueError("CSV must contain exactly: " + ", ".join(FIELDS))
            batch = []
            def flush():
                for sku, loc, day, qty in batch:
                    prior = conn.execute(
                        "SELECT quantity FROM inventory WHERE sku=? AND location=? AND as_of_date=?",
                        (sku, loc, day),
                    ).fetchone()
                    if prior is None:
                        conn.execute("INSERT INTO inventory VALUES(?,?,?,?)", (sku, loc, day, qty))
                        counts["inserted"] += 1
                    elif prior[0] != qty:
                        conn.execute(
                            "UPDATE inventory SET quantity=? WHERE sku=? AND location=? AND as_of_date=?",
                            (qty, sku, loc, day),
                        )
                        counts["updated"] += 1
                batch.clear()
            for row in reader:
                counts["read"] += 1
                try:
                    batch.append(validate(row))
                except ValueError:
                    counts["rejected"] += 1
                    continue
                if len(batch) >= batch_size:
                    flush()
            flush()
    return counts

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("sqlite_db")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    print(json.dumps(ingest(args.input_csv, args.sqlite_db, args.batch_size), indent=2))
