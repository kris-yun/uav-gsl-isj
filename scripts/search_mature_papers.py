"""Search for 20 mature papers for method idea scouting."""
import json, time, urllib.request, urllib.parse, os

QUERIES = [
    # Core GSL methods (2024-2026)
    ("gas source localization UAV 2024 2025", 15),
    ("mobile robot olfaction source localization 2024 2025", 15),
    ("gas distribution mapping sparse sampling 2024", 10),
    # Specific method families
    ("GMRF Markov random field gas distribution", 10),
    ("sparse Gaussian process gas mapping", 10),
    ("Kriging gas concentration mapping", 10),
    ("hit-map binary occupancy gas source", 10),
    ("probabilistic gas hit map source localization", 10),
    # Sensor robustness
    ("low-cost gas sensor robustness source localization", 10),
    ("MOX sensor drift gas localization", 10),
    ("multi-sensor gas source localization fusion", 10),
    ("electronic nose gas source localization", 10),
    # Plume dynamics
    ("plume intermittency mobile robot olfaction", 10),
    ("plume loss reacquisition gas source", 10),
    ("gas plume intermittency detection", 10),
    # Datasets
    ("Red:Vapor gas dataset wind tunnel UAV", 10),
    ("GADEN gas simulation source localization", 10),
    ("VGR gas dispersion dataset", 10),
    # Source declaration
    ("source declaration gas map peak", 10),
    ("gas source localization uncertainty calibration", 10),
]

def search(query, per_page):
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
            "User-Agent": "GSL-Mature-Search/1.0 (mailto:research@example.com)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "results": []}

def main():
    out = "papers/mature_search.json"
    os.makedirs("papers", exist_ok=True)
    all_papers = {}
    for i, (q, n) in enumerate(QUERIES):
        print(f"[{i+1}/{len(QUERIES)}] {q}")
        r = search(q, n)
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            time.sleep(3)
            continue
        for w in r.get("results", []):
            wid = w.get("id", "")
            if not wid: continue
            title = w.get("title", "")
            year = w.get("publication_year")
            cited = w.get("cited_by_count", 0)
            authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:5]]
            abstract_inv = w.get("abstract_inverted_index", {})
            if abstract_inv:
                words = {}
                for word, positions in abstract_inv.items():
                    for pos in positions: words[pos] = word
                abstract = " ".join(words[k] for k in sorted(words.keys()))[:600]
            else:
                abstract = ""
            if wid not in all_papers:
                all_papers[wid] = {
                    "id": wid, "title": title, "year": year,
                    "cited_by_count": cited, "authors": authors,
                    "abstract": abstract, "doi": w.get("doi", ""),
                    "queries": [q],
                }
            else:
                all_papers[wid]["queries"].append(q)
        print(f"  {r.get('meta',{}).get('count',0)} total, {len(r.get('results',[]))} fetched, total unique: {len(all_papers)}")
        time.sleep(2)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"total": len(all_papers), "papers": list(all_papers.values())}, f, ensure_ascii=False, indent=2)
    print(f"\nDONE: {len(all_papers)} unique papers saved to {out}")

if __name__ == "__main__":
    main()
