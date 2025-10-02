import asyncio
import time
import httpx
import json

API = "http://localhost:8000"

# Mapping queries to specific endpoints
query_endpoints = {
    "Ava": ["/search/prefix"],
    "Injection": ["/search/substring"],
    "antibiotic": ["/search/fulltext"],
    "Avastn": ["/search/fuzzy"],
}

results = {}

TOTAL_REQUESTS = 50   # number of requests per query + endpoint for throughput


async def run_one(client, endpoint, q):
    start = time.perf_counter()
    r = await client.get(API + endpoint, params={"q": q, "limit": 50}, timeout=30.0)
    elapsed = time.perf_counter() - start
    try:
        data = r.json()
    except Exception:
        data = []
    return elapsed, data


def filter_preview(data):
    """Extract only the required fields from response items"""
    fields = ["name", "manufacturer_name", "marketer_name", "type", "price"]
    return [
        {k: item.get(k) for k in fields if k in item}
        for item in data[:5]
    ]


async def benchmark_query(client, q, ep):
    latencies = []
    responses = []

    # launch 50 concurrent requests
    tasks = [run_one(client, ep, q) for _ in range(TOTAL_REQUESTS)]

    start_all = time.perf_counter()
    results_all = await asyncio.gather(*tasks)
    total_time = time.perf_counter() - start_all

    for elapsed, data in results_all:
        latencies.append(elapsed)
        responses.append(data)

    throughput = TOTAL_REQUESTS / total_time  # requests per second

    return {
        "avg_latency_ms": sum(latencies) / len(latencies) * 1000,
        "throughput_rps": throughput,
        "sample_response_count": len(responses[0]) if responses else 0,
        "sample_response_preview": filter_preview(responses[0]) if responses else [],
    }


async def main():
    async with httpx.AsyncClient() as client:
        for q, eps in query_endpoints.items():
            results[q] = {}
            for ep in eps:
                results[q][ep] = await benchmark_query(client, q, ep)

    # Print results to console
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
