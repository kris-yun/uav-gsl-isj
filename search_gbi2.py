import json, urllib.request

queries = [
    ("SafeBayes Grunwald", "safe+bayesian+grunwald+learning+rate"),
    ("GBI Syring Bhatt", "generalized+bayesian+inference+syring+bhatt"),
    ("Tempered Posterior Robust", "tempered+posterior+robust+inference+misspecification"),
    ("Power Posterior Learning Rate", "power+posterior+learning+rate+selection"),
    ("Bayesian Learning Rate Calibration", "bayesian+learning+rate+calibration+posterior"),
    ("GBI fractional likelihood 2023-2026", "fractional+likelihood+posterior+robust+inference"),
]

for label, q in queries:
    url = f"https://api.openalex.org/works?search={q}&sort=publication_year:desc&per_page=6&select=id,display_name,publication_year,cited_by_count"
    try:
        data = json.loads(urllib.request.urlopen(url).read())
        print(f"\n=== {label} ===")
        for w in data.get("results", []):
            print(f"  {w['publication_year']} | cit={w['cited_by_count']} | {w['display_name'][:130]}")
    except:
        print(f"\n=== {label} === FAILED")
