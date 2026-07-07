import requests, time
dois=[
 '10.1109/tro.2024.3426368',
 '10.1109/lra.2021.3057290',
 '10.1109/lra.2025.3511375',
 '10.1109/lra.2025.3557675',
 '10.1109/tvt.2023.3281572',
 '10.1109/jsen.2024.3373610',
 '10.1109/jsen.2024.3443655',
 '10.1109/jsen.2002.800682',
 '10.1109/jsen.2004.839597',
 '10.1109/jsen.2018.2855056',
 '10.1109/jsen.2025.3568168'
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
