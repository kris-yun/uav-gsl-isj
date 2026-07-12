import json, urllib.request

API_KEY = "s2k-DJ79WAMVOUXsjHZFtpjAKTOqMIqKoZpKTIvHZUV5"
base = "https://api.semanticscholar.org/graph/v1/paper/search"

queries = [
    "generalized Bayesian inference learning rate",
    "SafeBayes posterior tempering misspecification",
    "adaptive temperature posterior robust",
    "anytime-valid inference e-process stopping",
    "conformal prediction robust inference",
    "gas source localization UAV Bayesian",
    "olfactory navigation robot information theory",
    "generalized posterior calibration 2024 2025",
]

for q in queries:
    url = f"{base}?query={q.replace(' ', '+')}&year=2023-2026&limit=5&fields=title,year,citationCount,venue,externalIds"
    req = urllib.request.Request(url, headers={"x-api-key": API_KEY})
    try:
        data = json.loads(urllib.request.urlopen(req).read())
        papers = data.get("data", [])
        print(f"\n=== {q} ===")
        for p in papers[:3]:
            y = p.get("year", "?")
            c = p.get("citationCount", 0)
            t = p.get("title", "")[:110]
            v = p.get("venue", "")[:40]
            doi = p.get("externalIds", {}).get("DOI", "")
            print(f"  {y} | cit={c} | {v} | {t}")
            if doi:
                print(f"    DOI: {doi}")
    except Exception as e:
        print(f"\n=== {q} === ERROR: {e}")
