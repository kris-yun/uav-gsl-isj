import json, urllib.request

titles = [
    "Learning rate selection via weighted Fisher divergence",
    "Statistical Guarantees for Data-driven Posterior Tempering",
    "Safe Bayesian inference",
    "General framework for updating belief distributions",
    "Calibrating Generalized Posteriors",
    "Robust Generalised Bayesian Inference",
    "Inconsistency of Bayesian Inference for Misspecified",
    "Anytime valid e-process",
    "Adaptive conformal inference",
]

for t in titles:
    url = f"https://api.openalex.org/works?search={t.replace(' ', '+')}&sort=publication_year:desc&per_page=3&select=id,display_name,publication_year,cited_by_count,doi"
    try:
        data = json.loads(urllib.request.urlopen(url).read())
        results = data.get("results", [])
        if results:
            w = results[0]
            doi = w.get("doi", "N/A")
            print(f"  {w['publication_year']} | cit={w['cited_by_count']} | {w['display_name'][:120]}")
            if doi: print(f"    DOI: {doi}")
        else:
            print(f"  [NOT FOUND] {t}")
    except Exception as e:
        print(f"  [ERROR] {t}: {e}")
