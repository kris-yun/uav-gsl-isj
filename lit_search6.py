# -*- coding: utf-8 -*-
import urllib.request, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ultra-targeted searches for specific NN combinations applicable to our problem
searches = [
    ('KAN Kolmogorov-Arnold network physics-informed scientific computing', '2024-01-01'),
    ('deep kernel learning Gaussian process Bayesian optimization', '2024-01-01'),
    ('neural process meta-learning few-shot regression', '2024-01-01'),
    ('normalizing flow posterior estimation simulation-based inference', '2024-01-01'),
    ('physics-informed neural network residual learning correction', '2024-01-01'),
    ('state space model Mamba time series sensor', '2024-01-01'),
    ('neural operator learning PDE solution surrogate', '2024-01-01'),
    ('energy-based model unnormalized density estimation', '2024-01-01'),
    ('variational inference implicit likelihood posterior', '2024-01-01'),
    ('Bayesian neural network uncertainty calibration', '2024-01-01'),
    ('ensemble Kalman filter neural network hybrid', '2024-01-01'),
    ('particle filter neural network proposal distribution', '2024-01-01'),
    ('Monte Carlo dropout Bayesian approximation localization', '2024-01-01'),
    ('message passing neural network belief propagation', '2024-01-01'),
    ('Hamiltonian Monte Carlo posterior sampling neural', '2024-01-01'),
    ('implicit neural representation coordinate-based signal', '2024-01-01'),
    ('meta-learning optimization-based fast adaptation', '2024-01-01'),
    ('contrastive predictive coding representation learning', '2024-01-01'),
    ('reward-free exploration information gain acquisition', '2024-01-01'),
    ('successor representation reinforcement learning', '2024-01-01'),
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
print(f'\n=== ULTRA-TARGETED NN COMBINATIONS ({len(all_papers)} total) ===')
for p in sorted_papers:
    if p[0] not in seen:
        seen.add(p[0])
        line = f'{p[1]} | {p[2][:50]} | cited:{p[3]} | {p[0][:140]}'
        print(line)
        if len(seen) >= 80:
            break