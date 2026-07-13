# -*- coding: utf-8 -*-
import urllib.request, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

searches = [
    ('neural network residual correction physics model PDE', '2024-01-01'),
    ('graph neural network source localization sensor', '2024-01-01'),
    ('transformer spatial temporal sensor fusion localization', '2024-01-01'),
    ('physics informed neural network Bayesian uncertainty quantification', '2025-01-01'),
    ('neural process Gaussian process meta-learning localization', '2024-01-01'),
    ('flow matching simulation-based inference calibration', '2024-01-01'),
    ('diffusion model inverse problem source estimation', '2024-01-01'),
    ('attention mechanism sensor array signal processing', '2024-01-01'),
    ('neural ODE dynamical system state estimation', '2024-01-01'),
    ('equivariant neural network physical symmetry', '2024-01-01'),
    ('Kolmogorov-Arnold network KAN function approximation', '2024-01-01'),
    ('mixture of experts adaptive computation routing', '2024-01-01'),
    ('contrastive learning representation sensor signal', '2024-01-01'),
    ('neural Bayesian optimization acquisition function', '2024-01-01'),
    ('deep kernel learning Gaussian process scalable', '2024-01-01'),
    ('normalizing flow density estimation posterior inference', '2024-01-01'),
    ('active inference free energy perception action', '2024-01-01'),
    ('neural tangent kernel generalization theory', '2024-01-01'),
    ('model-based reinforcement learning world model', '2025-01-01'),
    ('physics guided machine learning surrogate model', '2025-01-01'),
    ('multi-agent cooperative search exploration', '2024-01-01'),
    ('neural posterior estimation likelihood-free', '2024-01-01'),
    ('amortized inference variational autoencoder simulator', '2024-01-01'),
    ('energy-based model score matching Langevin', '2024-01-01'),
    ('convolutional neural network spatial feature extraction', '2025-01-01'),
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
print(f'\n=== NEURAL NETWORK + PHYSICS COMBINATIONS ({len(all_papers)} total) ===')
for p in sorted_papers:
    if p[0] not in seen:
        seen.add(p[0])
        line = f'{p[1]} | {p[2][:50]} | cited:{p[3]} | {p[0][:140]}'
        print(line)
        if len(seen) >= 100:
            break