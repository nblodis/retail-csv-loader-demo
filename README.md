# Retail CSV Loader

An independently written Python/SQLite demonstration of CSV validation and idempotent inventory snapshot loading. All sample inputs are fictional.

## Run

```bash
python src/loader.py data/sample_inventory.csv demo.sqlite
python -m unittest discover -s tests -v
```

The importer validates dates, fields, and nonnegative quantities, processes rows in batches, and uses `(sku, location, as_of_date)` as its unique business key. Retries do not insert duplicate records; corrected quantities update existing rows. Output includes inserted, updated, read, and rejected counts.

## Engineering tradeoffs

SQLite and the Python standard library keep this demonstration reproducible without dependencies. Production use would warrant stronger monitoring, bulk upserts, checkpointing, schema migrations and concurrency validation.

**Provenance:** Original educational implementation using synthetic data; not workplace source code or an employer production system.
