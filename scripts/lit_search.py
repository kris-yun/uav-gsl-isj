#!/usr/bin/env python3
import urllib.request, urllib.parse, json

queries = [
    'anytime-valid inference robotics stopping',
    'e-process search sequential decision',
    'posterior credible region stopping criterion Bayesian search',
    'event-driven gas detection binary sensor localization',
    'infotaxis convergence guarantee formal proof',
    'Bayesian search theory exponential convergence',
    'non-detection information gain source localization',
    'adaptive search granularity posterior entropy',
]

all_results = []
for q in queries:
    url = 'https://api.openalex.org/works?search=' + urllib.parse.quote(q) + '&per_page=3&select=title,publication_year,doi'
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        results = data.get('results', [])
        for r in results:
            yr = r.get('publication_year', '?')
            ti = r.get('title', '?')
            doi = r.get('doi', '')
            if yr and yr >= 2020:
                all_results.append((yr, ti, doi, q))
    except:
        pass

# Deduplicate and sort
seen = set()
unique = []
for yr, ti, doi, q in sorted(all_results, key=lambda x: -x[0]):
    if ti not in seen:
        seen.add(ti)
        unique.append((yr, ti, doi, q))

print("=== Recent Literature (2020+) ===")
for yr, ti, doi, q in unique[:25]:
    print(f"[{yr}] {ti}")
    if doi:
        print(f"    {doi}")
    print(f"    Query: {q}")
    print()
