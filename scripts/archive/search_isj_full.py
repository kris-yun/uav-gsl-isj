import requests
issn='1530-437X'
queries=['gas leak source localization deep learning','odor source localization reinforcement learning','gas source localization UAV','gas plume localization','bio-inspired odor source localization','olfaction threshold odor source search']
for q in queries:
    url='https://api.crossref.org/works?query='+requests.utils.quote(q)+'&filter=issn:'+issn+'&rows=5&sort=relevance&order=desc'
    data=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0 (compatible)'}).json()
    print('QUERY:', q)
    for item in data.get('message',{}).get('items',[])[:5]:
        title=' '.join(item.get('title',['']))
        doi=item.get('DOI')
        year=(item.get('published-print') or item.get('published-online') or {}).get('date-parts',[['']])[0][0]
        print(f"  {year} | {doi} | {title}")
