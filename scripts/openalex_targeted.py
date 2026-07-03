import requests
import json
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def search_openalex(query, per_page=20):
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per_page": per_page,
        "sort": "relevance_score:desc",
        "filter": "publication_year:2022-2026"
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def extract(work):
    loc = work.get("primary_location", {}) or {}
    src = loc.get("source", {}) or {}
    oa = work.get("open_access", {}) or {}
    return {
        "title": (work.get("title") or "").encode("ascii", "replace").decode(),
        "year": work.get("publication_year", 0),
        "cited": work.get("cited_by_count", 0),
        "doi": work.get("doi", ""),
        "venue": (src.get("display_name") or "").encode("ascii", "replace").decode(),
        "oa": oa.get("is_oa", False),
        "oa_url": oa.get("oa_url", ""),
        "id": work.get("id", "")
    }

queries = [
    "odor source localization reinforcement learning robot",
    "gas source localization deep reinforcement learning",
    "chemical plume tracking reinforcement learning simulation",
    "mobile robot gas leak localization Bayesian dataset",
    "PMFS gas source localization MAPIRlab",
    "GADEN simulator gas dispersion robot olfaction",
    "infotaxis gas source localization algorithm",
    "bio-inspired odor source localization drone",
    "gas distribution mapping neural network robot",
    "sim-to-real olfactory navigation UAV"
]

all_results = {}
for q in queries:
    print(f"\n=== {q} ===")
    result = search_openalex(q, per_page=15)
    if "error" in result:
        print(f"  ERROR: {result['error']}")
        continue
    papers = []
    for w in result.get("results", []):
        p = extract(w)
        papers.append(p)
        oa_mark = "OA" if p["oa"] else "PAY"
        t = p['title'][:85]
        v = p['venue'][:30]
        print(f"  [{p['year']}] {t} | cite={p['cited']} | {oa_mark} | {v}")
    all_results[q] = papers
    time.sleep(0.3)

with open("D:/ZYC/A-gas/literature_review/openalex_targeted_round6.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print("\nDone.")
