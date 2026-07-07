import requests, json
issn='1552-3098'
q='gas source localization'
url='https://api.crossref.org/works?query='+requests.utils.quote(q)+'&filter=issn:'+issn+'&rows=10&sort=relevance&order=desc'
data=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0 (compatible)'}).json()
for item in data.get('message',{}).get('items',[])[:10]:
    title=' '.join(item.get('title',['']))
    doi=item.get('DOI')
    year=(item.get('published-print') or item.get('published-online') or {}).get('date-parts',[['']])[0][0]
    print(f"{year} | {doi} | {title}")
