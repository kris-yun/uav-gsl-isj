import requests, urllib.parse, re, itertools
query='gas source localization'
params={'newsearch':'true','queryText':query,'punumber':'7361'}
url='https://ieeexplore.ieee.org/search/searchresult.jsp?'+urllib.parse.urlencode(params)
html=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0'}).text
print(html[:1500])
