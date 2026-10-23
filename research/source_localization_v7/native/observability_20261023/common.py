from pathlib import Path
import csv,hashlib,json,sys
import numpy as np

PROJECT=Path(__file__).resolve().parents[2]
NATIVE=PROJECT/'native'
sys.path.insert(0,str(NATIVE))
sys.path.insert(0,str(PROJECT/'src'))
from recover_assets import run_path,OCC
from extract_existing_worlds import points_for_probes
from gaden_executor.reader import NativeQuery,decode_frame

OUT=PROJECT/'results/source_pair_observability_20261023'
PROTOCOL=Path(__file__).with_name('PROTOCOL.json')
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def write(name,d):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def csvout(name,rows):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def probes():
    with (PROJECT/'evidence/discovery/ocb_r2/metadata/E1_HOUSE_PROBE_CONTRACTS.tsv').open(newline='') as f:
        return sorted([r for r in csv.DictReader(f,delimiter='\t') if r['house']=='House01'],key=lambda r:int(r['probe_rank']))
def dataset():
    receipt=json.loads((OUT/'TRAIN_EXTRACTION_RECEIPT.json').read_text())
    arrays=[]
    for r in receipt['worlds']:
        with np.load(OUT/r['file'],allow_pickle=False) as z:arrays.append(z['values_ppm'])
    with np.load(OUT/receipt['worlds'][0]['file'],allow_pickle=False) as z:times=z['times_s']
    return np.array(arrays).reshape(2,2,len(times),30),times,receipt
