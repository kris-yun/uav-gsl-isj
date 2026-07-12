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

# More targeted queries
queries = [
    # Direct GSL papers
    ("infotaxis gas source localization", "2023-2026"),
    ("surgecast gas source", "2023-2026"),
    ("PMFS gas source localization", "2023-2026"),
    ("GrGSL gas source robot", "2023-2026"),
    ("filament model gas dispersion robot", "2023-2026"),
    # Adaptive tempering specific
    ("adaptive posterior tempering Bayesian", "2024-2026"),
    ("cold posterior effect Bayesian learning", "2023-2026"),
    ("likelihood tempering robust inference", "2023-2026"),
    # E-process specific
    ("e-process anytime valid sequential", "2023-2026"),
    ("sequential probability ratio test robot", "2023-2026"),
    # Information-theoretic search
    ("mutual information sensor placement search", "2024-2026"),
    ("information gain exploration robot Bayesian", "2024-2026"),
    # GBI applications
    ("Gibbs posterior machine learning robust", "2024-2026"),
    ("power likelihood Bayesian robust", "2023-2026"),
    # UAV gas
    ("UAV gas detection localization autonomous", "2024-2026"),
    # Event-triggered in estimation context
    ("event triggered state estimation adaptive", "2024-2026"),
]

with open(output, "w", encoding="utf-8") as f:
    f.write("=== Targeted Literature Search ===\nDate: 2026-07-11\n\n")

for i, (q, years) in enumerate(queries):
    print(f"[{i+1}/{len(queries)}] {q[:50]}...")
    results = search_s2(q, years)
    time.sleep(1.2)
    
    with open(output, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"[{i+1}] {q}\n")
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

print("\nDone!")
