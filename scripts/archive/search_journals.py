import requests, json, urllib.parse
journals=[
 ('IEEE Transactions on Robotics', '1552-3098'),
 ('IEEE Robotics and Automation Letters', '2377-3766'),
 ('IEEE Transactions on Automation Science and Engineering', '1545-5955'),
 ('Robotics and Autonomous Systems', '0921-8890'),
 ('Sensors', '1424-8220')
]
queries=['gas source localization','odor source localization','plume source localization','source seeking','infotaxis']
for journal,issn in journals:
    print('\n##',journal)
    seen=set()
    for q in queries:
        url='https://api.crossref.org/works?query='+requests.utils.quote(q)+'&filter=issn:'+issn+'&rows=5&sort=relevance&order=desc'
        data=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0 (compatible)'}).json()
        for item in data.get('message',{}).get('items',[])[:5]:
            doi=item.get('DOI')
            if doi in seen: continue
            seen.add(doi)
            title=' '.join(item.get('title',['']))
            year=(item.get('published-print') or item.get('published-online') or {}).get('date-parts',[['']])[0][0]
            print(f"{year} | {doi} | {title}")
