import urllib.request, urllib.parse, json

# Search specifically for the Distill-Belief paper
url = 'https://api.openalex.org/works?search=Distill-Belief+Closed-Loop+Inverse+Source+Localization&per_page=1&select=title,publication_year,doi,abstract_inverted_index'
try:
    resp = urllib.request.urlopen(url, timeout=10)
    data = json.loads(resp.read())
    results = data.get('results', [])
    if results:
        r = results[0]
        print('Title: ' + str(r.get('title')))
        print('Year: ' + str(r.get('publication_year')))
        print('DOI: ' + str(r.get('doi')))
        # Reconstruct abstract from inverted index
        aii = r.get('abstract_inverted_index', {})
        if aii:
            words = {}
            for word, positions in aii.items():
                for pos in positions:
                    words[pos] = word
            abstract = ' '.join(words[k] for k in sorted(words.keys()))
            print('Abstract: ' + abstract[:500])
    else:
        print('Not found')
except Exception as e:
    print('ERROR: ' + str(e))

print()

# Also search for binary detection in search theory
url2 = 'https://api.openalex.org/works?search=binary+observation+Bayesian+search+target+convergence&per_page=5&select=title,publication_year,doi'
try:
    resp = urllib.request.urlopen(url2, timeout=10)
    data = json.loads(resp.read())
    results = data.get('results', [])
    print('--- Related: Bayesian search with binary observation')
    for r in results:
        yr = r.get('publication_year', '?')
        ti = r.get('title', '?')
        print('  [' + str(yr) + '] ' + ti)
except Exception as e:
    print('ERROR: ' + str(e))
