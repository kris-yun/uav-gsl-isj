import requests, time
dois=[
 '10.1109/jsen.2024.3407982',
 '10.1109/jsen.2022.3202134',
 '10.1109/jsen.2002.807772',
 '10.1109/lra.2025.3511375'
]
for doi in dois:
    url='https://api.crossref.org/works/'+doi
    try:
        resp=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0 (compatible)'})
        data=resp.json().get('message',{})
        title=' '.join(data.get('title',['']))
        year=(data.get('published-print') or data.get('published-online') or {}).get('date-parts',[['']])[0][0]
        journal=data.get('container-title',[''])[0]
        print(f"{year} | {journal} | {doi} | {title}")
    except Exception as e:
        print(f"ERROR | {doi} | {e}")
    time.sleep(1)
