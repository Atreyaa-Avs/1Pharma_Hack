# 💊 1Pharma_Hack - Medicine Search Database Solution

A **FastAPI-based web service** for PostgreSQL database introspection and medicine search with advanced indexing strategies for optimal performance.

---

## 🚀 Setup Instructions

### Step 1: Start PostgreSQL Docker Container

docker run --name Pharmal_Hack -e POSTGRES_PASSWORD=mysecretkey -p 5431:5432 -d postgres

text

### Step 2: Check Container Status

docker ps -a

text

### Step 3: Copy Schema File to Container

docker cp "E:\1Pharma_Hack\schema.sql" Pharmal_Hack:/schema.sql

text

### Step 4: Access PostgreSQL in the Container

docker exec -it Pharmal_Hack psql -U postgres

text

### Step 5: Execute Schema File in PostgreSQL

\i /schema.sql

text

### Step 6: Verify Table Creation

\dt

text

### Step 7: Run Python Import Script (outside container)

python -u "e:\IPharma_Hack\import_data.py"

text

### Step 8: Start the FastAPI Server

python main.py

text

---

## 🗄️ Schema.sql Detailed Explanation

The database schema is optimized for high-performance medicine search with multiple indexing strategies.

### Table Structure

- **medicines** → Primary table storing medicine information (`id, sku_id, name, manufacturer, pricing, etc.`).
- **search_name** → Normalized column for dosage-independent searches.
- **tsv** → Materialized `tsvector` column for full-text search.

### Performance Indexes

- **Prefix Search Index:** `idx_medicines_lower_name_varchar_pattern` → fast `ILIKE 'prefix%'`.
- **Trigram Indexes:** GIN indexes for fuzzy/substring search on `name`, `manufacturer`, `composition`.
- **Full-text Index:** GIN index on `tsvector` for advanced search.

### Trigger Function

The trigger `medicines_tsv_trigger()` automatically:

- Maintains normalized `search_name`.
- Builds weighted `tsvectors`.

---

## 📂 File Descriptions

### Core Application Files

- **main.py** → FastAPI app with four endpoints (prefix, substring, fulltext, fuzzy). Uses asyncpg pooling.
- **conn_test.py** → FastAPI DB introspection API with `/tables` and `/table/{table_name}`.
- **import_data.py** → Bulk JSON importer using PostgreSQL `COPY`.

### Frontend

- **index.html** → User interface with:
  - 500ms debouncing
  - Pagination (5 results per page)
  - Four search modes

### Database Schema

- **schema.sql** → Optimized PostgreSQL schema for search performance.

---

## 🎨 Frontend UI Features

- **Search Modes:** Prefix, Substring, Full-text, Fuzzy.
- **Debouncing:** 500ms delay before sending requests.
- **Pagination:** Client-side, 5 results per page.

---

## ⚡ Performance Approach

### Indexing Strategy

- **Prefix Search** → `varchar_pattern_ops` index.
- **Substring / Fuzzy Search** → PostgreSQL `pg_trgm` GIN index.
- **Full-text Search** → Weighted `tsvector`:
  - **A →** name
  - **B →** composition
  - **C →** manufacturer

### Connection Management

- **main.py** → asyncpg connection pooling (1–100).
- **import_data.py** → Bulk data load via `COPY`.

### Search Query Optimization

- **Prefix:** `lower(name) LIKE lower($1) || '%'`.
- **Substring:** Trigram similarity scoring.
- **Full-text:** `ts_rank(tsv, query)`.
- **Fuzzy:** Trigram similarity (>0.2) + prefix priority.

---

## 📊 Benchmark Results

Below are the measured average latency and throughput for each search mode, based on 50 concurrent requests per query.

| Query      | Endpoint          | Avg Latency (ms) | Throughput (req/s) |
| ---------- | ----------------- | ---------------- | ------------------ |
| Ava        | /search/prefix    | 587.49           | 73.24              |
| Injection  | /search/substring | 5064.92          | 8.86               |
| antibiotic | /search/fulltext  | 125.60           | 217.78             |
| Avastn     | /search/fuzzy     | 7314.96          | 5.99               |

- **Avg Latency (ms):** Average response time per request.
- **Throughput (req/s):** Number of requests handled per second.

---
