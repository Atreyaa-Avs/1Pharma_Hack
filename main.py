# Main file that creates Search API

import typing
from fastapi import FastAPI, Query
import asyncpg
import uvicorn
from contextlib import asynccontextmanager

# Database URL
DATABASE_URL = "postgresql://postgres:mysecretkey@localhost:5431/postgres"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create the pool
    app.state.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=100)
    yield  # app runs here
    # Shutdown: close the pool
    await app.state.pool.close()

app = FastAPI(title="Medicine Search", lifespan=lifespan)


# CORS setup
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Only for Development purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generic fetch function
async def fetch(query: str, *args):
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
    return [dict(r) for r in rows]

@app.get("/")
async def home():
    return {"message": "FastAPI is running!"}

# Prefix search
@app.get('/search/prefix', response_model=typing.List[typing.Dict])
async def search_prefix(q: str = Query(..., min_length=1), limit: int = 50):
    sql = '''
        SELECT *
        FROM medicines
        WHERE lower(name) LIKE lower($1) || '%'
        ORDER BY lower(name)
        LIMIT $2
    '''
    return await fetch(sql, q, limit)


# Substring search
@app.get('/search/substring', response_model=typing.List[typing.Dict])
async def search_substring(q: str = Query(..., min_length=1), limit: int = 50):
    sql = '''
        SELECT *,
        similarity(name, $1) AS sim
        FROM medicines
        WHERE name ILIKE '%' || $1 || '%'  -- matches substring
        ORDER BY sim DESC
        LIMIT $2;
    '''
    return await fetch(sql, q, limit)


# Full-text search
@app.get('/search/fulltext', response_model=typing.List[typing.Dict])
async def search_fulltext(q: str = Query(..., min_length=1), limit: int = 50):
    sql = '''
        SELECT *
        FROM medicines
        WHERE tsv @@ plainto_tsquery('english', $1)
        ORDER BY ts_rank(tsv, plainto_tsquery('english', $1)) DESC
        LIMIT $2
    '''
    return await fetch(sql, q, limit)

@app.get('/search/fuzzy', response_model=typing.List[typing.Dict])
async def search_fuzzy(q: str = Query(..., min_length=1), limit: int = 50):
    sql = '''
        SELECT *,
               similarity(search_name, $1) AS sim,
               CASE WHEN lower(search_name) LIKE lower($1) || '%' THEN 1 ELSE 0 END AS prefix_match
        FROM medicines
        WHERE search_name % $1
          AND similarity(search_name, $1) > 0.2
        ORDER BY prefix_match DESC, sim DESC
        LIMIT $2
    '''
    return await fetch(sql, q, limit)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
