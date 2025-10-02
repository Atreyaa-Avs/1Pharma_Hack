# File that imports all the data from the "Data file" having JSON files, and load it into Docker PostgresDB

import json
import csv
import io
from pathlib import Path
import psycopg2

# --- CONFIG ---
DB_DSN = "postgresql://postgres:mysecretkey@localhost:5431/postgres"  # Update if needed
DATA_FOLDER = Path("data")  # Folder containing your JSON files
# ----------------

if not DATA_FOLDER.exists() or not DATA_FOLDER.is_dir():
    raise FileNotFoundError(f"Folder not found: {DATA_FOLDER}")

json_files = list(DATA_FOLDER.glob("*.json"))
if not json_files:
    raise FileNotFoundError(f"No JSON files found in {DATA_FOLDER}")

print(f"Found {len(json_files)} JSON files to import.")

# Connect to Postgres
conn = psycopg2.connect(DB_DSN)
cur = conn.cursor()

total_records = 0
seen_ids = set()  # Global set to track duplicates across all files

for file_path in json_files:
    print(f"Importing {file_path.name} ...")
    records = json.loads(file_path.read_text())

    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)

    for r in records:
        rec_id = r.get("id")
        if rec_id in seen_ids:
            continue  # Skip duplicate
        seen_ids.add(rec_id)

        writer.writerow([
            rec_id,
            r.get('sku_id'),
            r.get('name'),
            r.get('manufacturer_name'),
            r.get('marketer_name'),
            r.get('type'),
            r.get('price'),
            r.get('pack_size_label'),
            r.get('short_composition'),
            r.get('is_discontinued'),
            r.get('available'),
            r.get('slug'),
            r.get('image_url')
        ])
        total_records += 1

    buffer.seek(0)
    cur.copy_expert("""
        COPY medicines(
            id, sku_id, name, manufacturer_name, marketer_name, type,
            price, pack_size_label, short_composition, is_discontinued,
            available, slug, image_url
        ) FROM STDIN WITH CSV
    """, buffer)

conn.commit()
cur.close()
conn.close()

print(f"Import finished. Total records imported: {total_records}")
