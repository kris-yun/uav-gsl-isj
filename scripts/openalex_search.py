import requests
import json
import time
import sys

def search_openalex(query, per_page=25, page=1):
    """Search OpenAlex API for papers"""
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per_page": per_page,
        "page": page,
        "sort": "cited_by_count:desc"
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def extract_paper_info(work):
    """Extract key info from an OpenAlex work"""
    return {
        "title": work.get("title", ""),
        "year": work.get("publication_year", ""),
        "cited_by": work.get("cited_by_count", 0),
        "doi": work.get("doi", ""),
        "venue": work.get("primary_location", {}).get("source", {}).get("display_name", "") if work.get("primary_location") else "",
        "open_access": work.get("open_access", {}).get("is_oa", False),
        "oa_url": work.get("open_access", {}).get("oa_url", ""),
        "concepts": [c.get("display_name", "") for c in work.get("concepts", [])[:5]],
        "abstract_inv": work.get("abstract_inverted_index", {})
    }

def reconstruct_abstract(inv_index):
    """Reconstruct abstract from inverted index"""
    if not inv_index:
        return ""
    word_positions = []
    for word, positions in inv_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions)

if __name__ == "__main__":
    queries = [
        "UAV gas source localization reinforcement learning",
        "robot odor source localization deep learning public dataset",
        "chemical plume tracking mobile robot benchmark",
        "gas leak detection drone machine learning dataset",
        "indoor gas source localization neural network",
        "multi-robot gas source localization open source"
    ]
    
    all_results = {}
    for q in queries:
        print(f"\n=== Query: {q} ===")
        result = search_openalex(q, per_page=15)
        if "error" in result:
            print(f"Error: {result['error']}")
            continue
        papers = []
        for work in result.get("results", []):
            info = extract_paper_info(work)
            info["abstract"] = reconstruct_abstract(info.pop("abstract_inv", {}))[:500]
            papers.append(info)
            print(f"  [{info['year']}] {info['title'][:80]}... | cited={info['cited_by']} | OA={info['open_access']} | {info['venue'][:40]}")
        all_results[q] = papers
        time.sleep(0.5)
    
    with open("D:/ZYC/A-gas/literature_review/openalex_round6_raw.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print("\nSaved to literature_review/openalex_round6_raw.json")
