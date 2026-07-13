# -*- coding: utf-8 -*-
import urllib.request, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

searches = [
    ('KAN hybrid architecture BiLSTM transformer attention', '2024-01-01'),
    ('Mamba state space model localization tracking', '2024-01-01'),
    ('physics-informed KAN turbulence convection Science Advances', '2024-01-01'),
    ('KAN graph neural network molecular property Nature', '2024-01-01'),
    ('deep operator network KAN mechanics CMAME', '2024-01-01'),
    ('neural posterior estimation gravitational wave', '2024-01-01'),
    ('simulation-based inference toolkit sbi', '2024-01-01'),
    ('equivariant neural network physical symmetry 2025', '2025-01-01'),
    ('Bayesian neural network uncertainty quantification 2025', '2025-01-01'),
    ('normalizing flow density estimation inverse problem', '2024-01-01'),
    ('active perception robot information gain exploration', '2024-01-01'),
    ('neural tangent kernel generalization overparameterized', '2024-01-01'),
    ('implicit neural representation coordinate signal', '2024-01-01'),
    ('meta-learning optimization fast adaptation few-shot', '2024-01-01'),
    ('contrastive learning sensor signal representation', '2024-01-01'),
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
print(f'\n=== HYBRID ARCHITECTURES ({len(all_papers)} total) ===')
for p in sorted_papers:
    if p[0] not in seen:
        seen.add(p[0])
        line = f'{p[1]} | {p[2][:50]} | cited:{p[3]} | {p[0][:140]}'
        print(line)
        if len(seen) >= 80:
            break