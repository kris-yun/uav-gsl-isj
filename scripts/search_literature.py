"""Batch search Semantic Scholar for GSL-related papers with rate-limit delays."""
import json
import time
import urllib.request
import urllib.parse
import sys
import os

QUERIES = [
    # Core GSL
    "gas source localization UAV drone",
    "gas source localization mobile robot",
    "odor source localization robot",
    "chemical plume source localization",
    "gas source localization benchmark evaluation",
    "gas source localization baseline comparison",
    # GDM / KernelDM
    "gas distribution mapping kernel density",
    "gas distribution mapping mobile robot",
    "KernelDM gas distribution",
    "gas distribution mapping UAV",
    # Calibration-free / ranking
    "calibration-free gas sensor localization",
    "rank-based gas source localization",
    "percentile gas sensor localization",
    "binary sensing gas source UAV",
    "uncalibrated gas sensor source localization",
    # Trajectory / sampling
    "UAV trajectory gas sampling",
    "sparse trajectory gas source localization",
    "active sensing gas source robot",
    "infotaxis gas source localization",
    "entrotaxis gas source",
    # Plume tracking
    "plume tracking robot UAV",
    "chemical plume tracking algorithm",
    "plume tracing mobile robot",
    # Sensor dynamics
    "gas sensor dynamics compensation UAV",
    "MOX sensor response lag gas",
    "gas sensor drift compensation localization",
    # Multi-robot
    "multi-robot gas source localization",
    "multi-UAV gas source search",
    "cooperative gas source localization",
    # Wind / dispersion
    "wind-aided gas source localization",
    "dispersion model gas source estimation",
    "source term estimation gas",
    # Datasets
    "Red:Vapor gas dataset wind tunnel",
    "GADEN gas simulation dataset",
    "Orebro gas dataset 3D",
    # Negative / benchmark
    "olfaction benchmark negative result",
    "gas localization simple baseline complex method",
    # Field experiments
    "field experiment gas source localization UAV",
    "real-world gas source localization drone",
    # Bayesian / probabilistic
    "Bayesian gas source localization",
    "particle filter gas source localization",
    "Gaussian process gas distribution mapping",
    # Neural / learning
    "neural network gas source localization",
    "reinforcement learning gas source search",
    "graph neural network gas distribution",
    # Metrics / evaluation
    "source localization metric evaluation protocol",
    "gas mapping evaluation metric",
]

FIELDS = "title,authors,year,abstract,citationCount,externalIds"
LIMIT = 10
DELAY = 25  # seconds between requests

def search_semantic_scholar(query, limit=LIMIT):
    """Search Semantic Scholar API."""
    base = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": FIELDS,
        "year": "2023-2026",
    })
    url = f"{base}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GSL-Literature-Search/1.0"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "data": []}

def main():
    output_file = "papers/literature_search_results.json"
    os.makedirs("papers", exist_ok=True)

    all_papers = {}  # paperId -> paper info
    results_by_query = {}

    for i, query in enumerate(QUERIES):
        print(f"[{i+1}/{len(QUERIES)}] Searching: {query}")
        result = search_semantic_scholar(query)

        if "error" in result:
            print(f"  ERROR: {result['error']}")
            if "429" in str(result["error"]) or "Too Many" in str(result["error"]):
                print("  Rate limited. Waiting 60s...")
                time.sleep(60)
                result = search_semantic_scholar(query)
                if "error" in result:
                    print(f"  Still failing: {result['error']}")
                    time.sleep(DELAY)
                    continue
            else:
                time.sleep(DELAY)
                continue

        papers = result.get("data", [])
        count = 0
        for p in papers:
            pid = p.get("paperId", "")
            if pid and pid not in all_papers:
                all_papers[pid] = {
                    "paperId": pid,
                    "title": p.get("title", ""),
                    "year": p.get("year"),
                    "citationCount": p.get("citationCount", 0),
                    "authors": [a.get("name", "") for a in p.get("authors", [])[:5]],
                    "abstract": (p.get("abstract") or "")[:500],
                    "queries": [query],
                }
                count += 1
            elif pid in all_papers:
                all_papers[pid]["queries"].append(query)

        results_by_query[query] = {
            "total": result.get("total", 0),
            "fetched": len(papers),
            "new": count,
        }
        print(f"  Total: {result.get('total', 0)}, Fetched: {len(papers)}, New: {count}")

        # Save intermediate results
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "total_unique_papers": len(all_papers),
                "queries": results_by_query,
                "papers": list(all_papers.values()),
            }, f, ensure_ascii=False, indent=2)

        if i < len(QUERIES) - 1:
            time.sleep(DELAY)

    print(f"\n=== DONE ===")
    print(f"Total unique papers: {len(all_papers)}")
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
