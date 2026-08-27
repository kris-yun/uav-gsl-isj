#!/usr/bin/env python3
"""Qualify feature-space geometry needed to materialize the V3 observation operator H_e.

Frozen V2 can operate on anonymous feature columns; V3 cannot. Every field
feature used as a spatial query cell must carry an explicit coordinate and/or
native cell index so actual robot observations can select exactly the matching
forward-model support without source truth or nearest-neighbour guesswork.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('npz',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    d=np.load(a.npz,allow_pickle=False); errors=[]; warnings=[]
    if 'phi' not in d: errors.append('MISSING_PHI'); D=None
    else:
        phi=np.asarray(d['phi']); D=phi.shape[-1] if phi.ndim in (3,4) else None
        if D is None: errors.append(f'BAD_PHI_SHAPE:{phi.shape}')
    qxy=None; qcell=None
    if D is not None:
        if 'query_xy' in d:
            qxy=np.asarray(d['query_xy'],float)
            if qxy.shape!=(D,2) or not np.all(np.isfinite(qxy)): errors.append(f'BAD_QUERY_XY:{qxy.shape}')
        else: warnings.append('MISSING_QUERY_XY')
        if 'query_cell_index' in d:
            qcell=np.asarray(d['query_cell_index']).reshape(-1)
            if len(qcell)!=D or not np.issubdtype(qcell.dtype,np.integer): errors.append('BAD_QUERY_CELL_INDEX')
            elif len(np.unique(qcell))!=D: errors.append('DUPLICATE_QUERY_CELL_INDEX')
        else: warnings.append('MISSING_QUERY_CELL_INDEX')
        if qxy is None and qcell is None: errors.append('NO_FEATURE_GEOMETRY_FOR_H_E')
    report={'contract':'CG_PC_CTT_V3_OBSERVATION_SUPPORT_METADATA_V1','path':str(a.npz.resolve()),
            'feature_dim':D,'has_query_xy':qxy is not None,'has_query_cell_index':qcell is not None,
            'pass':not errors,'errors':errors,'warnings':warnings,
            'binding_note':('At runtime prefer exact native/reduced-grid cell registration. query_xy is required for '
                            'offline geometry stress; nearest-coordinate matching must use a frozen tolerance and is '
                            'not a substitute for cell-index provenance.')}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
    raise SystemExit(0 if not errors else 2)

if __name__=='__main__': main()
