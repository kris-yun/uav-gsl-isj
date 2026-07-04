import urllib.request, urllib.parse, json

queries = [
    'event-driven Bayesian gas source localization',
    'binary detection gas source localization Bayesian',
    'non-detection information gas source localization',
    'anytime-valid stopping source localization',
    'Poisson process gas plume source localization',
    'infotaxis binary detection',
    'filament arrival model gas source',
    'e-process robotic source localization',
]

for q in queries:
    url = 'https://api.openalex.org/works?search=' + urllib.parse.quote(q) + '&per_page=3&select=title,publication_year,doi'
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        results = data.get('results', [])
        print('--- Query: ' + q)
        for r in results:
            yr = r.get('publication_year', '?')
            ti = r.get('title', '?')
            print('  [' + str(yr) + '] ' + ti)
            doi = r.get('doi')
            if doi:
                print('    DOI: ' + doi)
        if not results:
            print('  (no results)')
    except Exception as e:
        print('--- Query: ' + q + ' -> ERROR: ' + str(e))
    print()
