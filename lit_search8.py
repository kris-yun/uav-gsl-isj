# -*- coding: utf-8 -*-
import urllib.request, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Search for the MOST recent and specific innovations
searches = [
    ('KAN scientific computing 2025 2026 interpretable symbolic', '2025-01-01'),
    ('physics-informed KAN PDE solving 2025', '2025-01-01'),
    ('deep kernel learning 2025 Gaussian process', '2025-01-01'),
    ('neural posterior estimation 2025 simulation inference', '2025-01-01'),
    ('active inference robot exploration 2025', '2025-01-01'),
    ('energy-based model score matching 2025', '2025-01-01'),
    ('mixture of experts adaptive routing 2025', '2025-01-01'),
    ('state space model Mamba 2025 efficient sequence', '2025-01-01'),
    ('neural ODE continuous-depth 2025 dynamical', '2025-01-01'),
    ('equivariant neural network symmetry physical 2025', '2025-01-01'),
    ('implicit neural representation coordinate 2025', '2025-01-01'),
    ('meta-learning few-shot adaptation 2025', '2025-01-01'),
    ('contrastive learning self-supervised 2025 sensor', '2025-01-01'),
    ('Bayesian deep learning uncertainty 2025', '2025-01-01'),
    ('transformer attention mechanism 2025 signal', '2025-01-01'),
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
print(f'\n=== LATEST 2025-2026 INNOVATIONS ({len(all_papers)} total) ===')
for p in sorted_papers:
    if p[0] not in seen:
        seen.add(p[0])
        line = f'{p[1]} | {p[2][:50]} | cited:{p[3]} | {p[0][:140]}'
        print(line)
        if len(seen) >= 80:
            break