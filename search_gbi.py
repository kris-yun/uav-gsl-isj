import json, urllib.request

queries = [
    ("GBI Recent", "generalized+bayesian+inference+robust"),
    ("Safe Bayes", "safe+bayesian+learning+rate+posterior+tempering"),
    ("Frac Posterior", "fractional+posterior+power+likelihood+robust"),
    ("Tempered Posterior", "tempered+posterior+adaptive+temperature"),
]

for label, q in queries:
    url = f"https://api.openalex.org/works?search={q}&sort=publication_year:desc&per_page=8&select=id,display_name,publication_year,cited_by_count"
    data = json.loads(urllib.request.urlopen(url).read())
    print(f"\n=== {label} ===")
    for w in data.get("results", []):
        print(f"  {w['publication_year']} | cit={w['cited_by_count']} | {w['display_name'][:130]}")
