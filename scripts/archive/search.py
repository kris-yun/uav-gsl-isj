import requests, urllib.parse, re, itertools
q='"IEEE Sensors Journal" gas source localization Bayesian search site:ieeexplore.ieee.org'
url='https://html.duckduckgo.com/html/?q='+urllib.parse.quote(q)
html=requests.get(url,timeout=20,headers={'User-Agent':'Mozilla/5.0'}).text
for m in itertools.islice(re.finditer(r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>', html), 10):
    href,title=m.group(1),m.group(2)
    print(title)
    print(href)
    print('---')
