"""Comprehensive 3-hour literature search for GSL gaps."""
import json
import time
import urllib.request
import urllib.parse
import os

# Search queries organized by gap-finding strategy
QUERIES = [
    # GSL evaluation and metrics
    "gas source localization evaluation metric",
    "gas source localization comparison protocol",
    "gas source localization sparse sampling",
    "odor source localization metric",
    "source localization accuracy metric evaluation",
    # GSL on specific datasets
    "GADEN gas simulation source localization",
    "Red:Vapor gas plume dataset",
    "Orebro gas dataset localization",
    "wind tunnel gas source localization",
    "indoor gas source localization benchmark",
    # GSL baselines
    "KernelDM gas distribution mapping",
    "kernel density gas source localization",
    "infotaxis gas source localization comparison",
    "entrotaxis gas source",
    "surge-cast gas source localization",
    "E. coli algorithm gas source",
    # Concentration metric / preprocessing
    "concentration metric gas sensor localization",
    "sensor preprocessing gas source localization",
    "gas sensor normalization source localization",
    "concentration threshold gas detection",
    "binary threshold gas source localization",
    # Source declaration
    "source declaration gas localization",
    "source estimation from concentration map",
    "peak detection gas source localization",
    "source position estimation gas",
    # Multi-sensor
    "multi-sensor gas source localization",
    "sensor fusion gas localization",
    "electronic nose gas source localization",
    "MOX sensor gas source localization",
    "PID sensor gas localization",
    # Calibration-free
    "calibration-free gas source localization",
    "uncalibrated gas sensor localization",
    "sensor drift gas localization",
    "gas sensor robustness localization",
    # Sparse / UAV
    "sparse trajectory gas source localization",
    "UAV gas source localization field",
    "drone gas source localization experiment",
    "aerial gas source localization",
    "UAV chemical plume tracking",
    # Specific methods
    "Gaussian process gas distribution mapping",
    "Bayesian gas source localization comparison",
    "particle filter gas source localization",
    "maximum likelihood gas source",
    "MLE gas source localization",
    # Scenario-specific
    "indoor gas leak localization",
    "outdoor gas source localization",
    "confined space gas localization",
    "pipeline leak gas localization",
    "environmental gas source localization",
    # Negative / failure analysis
    "gas localization failure analysis",
    "source localization limitations",
    "gas mapping limitations",
    "GSL method comparison failure",
]

FIELDS = "title,authors,year,abstract,citationCount,externalIds"
LIMIT = 15
DELAY = 3  # OpenAlex is generous

def search_openalex(query, per_page=LIMIT):
    base = "https://api.openalex.org/works"
    params = urllib.parse.urlencode({
        "search": query,
        "filter": "from_publication_date:2021-01-01",
        "per_page": per_page,
        "sort": "cited_by_count:desc",
    })
    url = f"{base}?{params}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "GSL-Literature-Search/2.0 (mailto:research@example.com)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "results": []}

def main():
    output_file = "papers/comprehensive_search.json"
    os.makedirs("papers", exist_ok=True)

    all_papers = {}
    results_by_query = {}

    for i, query in enumerate(QUERIES):
        print(f"[{i+1}/{len(QUERIES)}] {query}")
        result = search_openalex(query)

        if "error" in result:
            print(f"  ERROR: {result['error']}")
            time.sleep(DELAY)
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
        print(f"  {result.get('meta', {}).get('count', 0)} total, {len(works)} fetched, {count} new")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "total_unique_papers": len(all_papers),
                "queries": results_by_query,
                "papers": list(all_papers.values()),
            }, f, ensure_ascii=False, indent=2)

        time.sleep(DELAY)

    print(f"\n=== DONE ===")
    print(f"Total unique papers: {len(all_papers)}")

if __name__ == "__main__":
    main()
