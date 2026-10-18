#!/usr/bin/env python3
"""Structural/provenance qualification for a CG-PC-CTT M1 NPZ data product."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np

ALLOWED_SEMANTICS = {'exchangeable_realizations', 'fixed_nuisance_design'}
FORBIDDEN_RUNTIME_TOKENS = {
    'source_truth', 'truth_source', 'true_source', 'wind_id', 'route_id',
    'plume_seed', 'simulator_phase', 'future', 'oracle'
}


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def scalar_str(d, key):
    if key not in d: return None
    x=np.asarray(d[key])
    if x.size != 1: return None
    return str(x.reshape(-1)[0])


def main():
    p=argparse.ArgumentParser(); p.add_argument('npz'); p.add_argument('--json-out',default=None); a=p.parse_args()
    path=Path(a.npz)
    if not path.is_file(): raise SystemExit(f'MISSING: {path}')
    d=np.load(path,allow_pickle=True)
    errors=[]; warnings=[]
    if 'phi' not in d: errors.append('MISSING_PHI')
    else:
        phi=np.asarray(d['phi'])
        if phi.ndim!=4: errors.append(f'PHI_SHAPE_{phi.shape}_EXPECTED_N_S_M_D')
        else:
            N,S,M,D=phi.shape
            if N<1 or S<4 or M<4 or D<3: errors.append(f'PHI_DIMS_TOO_SMALL_{phi.shape}')
            if M!=8: warnings.append(f'MEMBER_COUNT_{M}_NOT_HISTORICAL_8')
            if not np.issubdtype(phi.dtype,np.number): errors.append(f'PHI_NONNUMERIC_{phi.dtype}')
            elif not np.all(np.isfinite(phi)): errors.append('PHI_NAN_OR_INF')
    semantics=scalar_str(d,'member_semantics')
    if semantics not in ALLOWED_SEMANTICS:
        errors.append('MEMBER_SEMANTICS_MISSING_OR_INVALID')
    # Metadata keys may contain evaluation truth, but any key explicitly labeled
    # runtime/input/proxy may not contain forbidden oracle concepts.
    keys=list(d.files)
    suspicious=[]
    for k in keys:
        kl=k.lower()
        if any(tok in kl for tok in FORBIDDEN_RUNTIME_TOKENS): suspicious.append(k)
    if suspicious:
        warnings.append('ORACLE_LABELED_KEYS_PRESENT_FOR_EVALUATION_ONLY:'+','.join(suspicious))
    required_meta=['context','house']
    for k in required_meta:
        if k not in d: warnings.append(f'MISSING_METADATA_{k}')
    report={
        'path':str(path.resolve()),
        'sha256':sha256(path),
        'keys':keys,
        'phi_shape':list(np.asarray(d['phi']).shape) if 'phi' in d else None,
        'phi_dtype':str(np.asarray(d['phi']).dtype) if 'phi' in d else None,
        'member_semantics':semantics,
        'structural_pass':not errors,
        'inferential_gate_allowed':(not errors and semantics=='exchangeable_realizations'),
        'errors':errors,
        'warnings':warnings,
        'binding_note':'structural_pass does not prove provenance; member generation/seeds/design must be documented in M1_BANK_PROVENANCE.json before H03/H02 evaluation.'
    }
    txt=json.dumps(report,indent=2,ensure_ascii=False); print(txt)
    if a.json_out: Path(a.json_out).write_text(txt)
    raise SystemExit(0 if not errors else 2)

if __name__=='__main__': main()
