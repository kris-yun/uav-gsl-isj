import urllib.request, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

searches = [
    ('Poisson filament model gas detection plume', '2020-01-01'),
    ('generalized Bayesian posterior concentration rate', '2022-01-01'),
    ('learned residual physics model correction robot', '2023-01-01'),
    ('wind adaptive gas source localization', '2020-01-01'),
    ('event-driven Bayesian inference sensor', '2023-01-01'),
    ('anytime-valid e-value sequential analysis', '2023-01-01'),
    ('plug-in play gas source localization method', '2023-01-01'),
    ('informed proposal distribution MCMC localization', '2023-01-01'),
    ('misspecified likelihood ratio test correction', '2023-01-01'),
    ('model error bound posterior Bayesian robust', '2023-01-01'),
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
print(f'\n=== HIGHLY TARGETED RESULTS ({len(all_papers)} total) ===')
for p in sorted_papers:
    if p[0] not in seen:
        seen.add(p[0])
        line = f'{p[1]} | {p[2][:50]} | cited:{p[3]} | {p[0][:140]}'
        print(line)
        if len(seen) >= 80:
            break
