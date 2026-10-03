"""Download only two frozen primary Lagoon Pingo files into an isolated C:\\work folder."""
import hashlib,json,time,csv
from pathlib import Path
import requests
ROOT=Path(r'C:\work\LAGOON_PINGO_REAL_DATA_20261003')
NAMES=['svalbard_merged.nc','Dissolved_methane_floating_flux_chamber_ebullition.xlsx']
def digest(path,kind):
 h=hashlib.new(kind)
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 for d in ['raw','metadata','audit','derived','reports','geometry']: (ROOT/d).mkdir(parents=True,exist_ok=True)
 r=requests.get('https://zenodo.org/api/records/19597182',timeout=60);r.raise_for_status();record=r.json()
 (ROOT/'metadata/zenodo_record_19597182.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 allfiles=[{'file':f['key'],'bytes':f['size'],'official_checksum':f['checksum'],'url':f['links']['self'],'selected':f['key'] in NAMES} for f in record['files']]
 with (ROOT/'metadata/OFFICIAL_FILE_INVENTORY.csv').open('w',newline='',encoding='utf-8') as out:
  w=csv.DictWriter(out,fieldnames=allfiles[0].keys());w.writeheader();w.writerows(allfiles)
 checks=[]
 for name in NAMES:
  info=next(f for f in record['files'] if f['key']==name);target=ROOT/'raw'/name;part=target.with_suffix(target.suffix+'.part')
  if not(target.exists() and target.stat().st_size==info['size'] and digest(target,'md5')==info['checksum'].split(':')[1]):
   for attempt in range(5):
    try:
     start=part.stat().st_size if part.exists() else 0
     headers={'Range':f'bytes={start}-'} if start else {}
     with requests.get(info['links']['self'],headers=headers,stream=True,timeout=(40,180)) as resp:
      resp.raise_for_status();resume=bool(start and resp.status_code==206);received=start if resume else 0;milestone=received//(50*1024*1024)
      with part.open('ab' if resume else 'wb') as out:
       for block in resp.iter_content(1024*1024):
        if block:out.write(block);received+=len(block)
        if received//(50*1024*1024)>milestone:milestone=received//(50*1024*1024);print(f'{name}: {received/1e6:.1f}/{info["size"]/1e6:.1f} MB',flush=True)
     assert part.stat().st_size==info['size']
     assert digest(part,'md5')==info['checksum'].split(':')[1]
     part.replace(target);break
    except Exception as exc:
     print(f'Attempt {attempt+1}: {exc}',flush=True)
     if attempt==4:raise
     time.sleep(2)
  checks.append({'file':name,'bytes':target.stat().st_size,'official_md5':info['checksum'].split(':')[1],'verified_md5':digest(target,'md5'),'sha256':digest(target,'sha256'),'path':str(target)})
  print(f'{name}: downloaded and checksum verified',flush=True)
 (ROOT/'metadata/DOWNLOAD_RECEIPT.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
 (ROOT/'metadata/SHA256SUMS.txt').write_text(''.join(x['sha256']+'  raw/'+x['file']+'\n' for x in checks),encoding='utf-8')
 (ROOT/'README_zh.md').write_text('# Lagoon Pingo 独立数据目录\n\n仅本数据集使用，不与 WiscoDISCO、S2X、GADEN 或旧湖岸模拟数据混放。\n\n- raw：两个官方原始文件，保持字节不变。\n- metadata：官方记录、所有文件大小清单、下载回执、MD5/SHA256。\n- audit：schema、架次、采样、同步和质量审计。\n- derived：投影轨迹与衍生表。\n- geometry：后续独立岸线几何资料。\n- reports：结论和证据索引。\n\n官方来源：https://zenodo.org/records/19597182\n',encoding='utf-8')
 print(json.dumps({'root':str(ROOT),'total_bytes':sum(x['bytes'] for x in checks),'files':checks},indent=2),flush=True)
if __name__=='__main__':main()
