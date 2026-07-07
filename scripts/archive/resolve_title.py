import requests, time
titles=[
 'Gas Source Localization in Unknown Indoor Environments Using Dual-Mode Information-Theoretic Search',
 'Information-Driven Gas Source Localization Exploiting Gas and Wind Local Measurements for Autonomous Mobile Robots',
 'Robotic Gas Source Localization With Probabilistic Mapping and Online Dispersion Simulation'
]
for title in titles:
    url='https://api.crossref.org/works?query.title='+requests.utils.quote(title)+'&rows=1'
    data=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0 (compatible)'}).json()
    item=data['message']['items'][0]
    doi=item['DOI']
    year=(item.get('published-print') or item.get('published-online') or {}).get('date-parts',[['']])[0][0]
    journal=item.get('container-title',[''])[0]
    t=' '.join(item.get('title',['']))
    print(f"{year} | {journal} | {doi} | {t}")
    time.sleep(1)
