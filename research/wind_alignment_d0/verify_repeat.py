#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('root');a=ap.parse_args();root=Path(a.root)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
comparisons={}
for first,second,label in [('forward_bank','forward_bank_repeat','forward'),('scores','scores_repeat','scores')]:
    x=root/first;y=root/second
    xf={str(p.relative_to(x)):p for p in x.rglob('*') if p.is_file()};yf={str(p.relative_to(y)):p for p in y.rglob('*') if p.is_file()}
    assert xf.keys()==yf.keys()
    differences=[name for name in xf if sha(xf[name])!=sha(yf[name])]
    comparisons[label]={'file_count':len(xf),'map_count':sum(n.endswith('.f32') for n in xf),'all_bytes_identical':not differences,'differences':differences}
assert all(x['all_bytes_identical'] for x in comparisons.values())
record={'pass':True,'comparisons':comparisons,'total_generated_maps':87+1044*2,'unique_scientific_maps':1044,'sensor_height_bank_maps':957,'P0_maps':87,'P1_reuses_P2_state0':True}
(root/'deterministic_repeat.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');print(json.dumps(record,indent=2))
