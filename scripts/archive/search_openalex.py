import sys, io, urllib.request, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Use OpenAlex API (free, no rate limit)
queries = [
    "tempered posterior Bayesian learning rate convergence",
    "online learning forgetting non-stationary regret",
    "regularized posterior misspecification robust Bayesian",
    "Bayesian active learning expected information gain optimal",
    "discounted weighted online convex optimization tracking",
    "power posterior safe Bayesian inference",
]

for q in queries:
    print(f"\n### {q}")
    url = f"https://api.openalex.org/works?search={q.replace(' ','+')}&filter=from_publication_date:2023-01-01&sort=relevance_score:desc&per_page=3"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mailto:research@example.com"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        for w in data.get("results", []):
            title = w.get("title", "?")
            year = w.get("publication_year", "?")
            venue = w.get("primary_location", {}).get("source", {}).get("display_name", "?") if w.get("primary_location") else "?"
            doi = w.get("doi", "")
            print(f"  [{year}] {title}")
            print(f"    {venue} | {doi}")
    except Exception as e:
        print(f"  Error: {e}")
