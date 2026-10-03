import requests,json,hashlib,zipfile
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
SESSION=requests.Session();SESSION.mount('https://',HTTPAdapter(max_retries=Retry(total=5,backoff_factor=1,status_forcelist=[429,500,502,503,504])))
ROOT=Path(r'C:\work\MACKENZIE_CHANNEL_SEEP2_REAL_DATA_20261003')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for n in ['raw','metadata','author_code_and_data','audit','derived','reports']: (ROOT/n).mkdir(parents=True,exist_ok=True)
 meta=ROOT/'metadata/zenodo_record_20019779.json'
 if meta.exists():record=json.loads(meta.read_text(encoding='utf8'))
 else:
  r=SESSION.get('https://zenodo.org/api/records/20019779',timeout=60);r.raise_for_status();record=r.json();meta.write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding='utf8')
 receipts=[]
 for f in record['files']:
  p=ROOT/'raw'/f['key']
  if not p.exists():
   with SESSION.get(f['links']['self'],stream=True,timeout=(40,180)) as r:
    r.raise_for_status()
    with p.with_suffix(p.suffix+'.part').open('wb') as out:
     for b in r.iter_content(1024*1024):out.write(b)
   p.with_suffix(p.suffix+'.part').replace(p)
  assert p.stat().st_size==f['size'];assert hashlib.md5(p.read_bytes()).hexdigest()==f['checksum'].split(':')[1]
  receipts.append(dict(file=f['key'],bytes=p.stat().st_size,official_md5=f['checksum'],sha256=sha(p)))
  if p.suffix=='.zip':
   with zipfile.ZipFile(p) as z:
    assert z.testzip() is None
    for name in z.namelist():
     target=(ROOT/'author_code_and_data'/name).resolve();assert target.is_relative_to((ROOT/'author_code_and_data').resolve())
    z.extractall(ROOT/'author_code_and_data')
 (ROOT/'metadata/DOWNLOAD_RECEIPT.json').write_text(json.dumps(receipts,indent=2))
 inventory=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in (ROOT/'author_code_and_data').rglob('*') if p.is_file()]
 (ROOT/'metadata/EXTRACTED_MANIFEST.json').write_text(json.dumps(inventory,indent=2))
 for name,url in [('paper.html','https://amt.copernicus.org/articles/19/3983/2026/'),('paper.xml','https://amt.copernicus.org/articles/19/3983/2026/amt-19-3983-2026.xml')]:
  r=SESSION.get(url,timeout=60);r.raise_for_status();(ROOT/'metadata'/name).write_bytes(r.content)
 print(json.dumps(receipts,indent=2));print('\n'.join(x['path'] for x in inventory))
if __name__=='__main__':main()
