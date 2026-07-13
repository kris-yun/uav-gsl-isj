# -*- coding: utf-8 -*-
import urllib.request, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

searches = [
    ('KAN inverse problem source estimation 2025', '2025-01-01'),
    ('KAN Bayesian posterior estimation 2025', '2025-01-01'),
    ('KAN sensor signal processing 2025', '2025-01-01'),
    ('KAN robotics control 2025', '2025-01-01'),
    ('KAN fluid dynamics simulation 2025', '2025-01-01'),
    ('KAN uncertainty quantification 2025', '2025-01-01'),
    ('KAN PDE-constrained optimization 2025', '2025-01-01'),
    ('KAN sparse regression system identification 2025', '2025-01-01'),
    ('KAN time series forecasting 2025', '2025-01-01'),
    ('KAN anomaly detection 2025', '2025-01-01'),
]

all_papers = []
for idx, (query, date) in enumerate(searches):
    url = 'https://api.openalex.org/works?search=' + query.replace(' ','+') + '&filter=from_publication_date:' + date + '&sort=relevance_score:desc&per_page=8'
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'research-agent/1.0'})
        resp = urllib.request.urlopen(req, timeout=20)
        data = json.loads(resp.read())
        for w in data.get('results', []):
            title = (w.get('title') or '').encode('ascii','replace').decode()
            year = w.get('publication_year','')
            loc = w.get('primary_location') or {}
            src = ((loc.get('source') or {}).get('display_name') or '').encode('ascii','replace').decode()
            cited = w.get('cited_by_count',0)
            doi = w.get('doi','')
            all_papers.append((title, year, src, cited, doi, query))
        print(f'[{idx+1}/{len(searches)}] {query}: {len(data.get("results",[]))} results')
    except Exception as e:
        print(f'[{idx+1}] Error: {e}')
    time.sleep(2)

seen = set()
sorted_papers = sorted(all_papers, key=lambda x: -x[3])
print(f'\n=== KAN APPLICATIONS 2025 ({len(all_papers)} total) ===')
for p in sorted_papers:
    if p[0] not in seen:
        seen.add(p[0])
        line = f'{p[1]} | {p[2][:50]} | cited:{p[3]} | {p[0][:140]}'
        print(line)
        if len(seen) >= 60:
            break