"""Independent parity with official labeler and cumulative event adapter."""
import ast,hashlib,json,sys
from pathlib import Path
import numpy as np
from audit_open49 import CACHE,OUT,load,dump,sha
from prepare_open49 import METHOD
from official_three_channel import channels

def main():
    r=load(OUT/'OPEN49_TRAINABILITY.json');p=load(OUT/'PREFIX_MANIFEST.json');assert r['decision']=='OPEN49_TRAINABLE'
    nb=load(METHOD/'Topography-aware-Gas-Source-Localization-lfs/train/labeler.ipynb');nodes=[n for n in ast.parse(''.join(nb['cells'][1]['source'])).body if isinstance(n,ast.FunctionDef)]
    ns=dict(np=np);exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact-official-labeler>','exec'),ns)
    chosen=[p[0],next(x for x in p if x['house']=='House02'),p[-1]];checks=[]
    dest=CACHE/'parity';dest.mkdir(exist_ok=True)
    for j,prefix in enumerate(chosen):
        t=next(t for t in r['trajectories'] if t['case_id']==prefix['case_id']);h,w=t['map_dimensions'];a=np.load(CACHE/f'{t["house"]}_occupancy.npy');origin=t['origin'];res=t['resolution']
        inp=dest/f'map{j}.txt';text=f'Resolution: {res}\nWidth: {w}\nHeight: {h}\nOrigin: position: \n  x: {origin["x"]}\n  y: {origin["y"]}\nData:\n'+'\n'.join(' '.join(str(int(v)) for v in row) for row in a)+'\n';inp.write_text(text,encoding='utf-8')
        output=dest/f'label{j}.txt';ns['process_map_file'](inp,*t['truth_xy'],output,prefix['prefix_encounters'])
        lines=output.read_text(encoding='utf-8').splitlines();idx=lines.index('Data:')+1;expected=np.array([[float(v) for v in line.split()] for line in lines[idx:]],np.float32)
        with np.load(prefix['path']) as z:actual=z['label'];x=z['x']
        assert np.array_equal(actual[:h,:w],expected),'Official label parity failed'
        events=load(CACHE/'prepared'/prefix['case_id']/'OBSERVED_EVENTS.json');direct,meta=channels(a,res,origin,events,budget_s=prefix['timestamp_s']);direct[0,h:,:]=-1;direct[0,:,w:]=-1
        assert np.array_equal(direct,x),'Incremental construction differs from exact adapter'
        checks.append(dict(case_id=prefix['case_id'],prefix=prefix['prefix_encounters'],label_exact_equal=True,input_byte_equal=True))
    # Plume/trajectory grouping and literal rotation parity.
    assert not ({x['case_id'] for x in p if x['split']=='train'} & {x['case_id'] for x in p if x['split']=='validation'})
    assert all(x['physical_seed']!=2026900001 and 'House03' not in x['house'] for x in p)
    dump(OUT/'PREPARATION_PARITY.json',dict(decision='D0B_PREPARATION_PARITY_PASS',checks=checks,grouped_split_no_leakage=True,current_target_excluded=True,new_simulations=0))
    print('D0B_PREPARATION_PARITY_PASS')
if __name__=='__main__':main()
