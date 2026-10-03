"""Read-only authoritative metadata/code availability audit; never pairs flight axes."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json
import requests

ROOT = Path(r'C:\work\LAGOON_PINGO_REAL_DATA_20261003')
OUT = ROOT / 'unlock_20261003'
OUT.mkdir(exist_ok=True)
URLS = {
 'zenodo_record': 'https://zenodo.org/api/records/19597182',
 'zenodo_concept': 'https://zenodo.org/api/records/19597181',
 'github_repo': 'https://api.github.com/repos/johanage/lagoon-pingo-analysis',
 'github_user_repos': 'https://api.github.com/users/johanage/repos?per_page=100',
 'github_alouette_repos': 'https://api.github.com/users/AlouetteUiO/repos?per_page=100',
 'github_repo_search': 'https://api.github.com/search/repositories?q=lagoon-pingo',
 'github_user_search': 'https://api.github.com/search/users?q=johanage',
 'github_web': 'https://github.com/johanage/lagoon-pingo-analysis',
 'github_main_readme': 'https://raw.githubusercontent.com/johanage/lagoon-pingo-analysis/main/README.md',
 'github_master_readme': 'https://raw.githubusercontent.com/johanage/lagoon-pingo-analysis/master/README.md',
 'author_github_profile': 'https://github.com/johanage',
 'author_github_repositories': 'https://github.com/johanage?tab=repositories',
 'alouette_repositories': 'https://github.com/AlouetteUiO?tab=repositories',
 'inverse_days_abstracts': 'https://fips.fi/wp-content/uploads/2025/12/book_of_abstracts_inverse_days2025v2.pdf',
 'ssc_abstracts': 'https://www.forskningsradet.no/contentassets/4ad2ee6d040d49aa8d20e7227f79d1ff/book-of-abstracts-ssc-2025.pdf',
}

def fetch(item):
    name,url = item
    rec = {'id': name, 'requested_url': url, 'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        r=requests.get(url, timeout=75, headers={'User-Agent':'public-dataset-contract-audit/1.0'})
        suffix='.pdf' if 'application/pdf' in r.headers.get('Content-Type','') else '.json' if 'json' in r.headers.get('Content-Type','') else '.txt'
        dest=OUT/(name+suffix)
        dest.write_bytes(r.content)
        rec.update(status=r.status_code, final_url=r.url, content_type=r.headers.get('Content-Type'), bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest(), saved_file=dest.name)
    except Exception as exc:
        rec['error']=str(exc)
    return rec

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        receipts=list(pool.map(fetch, URLS.items()))
    (OUT/'HTTP_RECEIPTS.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2),encoding='utf-8')
    for rec in receipts:
        print(rec['id'],rec.get('status',rec.get('error')),rec.get('bytes'))
    for label in ['github_user_repos','github_alouette_repos','github_repo_search']:
        p=OUT/(label+'.json')
        if p.exists():
            d=json.loads(p.read_text(encoding='utf-8'))
            repos=d if isinstance(d,list) else d.get('items',[])
            print(label, [(x['full_name'],x.get('description')) for x in repos])
