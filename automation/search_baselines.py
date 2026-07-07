import requests
import json
import time

api_key = 's2k-DJ79WAMVOUXsjHZFtpjAKTOqMIqKoZpKTIvHZUV5'
headers = {'Authorization': f'Bearer {api_key}'}

queries = [
    'infotaxis gas source localization',
    'particle filter odor source localization robot',
    'surge cast klinotaxis olfactory',
    'kernel DM+V gas distribution mapping',
]

for q in queries:
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={q}&limit=3&fields=title,url,year,externalIds'
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f'\n=== {q} ===')
            for p in data.get('data', []):
                print(f"  {p.get('year')}: {p.get('title')}")
                print(f"    URL: {p.get('url')}")
        else:
            print(f'Status {resp.status_code} for {q}')
    except Exception as e:
        print(f'Error for {q}: {e}')
    time.sleep(1.1)  # Rate limit: 1 req/sec
