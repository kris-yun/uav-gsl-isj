import requests, json, urllib.parse
q='gas source localization UAV OR mobile robot'
url='https://api.openalex.org/works?search='+requests.utils.quote(q)+'&sort=relevance_score:desc&per_page=10'
resp=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0'})
print(resp.status_code)
print(resp.text[:500])
