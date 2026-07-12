import json, urllib.request, urllib.parse, time

API_KEY = "s2k-DJ79WAMVOUXsjHZFtpjAKTOqMIqKoZpKTIvHZUV5"
s2_base = "https://api.semanticscholar.org/graph/v1/paper/search"
oa_base = "https://api.openalex.org/works"

output = r"D:\ZYC\A-gas\literature_deep_search_v2.txt"

def search_s2(query, year="2024-2026", limit=5):
    encoded = urllib.parse.quote_plus(query)
    url = f"{s2_base}?query={encoded}&year={year}&limit={limit}&fields=title,year,citationCount,venue,abstract,externalIds"
    req = urllib.request.Request(url, headers={"x-api-key": API_KEY})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return data.get("data", [])
    except Exception as e:
        return [{"error": str(e)}]

def search_oa(query, year_from="2024", year_to="2026"):
    encoded = urllib.parse.quote_plus(query)
    url = f"{oa_base}?search={encoded}&filter=publication_year:{year_from}-{year_to}&sort=publication_year:desc&per_page=5&select=id,display_name,publication_year,cited_by_count,doi"
    try:
        data = json.loads(urllib.request.urlopen(url, timeout=15).read())
        return data.get("results", [])
    except Exception as e:
        return [{"error": str(e)}]

queries = [
    # GBI core
    ("generalized Bayesian inference misspecified convergence", "S2", "2023-2026"),
    ("safe Bayesian learning rate", "S2", "2022-2026"),
    ("power posterior beta posterior convergence", "S2", "2023-2026"),
    ("posterior tempering adaptive temperature", "S2", "2023-2026"),
    # E-process
    ("anytime valid e-process sequential", "S2", "2024-2026"),
    ("e-value martingale testing stopping", "S2", "2024-2026"),
    # GSL
    ("gas source localization Bayesian robot", "S2", "2023-2026"),
    ("olfactory source localization information", "S2", "2023-2026"),
    ("plume tracking UAV robot", "S2", "2024-2026"),
    # Active inference
    ("active inference robot exploration", "S2", "2024-2026"),
    # Robust Bayes
    ("robust Bayesian divergence loss", "S2", "2023-2026"),
    # Event-triggered
    ("event triggered estimation sensor", "S2", "2023-2026"),
    # Surprisal/info
    ("surprisal adaptive learning rate posterior", "S2", "2023-2026"),
    # KF
    ("Kalman filter innovation adaptive", "S2", "2024-2026"),
    # UAV
    ("UAV indoor navigation search rescue", "S2", "2024-2026"),
    # GSL recent
    ("gas source localization 2024 2025", "OA", ""),
    # Bayesian search
    ("Bayesian search mobile sensor adaptive", "OA", ""),
    # Conformal
    ("conformal prediction sequential decision", "OA", ""),
]

with open(output, "w", encoding="utf-8") as f:
    f.write("=== Deep Literature Search v2 ===\nDate: 2026-07-11\n\n")

for i, (q, source, years) in enumerate(queries):
    print(f"[{i+1}/{len(queries)}] {q[:50]}...")
    
    with open(output, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"[{i+1}] {q} ({source})\n")
        f.write(f"{'='*70}\n")
        
        if source == "S2":
            results = search_s2(q, years)
            time.sleep(1.5)
            if results and "error" not in results[0]:
                for p in results:
                    y = p.get("year", "?")
                    c = p.get("citationCount", 0)
                    t = p.get("title", "N/A")
                    v = p.get("venue", "")
                    doi = (p.get("externalIds") or {}).get("DOI", "")
                    abstract = (p.get("abstract") or "")[:250]
                    f.write(f"  {y} | cit={c} | {v[:50]}\n")
                    f.write(f"    Title: {t}\n")
                    if doi: f.write(f"    DOI: {doi}\n")
                    if abstract: f.write(f"    Abstract: {abstract}...\n")
                    f.write("\n")
                print(f"  Found {len(results)} papers")
            else:
                err = results[0].get("error", "no results") if results else "empty"
                f.write(f"  [ERROR] {err}\n")
                print(f"  Error: {err}")
        elif source == "OA":
            results = search_oa(q)
            time.sleep(1)
            if results and "error" not in str(results[0]):
                for w in results:
                    y = w.get("publication_year", "?")
                    c = w.get("cited_by_count", 0)
                    n = w.get("display_name", "N/A")
                    doi = w.get("doi", "")
                    f.write(f"  {y} | cit={c} | {n}\n")
                    if doi: f.write(f"    DOI: {doi}\n")
                print(f"  Found {len(results)} papers")
            else:
                f.write(f"  [NO RESULTS]\n")
                print(f"  No results")

print("\nDone!")
