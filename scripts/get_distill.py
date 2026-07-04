import urllib.request

url = 'http://export.arxiv.org/api/query?id_list=2604.26095'
try:
    resp = urllib.request.urlopen(url, timeout=10)
    data = resp.read().decode('utf-8')
    # Extract summary
    start = data.find('<summary>')
    end = data.find('</summary>')
    if start >= 0 and end >= 0:
        summary = data[start+9:end]
        print('Distill-Belief FULL Abstract:')
        print(summary)
    print()
    # Extract authors
    import re
    authors = re.findall(r'<name>(.*?)</name>', data)
    print('Authors: ' + ', '.join(authors))
except Exception as e:
    print('ERROR: ' + str(e))
