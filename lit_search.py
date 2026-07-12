import urllib.request, json, time

searches = [
    ('physics-informed residual learning source localization', '2025-01-01'),
    ('generalized Bayesian inference adaptive temperature', '2024-01-01'),
    ('anytime-valid e-process stopping rule', '2024-01-01'),
    ('gas source localization unmanned aerial vehicle', '2024-01-01'),
    ('model misspecification robust posterior correction', '2024-01-01'),
    ('conformal prediction adaptive distribution-free', '2025-01-01'),
    ('Bayesian optimization active sensing localization', '2025-01-01'),
    ('drift diffusion model decision stopping', '2025-01-01'),
    ('spatiotemporal feature fusion sensor localization', '2025-01-01'),
    ('Gaussian process height selection UAV', '2024-01-01'),
]

all_papers = []
for idx, (query, date) in enumerate(searches):
    url = 'https://api.openalex.org/works?search=' + query.replace(' ','+') + '&filter=from_publication_date:' + date + '&sort=relevance_score:desc&per_page=10'
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'research-agent/1.0'})
        resp = urllib.request.urlopen(req, timeout=20)
        data = json.loads(resp.read())
        for w in data.get('results', []):
            title = w.get('title','')
            year = w.get('publication_year','')
            loc = w.get('primary_location') or {}
            src = (loc.get('source') or {}).get('display_name','')
            cited = w.get('cited_by_count',0)
            doi = w.get('doi','')
            all_papers.append((title, year, src, cited, doi, query))
        print(f'[{idx+1}/{len(searches)}] {query}: {len(data.get("results",[]))} results')
    except Exception as e:
        print(f'[{idx+1}] Error: {e}')
    time.sleep(2)

seen = set()
sorted_papers = sorted(all_papers, key=lambda x: -x[3])
print(f'\n=== TOP PAPERS ({len(all_papers)} total, {len(set(p[0] for p in all_papers))} unique) ===')
for p in sorted_papers:
    if p[0] not in seen:
        seen.add(p[0])
        print(f'{p[1]} | {p[2][:50]} | cited:{p[3]} | {p[0][:140]}')
        if len(seen) >= 60:
            break
