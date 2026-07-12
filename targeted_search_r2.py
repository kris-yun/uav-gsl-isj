import json, urllib.request, urllib.parse, time

API_KEY = "s2k-DJ79WAMVOUXsjHZFtpjAKTOqMIqKoZpKTIvHZUV5"
s2_base = "https://api.semanticscholar.org/graph/v1/paper/search"
output = r"D:\ZYC\A-gas\literature_targeted_search.txt"

def search_s2(query, year="2023-2026", limit=5):
    encoded = urllib.parse.quote_plus(query)
    url = f"{s2_base}?query={encoded}&year={year}&limit={limit}&fields=title,year,citationCount,venue,abstract,externalIds"
    req = urllib.request.Request(url, headers={"x-api-key": API_KEY})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return data.get("data", [])
    except Exception as e:
        return [{"error": str(e)}]

queries = [
    # Key specific papers
    ("entrotaxis gas source search", "2023-2026"),
    ("Bissiri Holmes Walker Gibbs posterior", "2016-2026"),
    ("Grunwald safe Bayesian learning rate", "2012-2026"),
    ("Wenzel cold posterior NeurIPS", "2020-2026"),
    ("Robust Bayesian tempered posterior optimization", "2024-2026"),
    ("anytime valid Poisson process confidence", "2024-2026"),
    ("surprisal self-information Bayesian update", "2023-2026"),
    ("adaptive forgetting factor Bayesian estimation", "2024-2026"),
    ("GSL indoor UAV 2024 2025 survey", "2024-2026"),
    ("Bayesian optimization sensor adaptive", "2024-2026"),
    ("posterior contraction misspecified model rate", "2023-2026"),
    ("information theoretic search mobile robot", "2024-2026"),
    ("sequential decision Bayesian stopping rule", "2024-2026"),
    ("GADEN gas dispersion simulation robot", "2023-2026"),
    ("olfactory robot infotaxis entrotaxis comparison", "2023-2026"),
]

with open(output, "a", encoding="utf-8") as f:
    f.write("\n\n=== Targeted Search Round 2 ===\n\n")

for i, (q, years) in enumerate(queries):
    print(f"[{i+1}/{len(queries)}] {q[:50]}...")
    results = search_s2(q, years)
    time.sleep(1.2)
    
    with open(output, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"[R2-{i+1}] {q}\n")
        f.write(f"{'='*70}\n")
        if results and "error" not in results[0]:
            for p in results:
                y = p.get("year", "?")
                c = p.get("citationCount", 0)
                t = p.get("title", "N/A")
                v = p.get("venue", "")[:50]
                doi = (p.get("externalIds") or {}).get("DOI", "")
                abstract = (p.get("abstract") or "")[:300]
                f.write(f"  {y} | cit={c} | {v}\n")
                f.write(f"    Title: {t}\n")
                if doi: f.write(f"    DOI: {doi}\n")
                if abstract: f.write(f"    Abstract: {abstract}\n")
                f.write("\n")
            print(f"  Found {len(results)}")
        else:
            err = results[0].get("error", "no results") if results else "empty"
            f.write(f"  [ERROR] {err}\n")
            print(f"  Error: {err}")

print("\nDone Round 2!")
