import urllib.request, urllib.parse, json

# Try arXiv search
url = 'http://export.arxiv.org/api/query?search_query=ti:Distill-Belief+AND+ti:Source+Localization&max_results=3'
try:
    resp = urllib.request.urlopen(url, timeout=10)
    data = resp.read().decode('utf-8')
    print('arXiv results:')
    print(data[:2000])
except Exception as e:
    print('ERROR: ' + str(e))
