import psycopg2
from fastapi import FastAPI
import uvicorn
from psycopg2.extras import RealDictCursor

app = FastAPI()

# Postgres connection settings
DB_HOST = "localhost"
DB_PORT = "5431"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "mysecretkey"

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

@app.get("/tables")
def list_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return {"tables": tables}

@app.get("/table/{table_name}")
def get_table_rows(table_name: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)  # returns dicts
    cur.execute(f"SELECT * FROM {table_name} LIMIT 5;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {table_name: rows}

if __name__ == "__main__":
    uvicorn.run("conn_test:app", host="0.0.0.0", port=8000, reload=True)
