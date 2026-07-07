import sys, io, urllib.request, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Search Semantic Scholar API for recent papers
queries = [
    "tempered posterior Bayesian inference convergence rate 2024",
    "online learning with forgetting non-stationary regret bound 2024",
    "regularized posterior contraction misspecification 2024",
    "Bayesian active learning information gain acquisition 2024 2025",
    "posterior collapse recovery variational inference 2024",
    "discounted weighted online learning non-stationary 2024 2025",
]

for q in queries:
    print(f"\n### Query: {q}")
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={q.replace(' ','+')}&year=2023-2026&limit=3&fields=title,authors,year,venue,externalIds,abstract"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        for p in data.get("data", []):
            title = p.get("title", "?")
            year = p.get("year", "?")
            venue = p.get("venue", "?")
            arxiv = p.get("externalIds", {}).get("ArXiv", "")
            doi = p.get("externalIds", {}).get("DOI", "")
            abstract = (p.get("abstract", "") or "")[:200]
            print(f"  - [{year}] {title}")
            print(f"    Venue: {venue} | arXiv: {arxiv} | DOI: {doi}")
            print(f"    Abstract: {abstract}...")
    except Exception as e:
        print(f"  Error: {e}")
