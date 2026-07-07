import requests, json
queries=['gas source localization UAV','odor source localization mobile robot Bayesian','gas source localization mobile robot','chemical plume source localization UAV','plume source localization Bayesian search mobile robot']
for query in queries:
    url='https://api.crossref.org/works?query='+requests.utils.quote(query)+'&rows=10&sort=relevance&order=desc'
    data=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0 (compatible)'}).json()
    print('QUERY:', query)
    for item in data.get('message',{}).get('items',[])[:10]:
        title=' '.join(item.get('title',['']))
        doi=item.get('DOI')
        year=(item.get('published-print') or item.get('published-online') or {}).get('date-parts',[['']])[0][0]
        journal=item.get('container-title',[''])[0]
        print(f"  {year} | {journal} | {doi} | {title}")
