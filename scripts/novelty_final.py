import urllib.request, urllib.parse, json

# Direct search for the Distill-Belief paper
url = 'https://api.openalex.org/works?filter=publication_year:2026&search=inverse+source+localization+physical+fields&per_page=5&select=title,publication_year,doi,abstract_inverted_index'
try:
    resp = urllib.request.urlopen(url, timeout=10)
    data = json.loads(resp.read())
    results = data.get('results', [])
    print('--- 2026 inverse source localization papers:')
    for r in results:
        ti = r.get('title', '?')
        print('  ' + ti)
        aii = r.get('abstract_inverted_index', {})
        if aii:
            words = {}
            for word, positions in aii.items():
                for pos in positions:
                    words[pos] = word
            abstract = ' '.join(words[k] for k in sorted(words.keys()))
            print('  Abstract: ' + abstract[:300])
        print()
except Exception as e:
    print('ERROR: ' + str(e))

# Search for infotaxis variants
url2 = 'https://api.openalex.org/works?search=infotaxis+variant+binary+detection&per_page=5&select=title,publication_year'
try:
    resp = urllib.request.urlopen(url2, timeout=10)
    data = json.loads(resp.read())
    results = data.get('results', [])
    print('--- infotaxis variants:')
    for r in results:
        yr = r.get('publication_year', '?')
        ti = r.get('title', '?')
        print('  [' + str(yr) + '] ' + ti)
except Exception as e:
    print('ERROR: ' + str(e))
