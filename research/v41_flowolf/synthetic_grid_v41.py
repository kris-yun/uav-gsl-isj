#!/usr/bin/env python3
"""Fixed software-development matrix; no native S2 or blind-world claim."""
from pathlib import Path
from collections import defaultdict
import json,numpy as np
from demo_v41 import run

SOURCES=((-6.,-3.,10.),(0.,0.,10.),(6.,3.,10.))
SEEDS=(42,9001)
MODES=('bio','ordinary_eig_full','ordinary_projected_full',
       'bio_noidentity','bio_nogap')

def main():
    records=[]
    for s in SOURCES:
        for seed in SEEDS:
            for m in MODES:
                r=run(mode=m,source=s,seed=seed,steps=16,save_trace=False)
                records.append({'source':list(s),'seed':seed,'mode':m,
                    'error_m':r['map_error_m_eval_only'], 'contacts':r['contacts'],
                    'cpu_s':r['elapsed_s'],'pathlen_m':sum(r['distance_per_uav_m'])})
    stats={m:{'mean_error_m':float(np.mean([r['error_m'] for r in records if r['mode']==m])),
              'median_error_m':float(np.median([r['error_m'] for r in records if r['mode']==m]))}
              for m in MODES}
    out={'scope':'six same-model synthetic development conditions; NOT native S2',
         'sources':SOURCES,'seeds':SEEDS,'steps':16,
         'modes':MODES,'summary':stats,'cases':records}
    Path('V41_SYNTHETIC_6_CASES.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    for m,s in stats.items():print(m,'mean',round(s['mean_error_m'],3),
                                     'median',round(s['median_error_m'],3))
    print('NO BIO MAIN INNOVATION CERTIFICATE: BIO-noidentity may be better')

if __name__=='__main__':main()