#!/usr/bin/env python3
import urllib.request, urllib.parse, json

queries = [
    'infotaxis odor source localization',
    'safe anytime-valid inference e-process',
    'gas source localization UAV Bayesian',
    'chemical plume tracing mobile robot',
    'filament model gas dispersion source localization',
    'surge cast gas source localization',
    'PMFS gas source localization probability',
    'IEEE sensors journal gas source localization',
]

all_results = []
for q in queries:
    url = 'https://api.openalex.org/works?search=' + urllib.parse.quote(q) + '&per_page=5&select=title,publication_year,doi,authorships'
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        results = data.get('results', [])
        for r in results:
            yr = r.get('publication_year', '?')
            ti = r.get('title', '?')
            doi = r.get('doi', '')
            authors = [a.get('raw_author_name', '') for a in (r.get('authorships') or [])[:2]]
            all_results.append((yr, ti, doi, ', '.join(authors), q))
    except:
        pass

seen = set()
unique = []
for yr, ti, doi, auth, q in sorted(all_results, key=lambda x: -x[0]):
    if ti not in seen:
        seen.add(ti)
        unique.append((yr, ti, doi, auth, q))

print("=== Key References ===")
for yr, ti, doi, auth, q in unique[:30]:
    print(f"[{yr}] {ti}")
    print(f"    Authors: {auth}")
    if doi:
        print(f"    DOI: {doi}")
    print()
