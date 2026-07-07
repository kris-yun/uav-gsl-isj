"""Search OpenAlex API for GSL papers. OpenAlex has generous rate limits."""
import json
import time
import urllib.request
import urllib.parse
import os

QUERIES = [
    "gas source localization UAV",
    "gas source localization mobile robot",
    "odor source localization robot",
    "chemical plume tracking",
    "gas distribution mapping kernel",
    "calibration-free gas sensor",
    "binary sensing gas source",
    "infotaxis gas source",
    "entrotaxis gas source",
    "plume tracing robot",
    "multi-robot gas localization",
    "gas sensor drift localization",
    "sparse sampling gas source",
    "UAV trajectory gas sensing",
    "Red:Vapor gas dataset",
    "GADEN gas simulation",
    "particle filter gas source",
    "Gaussian process gas mapping",
    "source term estimation gas",
    "gas localization benchmark",
]

def search_openalex(query, per_page=25):
    """Search OpenAlex API."""
    base = "https://api.openalex.org/works"
    params = urllib.parse.urlencode({
        "search": query,
        "filter": "from_publication_date:2023-01-01",
        "per_page": per_page,
        "sort": "cited_by_count:desc",
    })
    url = f"{base}?{params}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "GSL-Literature-Search/1.0 (mailto:research@example.com)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "results": []}

def main():
    output_file = "papers/openalex_results.json"
    os.makedirs("papers", exist_ok=True)

    all_papers = {}  # id -> paper info
    results_by_query = {}

    for i, query in enumerate(QUERIES):
        print(f"[{i+1}/{len(QUERIES)}] Searching: {query}")
        result = search_openalex(query)

        if "error" in result:
            print(f"  ERROR: {result['error']}")
            time.sleep(5)
            continue

        works = result.get("results", [])
        count = 0
        for w in works:
            wid = w.get("id", "")
            if not wid:
                continue
            title = w.get("title", "")
            year = w.get("publication_year")
            cited = w.get("cited_by_count", 0)
            authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:5]]
            abstract_inv = w.get("abstract_inverted_index", {})
            # Reconstruct abstract from inverted index
            if abstract_inv:
                words = {}
                for word, positions in abstract_inv.items():
                    for pos in positions:
                        words[pos] = word
                abstract = " ".join(words[k] for k in sorted(words.keys()))[:500]
            else:
                abstract = ""

            if wid not in all_papers:
                all_papers[wid] = {
                    "id": wid,
                    "title": title,
                    "year": year,
                    "cited_by_count": cited,
                    "authors": authors,
                    "abstract": abstract,
                    "doi": w.get("doi", ""),
                    "queries": [query],
                }
                count += 1
            else:
                all_papers[wid]["queries"].append(query)

        results_by_query[query] = {
            "total": result.get("meta", {}).get("count", 0),
            "fetched": len(works),
            "new": count,
        }
        print(f"  Total: {result.get('meta', {}).get('count', 0)}, Fetched: {len(works)}, New: {count}")

        # Save intermediate
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "total_unique_papers": len(all_papers),
                "queries": results_by_query,
                "papers": list(all_papers.values()),
            }, f, ensure_ascii=False, indent=2)

        time.sleep(2)  # OpenAlex is generous, 2s is enough

    print(f"\n=== DONE ===")
    print(f"Total unique papers: {len(all_papers)}")
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
