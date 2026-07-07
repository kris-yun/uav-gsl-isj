import requests, json
issn='1530-437X'
queries=['infotaxis sensor','entrotaxis','Bayesian source seeking','non-detection source localization mobile robot','binary measurement gas source localization']
for query in queries:
    url='https://api.crossref.org/works?query='+requests.utils.quote(query)+'&filter=issn:'+issn+'&rows=5&sort=relevance&order=desc'
    data=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0 (compatible)'}).json()
    print('QUERY:', query)
    for item in data.get('message',{}).get('items',[])[:5]:
        title=' '.join(item.get('title',['']))
        doi=item.get('DOI')
        year=(item.get('published-print') or item.get('published-online') or {}).get('date-parts',[['']])[0][0]
        print(f"  {year} | {doi} | {title}")
