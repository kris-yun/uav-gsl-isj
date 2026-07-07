import requests, json
q='gas source localization UAV Bayesian Poisson mobile robot'
url='https://api.semanticscholar.org/graph/v1/paper/search?query='+requests.utils.quote(q)+'&limit=10&fields=title,year,venue,externalIds,url'
resp=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0'})
print(resp.status_code)
print(resp.text[:1500])
