import urllib.request, urllib.parse, json

url = 'https://api.openalex.org/works?search=Distill-Belief+Closed-Loop+Inverse+Source+Localization+Characterization+Physical+Fields&per_page=1&select=title,publication_year,doi,abstract_inverted_index,authorships,concepts'
try:
    resp = urllib.request.urlopen(url, timeout=10)
    data = json.loads(resp.read())
    results = data.get('results', [])
    if results:
        r = results[0]
        print('Title: ' + str(r.get('title')))
        print('Year: ' + str(r.get('publication_year')))
        print('DOI: ' + str(r.get('doi')))
        authors = [a.get('raw_author_name','') for a in (r.get('authorships') or [])]
        print('Authors: ' + ', '.join(authors))
        concepts = [c.get('display_name','') + '(' + str(c.get('score','')) + ')' for c in (r.get('concepts') or [])[:10]]
        print('Concepts: ' + ', '.join(concepts))
        aii = r.get('abstract_inverted_index', {})
        if aii:
            words = {}
            for word, positions in aii.items():
                for pos in positions:
                    words[pos] = word
            abstract = ' '.join(words[k] for k in sorted(words.keys()))
            print('FULL Abstract:')
            print(abstract)
except Exception as e:
    print('ERROR: ' + str(e))
