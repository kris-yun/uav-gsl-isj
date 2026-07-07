import urllib.request, time

searches = [
    'PCA principal component analysis gas source localization UAV',
    'Peclet number gas plume kernel adaptive estimation',
    'compressed sensing gas source localization sparse',
    'cluster shape odor plume source direction estimation',
    'hit probability gradient direction source estimation',
]

for q in searches:
    url = 'https://scholar.google.com/scholar?q=' + q.replace(' ', '+') + '&as_ylo=2020'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode('utf-8', errors='ignore')
        has_results = 'gs_ri' in html or 'gs_or' in html
        has_no = 'did not match' in html
        print(f'Query: {q}')
        if has_no:
            print('  -> NO RESULTS = GENUINELY NOVEL')
        elif has_results:
            print('  -> Has results - need to check if related')
        else:
            print('  -> Unclear (might be blocked)')
    except Exception as e:
        print(f'Query: {q}')
        print(f'  -> Error: {e}')
    time.sleep(2)
