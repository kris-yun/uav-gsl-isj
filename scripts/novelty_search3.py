import urllib.request, urllib.parse, json

queries = [
    'Distill-Belief Closed-Loop Inverse Source Localization',
    'infotaxis non-detection information exclusion',
    'Bayesian search binary sensor convergence guarantee',
    'gas source localization e-process anytime-valid',
    'conformal prediction gas source localization',
    'posterior credible region stopping criterion search',
]

for q in queries:
    url = 'https://api.openalex.org/works?search=' + urllib.parse.quote(q) + '&per_page=3&select=title,publication_year,doi,authorships'
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        results = data.get('results', [])
        print('--- Query: ' + q)
        for r in results:
            yr = r.get('publication_year', '?')
            ti = r.get('title', '?')
            authors = [a.get('raw_author_name','') for a in (r.get('authorships') or [])[:3]]
            astr = ', '.join(authors)
            print('  [' + str(yr) + '] ' + ti)
            print('    Authors: ' + astr)
        if not results:
            print('  (no results)')
    except Exception as e:
        print('--- Query: ' + q + ' -> ERROR: ' + str(e))
    print()
