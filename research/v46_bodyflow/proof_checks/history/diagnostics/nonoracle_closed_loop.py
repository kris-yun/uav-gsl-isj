#!/usr/bin/env python3
"""One preregistered-resolution diagnostic; not a model superiority benchmark.

All three methods share geomspace(0.5,4,65), chosen by quadrature refinement
on the frozen historical prefix. The unknown generating q is never inserted.
"""
from pathlib import Path
import json,numpy as np
from audit_v43 import diagnostic_run
out=[]
for mode in ['bio','bio_noidentity','ordinary_projected_full']:
    r=diagnostic_run(mode,tuple(np.geomspace(.5,4.,65)),steps=20)
    out.append(r)
    print({k:v for k,v in r.items() if k not in ('records','q_values')},flush=True)
(Path(__file__).resolve().parents[1]/'results'/'nonoracle_closed_loop_results.json').write_text(json.dumps({'scope':'Development diagnosis, same-model one source/seed; no S2/native claim and no evidence of BIO superiority.','runs':out},indent=2))
