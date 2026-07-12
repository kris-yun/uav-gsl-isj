import json, urllib.request, time

API_KEY = "s2k-DJ79WAMVOUXsjHZFtpjAKTOqMIqKoZpKTIvHZUV5"
s2_base = "https://api.semanticscholar.org/graph/v1/paper/search"
oa_base = "https://api.openalex.org/works"

output = r"D:\ZYC\A-gas\literature_deep_search.txt"

def search_s2(query, year="2024-2026", limit=5):
    url = f"{s2_base}?query={query}&year={year}&limit={limit}&fields=title,year,citationCount,venue,abstract,externalIds"
    req = urllib.request.Request(url, headers={"x-api-key": API_KEY})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return data.get("data", [])
    except Exception as e:
        return [{"error": str(e)}]

def search_oa(query, year="2024-2026"):
    url = f"{oa_base}?search={query}&filter=publication_year:{year.split('-')[0]}-{year.split('-')[1]}&sort=publication_year:desc&per_page=5&select=id,display_name,publication_year,cited_by_count,doi"
    try:
        data = json.loads(urllib.request.urlopen(url, timeout=15).read())
        return data.get("results", [])
    except Exception as e:
        return [{"error": str(e)}]

queries = [
    # Core GBI theory
    ("generalized Bayesian inference misspecified model convergence rate", "S2", "2023-2026"),
    ("safe Bayesian learning rate posterior tempered", "S2", "2023-2026"),
    ("power posterior beta posterior convergence misspecification", "S2", "2023-2026"),
    ("posterior tempering adaptive temperature selection", "S2", "2023-2026"),
    # E-process and anytime valid
    ("anytime valid inference e-process sequential testing", "S2", "2024-2026"),
    ("e-value martingale testing stopping rule", "S2", "2024-2026"),
    # GSL specific
    ("gas source localization Bayesian robot", "S2", "2023-2026"),
    ("olfactory source localization information gain", "S2", "2023-2026"),
    ("plume tracking robot UAV adaptive", "S2", "2023-2026"),
    # Active inference / free energy
    ("active inference robot exploration free energy", "S2", "2024-2026"),
    # Robust Bayesian
    ("robust Bayesian inference divergence loss function", "S2", "2023-2026"),
    # Event-triggered estimation
    ("event triggered estimation sensor adaptive", "S2", "2023-2026"),
    # Cross-domain
    ("surprisal information gain adaptive learning rate", "S2", "2023-2026"),
    ("Kalman filter innovation adaptive estimation", "S2", "2024-2026"),
    # UAV specific
    ("UAV indoor navigation autonomous search", "S2", "2024-2026"),
]

with open(output, "w", encoding="utf-8") as f:
    f.write("=== Deep Literature Search Results ===\nDate: 2026-07-11\n\n")

for i, (q, source, years) in enumerate(queries):
    print(f"[{i+1}/{len(queries)}] Searching: {q[:60]}...")
    
    with open(output, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"[{i+1}] {q} ({source}, {years})\n")
        f.write(f"{'='*70}\n")
        
        if source == "S2":
            results = search_s2(q, years)
            time.sleep(1.5)  # Respect rate limit
            if results and "error" not in results[0]:
                for p in results:
                    y = p.get("year", "?")
                    c = p.get("citationCount", 0)
                    t = p.get("title", "N/A")
                    v = p.get("venue", "")
                    doi = p.get("externalIds", {}).get("DOI", "") if p.get("externalIds") else ""
                    abstract = (p.get("abstract") or "")[:200]
                    f.write(f"  {y} | cit={c} | {v[:40]}\n")
                    f.write(f"    Title: {t}\n")
                    if doi: f.write(f"    DOI: {doi}\n")
                    if abstract: f.write(f"    Abstract: {abstract}...\n")
                    f.write("\n")
                print(f"  Found {len(results)} papers")
            else:
                err = results[0].get("error", "no results") if results else "empty"
                f.write(f"  [ERROR/EMPTY] {err}\n")
                print(f"  Error: {err}")

print("\nDone!")
