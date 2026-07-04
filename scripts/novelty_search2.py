import urllib.request, urllib.parse, json

queries = [
    'binary detection robot chemical plume tracing',
    'Bernoulli likelihood gas source localization',
    'non-detection exclude source location robot',
    'event-based observation model source localization',
    'anytime-valid inference robotic search',
    'Ville inequality source localization',
    'e-process search convergence guarantee',
    'infotaxis stopping criterion formal guarantee',
]

for q in queries:
    url = 'https://api.openalex.org/works?search=' + urllib.parse.quote(q) + '&per_page=5&select=title,publication_year,doi,concepts'
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        results = data.get('results', [])
        print('--- Query: ' + q)
        for r in results:
            yr = r.get('publication_year', '?')
            ti = r.get('title', '?')
            print('  [' + str(yr) + '] ' + ti)
        if not results:
            print('  (no results)')
    except Exception as e:
        print('--- Query: ' + q + ' -> ERROR: ' + str(e))
    print()
