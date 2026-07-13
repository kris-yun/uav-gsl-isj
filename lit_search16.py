# -*- coding: utf-8 -*-
import urllib.request, json, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = "s2k-DJ79WAMVOUXsjHZFtpjAKTOqMIqKoZpKTIvHZUV5"

searches = [
    'KAN gas source localization',
    'KAN sensor network localization',
    'KAN Bayesian inference posterior',
    'KAN physical model correction residual',
    'KAN interpretable scientific machine learning',
]

all_papers = []
for idx, query in enumerate(searches):
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={query.replace(" ","+")}&limit=10&fields=title,year,venue,citationCount'
    try:
        req = urllib.request.Request(url, headers={'x-api-key': API_KEY})
        resp = urllib.request.urlopen(req, timeout=20)
        data = json.loads(resp.read())
        for w in data.get('data', []):
            title = (w.get('title') or '').encode('ascii','replace').decode()
            year = w.get('year','')
            venue = (w.get('venue') or '').encode('ascii','replace').decode()
            cited = w.get('citationCount',0)
            all_papers.append((title, year, venue, cited, query))
        print(f'[{idx+1}/{len(searches)}] {query}: {len(data.get("data",[]))} results')
    except Exception as e:
        print(f'[{idx+1}] Error: {e}')
    time.sleep(1.5)

seen = set()
sorted_papers = sorted(all_papers, key=lambda x: -x[3])
print(f'\n=== KAN APPLICATIONS via S2 ({len(all_papers)} total) ===')
for p in sorted_papers:
    if p[0] not in seen:
        seen.add(p[0])
        line = f'{p[1]} | {p[2][:50]} | cited:{p[3]} | {p[0][:140]}'
        print(line)
        if len(seen) >= 30:
            break