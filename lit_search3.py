import urllib.request, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

searches = [
    ('posterior contraction rate misspecified model Bayesian', '2023-01-01'),
    ('generalized Bayesian learning Bissiri temperature selection', '2023-01-01'),
    ('physics residual neural network correction PDE', '2024-01-01'),
    ('robot olfaction gas plume tracking Bayesian', '2024-01-01'),
    ('infotaxis information gain gas source', '2023-01-01'),
    ('adaptive conformal inference non-exchangeable', '2024-01-01'),
    ('sequential hypothesis testing e-value martingale', '2024-01-01'),
    ('sensor array localization Fisher information', '2024-01-01'),
    ('UAV 3D path planning gas detection indoor', '2024-01-01'),
    ('plug-in estimator robust misspecification calibration', '2024-01-01'),
    ('turbulent plume intermittent filament model', '2023-01-01'),
    ('deep reinforcement learning chemical source', '2024-01-01'),
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
    time.sleep(2)

seen = set()
sorted_papers = sorted(all_papers, key=lambda x: -x[3])
print(f'\n=== TOP RESULTS BY RELEVANCE ({len(all_papers)} total) ===')
for p in sorted_papers:
    if p[0] not in seen:
        seen.add(p[0])
        line = f'{p[1]} | {p[2][:50]} | cited:{p[3]} | {p[0][:140]}'
        print(line)
        if len(seen) >= 80:
            break
