#!/usr/bin/env python3
"""Read-only comparison of legacy six-source realizations to legal full-support means."""
import csv
import json
from pathlib import Path
import numpy as np

BASE = Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
ROOT = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
MANIFEST = json.loads((BASE / 'inputs/environment_manifest.json').read_text())
for env in range(3):
    source_rows = list(csv.DictReader((BASE/f'inputs/env_{env}/sources.csv').open()))
    with np.load(ROOT/f'legal_support_v2/env_{env}_bank.npz', allow_pickle=False) as b:
        ids = [str(x) for x in b['source_ids']]
        means = b['rawu']
    out = []
    for s, row in enumerate(source_rows):
        sid = row['source_id']
        if sid not in ids:
            out.append(dict(source=sid, in_legal_bank=False))
            continue
        files = sorted((BASE/f'forward/env_{env}/source_{s}').glob('*.rawu.f32'))
        if len(files) != 88:
            out.append(dict(source=sid, runs=len(files)))
            continue
        mean = np.mean([np.fromfile(f, dtype='<f4').astype('float64') for f in files], axis=0)
        legal = means[ids.index(sid)]
        out.append(dict(source=sid, runs=88,
                        mean_max_abs=float(np.max(np.abs(mean-legal))),
                        mean_rel_l2=float(np.linalg.norm(mean-legal)/max(np.linalg.norm(legal),1e-12))))
    print(json.dumps(dict(env=env, house=MANIFEST[env]['house'], rows=out), sort_keys=True))
