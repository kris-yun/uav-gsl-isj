#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
from completeness_gate import GateConfig, compute_gate


def opt(d, k, n, default):
    if k in d:
        x = np.asarray(d[k])
        if len(x) != n:
            raise ValueError(f"{k} length mismatch")
        return x
    return np.asarray([default] * n)


def scalar_string(d, key, default):
    if key not in d:
        return default
    x = np.asarray(d[key])
    if x.ndim == 0:
        return str(x.item())
    if x.size == 1:
        return str(x.reshape(-1)[0])
    raise ValueError(f"{key} must be scalar")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--npz', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--gamma-min', type=float, default=0.05)
    p.add_argument('--p-max', type=float, default=0.01)
    p.add_argument('--rank-k', type=int, default=3)
    p.add_argument('--ridge-rel', type=float, default=1e-3)
    p.add_argument(
        '--member-semantics',
        choices=['exchangeable_realizations', 'fixed_nuisance_design'],
        default=None,
    )
    a = p.parse_args()

    d = np.load(a.npz, allow_pickle=True)
    phi = np.asarray(d['phi'], dtype=np.float64)
    if phi.ndim != 4:
        raise ValueError(f"phi must be [N,S,M,D], got {phi.shape}")
    N = phi.shape[0]
    context = opt(d, 'context', N, '')
    split = opt(d, 'split', N, '')
    house = opt(d, 'house', N, '')
    margin = opt(d, 'margin', N, np.nan).astype(float)

    semantics = a.member_semantics or scalar_string(d, 'member_semantics', 'UNDECLARED')
    if semantics == 'UNDECLARED':
        raise ValueError(
            'member_semantics must be declared before evaluation; '
            'do not guess whether the M1 members are stochastic realizations or a fixed design'
        )

    cfg = GateConfig(
        gamma_min=a.gamma_min,
        p_max=a.p_max,
        rank_k=a.rank_k,
        ridge_rel=a.ridge_rel,
        member_semantics=semantics,
    )

    rows = []
    for i in range(N):
        g = compute_gate(phi[i], cfg)
        rows.append({
            'i': i,
            'context': context[i],
            'split': split[i],
            'house': house[i],
            **g.to_dict(),
            'margin': margin[i],
        })

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    accepted = np.asarray([r['accepted'] for r in rows], dtype=bool)
    summary = {
        'protocol': 'CG_PC_CTT_GATE_V2_REPLICATED_CROSS_MEMBER',
        'n': N,
        'coverage': float(accepted.mean()),
        'accepted': int(accepted.sum()),
        'rejected': int((~accepted).sum()),
        'gamma_min': a.gamma_min,
        'p_max': a.p_max,
        'rank_k': a.rank_k,
        'member_semantics': semantics,
        'inferential_valid': bool(all(r['inferential_valid'] for r in rows)),
        'NOTE': 'No alpha threshold calibration exists in V2.',
    }
    if np.any(np.isfinite(margin)):
        for name, mask in [('accepted', accepted), ('rejected', ~accepted)]:
            z = margin[mask & np.isfinite(margin)]
            summary[f'{name}_mean_margin'] = float(z.mean()) if len(z) else None
            summary[f'{name}_positive_margin_rate'] = float(np.mean(z > 0)) if len(z) else None
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
