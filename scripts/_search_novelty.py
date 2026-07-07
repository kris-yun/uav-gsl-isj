import urllib.request, json

queries = [
    'PCA gas source localization direction estimation',
    'Peclet number adaptive kernel gas plume',
    'compressed sensing sparse source probability gas localization',
    'cluster shape gas source direction',
    'gradient direction gas source estimation low wind',
]

for q in queries:
    url = 'https://api.semanticscholar.org/graph/v1/paper/search?query=' + q.replace(' ', '+') + '&limit=3&fields=title,year,venue'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        print(f'\n=== {q} ===')
        for p in data.get('data', []):
            yr = p.get('year', '')
            vn = p.get('venue', '')
            tl = p.get('title', '')
            print(f'  {yr} | {vn} | {tl}')
        if not data.get('data'):
            print('  NO RESULTS - genuinely novel!')
    except Exception as e:
        print(f'  Error: {e}')
