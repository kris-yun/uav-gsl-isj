"""Download publisher sensor products to isolated directory and inspect headers only."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json
import requests, h5py

ROOT=Path(r'C:\work\LAGOON_PINGO_REAL_DATA_20261003\unlock_20261003')
RAW=ROOT/'raw_sensor_contract_inputs'
RAW.mkdir(exist_ok=True)
NAMES=['svalbard_aeris_all_flights.nc','svalbard_trisonica_corrected_split_flights.nc','svalbard_flightrecords.nc']

def download(f):
    p=RAW/f['key']; url=f['links']['self']
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not p.exists():
        with requests.get(url,stream=True,timeout=120) as r:
            r.raise_for_status()
            with p.with_suffix('.partial').open('wb') as o:
                for chunk in r.iter_content(1<<20): o.write(chunk)
        p.with_suffix('.partial').replace(p)
    md5=hashlib.md5(); sha=hashlib.sha256()
    with p.open('rb') as s:
        while block:=s.read(1<<20): md5.update(block);sha.update(block)
    receipt={'name':p.name,'bytes':p.stat().st_size,'md5':md5.hexdigest(),'sha256':sha.hexdigest(),'publisher_checksum':f['checksum'],'source_url':url,'retrieved_utc':start}
    assert f['checksum']=='md5:'+md5.hexdigest()
    assert p.stat().st_size==f['size']
    def serial(v):
        if isinstance(v,bytes): return v.decode('utf-8','replace')
        if hasattr(v,'tolist'): return serial(v.tolist())
        if isinstance(v,list): return [serial(x)for x in v]
        return str(v) if isinstance(v,h5py.Reference) else v
    with h5py.File(p,'r') as ds:
        schema={'dimensions':{k:v.shape[0] for k,v in ds.items() if isinstance(v,h5py.Dataset) and v.attrs.get('CLASS')==b'DIMENSION_SCALE'},'attrs':{k:serial(v)for k,v in ds.attrs.items()},'variables':{k:{'shape':list(v.shape),'dtype':str(v.dtype),'attrs':{a:serial(b)for a,b in v.attrs.items()if a not in ['DIMENSION_LIST','REFERENCE_LIST']}}for k,v in ds.items()if isinstance(v,h5py.Dataset)}}
    (ROOT/(p.name+'.schema.json')).write_text(json.dumps(schema,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(p.name,receipt['bytes'],schema['dimensions'],schema['attrs'],flush=True)
    return receipt

if __name__=='__main__':
    rec=json.loads((ROOT/'zenodo_record.json').read_text(encoding='utf-8'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        receipts=list(pool.map(download,[f for f in rec['files']if f['key']in NAMES]))
    (ROOT/'SENSOR_DOWNLOAD_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
