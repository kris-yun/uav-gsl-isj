# -*- coding: utf-8 -*-
import urllib.request, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Final round: search for specific innovations that could strengthen our paper
searches = [
    ('symbolic regression physics discovery interpretable', '2024-01-01'),
    ('B-spline neural network function approximation', '2024-01-01'),
    ('Kolmogorov-Arnold representation theorem machine learning', '2024-01-01'),
    ('learnable activation function neural network', '2024-01-01'),
    ('interpretable residual learning scientific computing', '2024-01-01'),
]

all_papers = []
for idx, (query, date) in enumerate(searches):
    url = 'https://api.openalex.org/works?search=' + query.replace(' ','+') + '&filter=from_publication_date:' + date + '&sort=relevance_score:desc&per_page=10'
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
    time.sleep(3)

seen = set()
sorted_papers = sorted(all_papers, key=lambda x: -x[3])
print(f'\n=== SYMBOLIC + INTERPRETABLE ({len(all_papers)} total) ===')
for p in sorted_papers:
    if p[0] not in seen:
        seen.add(p[0])
        line = f'{p[1]} | {p[2][:50]} | cited:{p[3]} | {p[0][:140]}'
        print(line)
        if len(seen) >= 40:
            break