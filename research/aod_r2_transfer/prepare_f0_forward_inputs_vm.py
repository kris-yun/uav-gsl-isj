#!/usr/bin/env python3
"""Freeze a 2D PMFS input from OCB-R2's hashed canonical 3D winds.

Metadata/model inputs only; no concentration or native filament records.
"""
import csv
import hashlib
import json
import shutil
import struct
from pathlib import Path

import numpy as np


ROOT = Path('/home/zyc/aod_r2_f0')
TOOLS = ROOT / 'tools'
INPUTS = ROOT / 'inputs'
S2 = json.loads((TOOLS / 'S1_STATIC_ASSET_AUDIT.json').read_text())[:8]
LEGAL = json.loads((TOOLS / 'LEGAL_SUPPORT_COMPLETE.json').read_text())
ENVS = json.loads((TOOLS / 'environment_manifest.json').read_text())
FREEZE = json.loads((TOOLS / 'AOD_R2_F0_PRE_TARGET_FREEZE.json').read_text())
BIN = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927/full_support/full_support_forward')
MASK_ROOT = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927/legal_support_v2')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def env3d(path):
    with Path(path).open() as f:
        header = [next(f).strip() for _ in range(4)]
    minimum = [float(x) for x in header[0].split()[1:]]
    dims = [int(x) for x in header[2].split()[1:]]
    spacing = float(header[3].split()[1])
    assert len(minimum) == len(dims) == 3 and spacing == .1
    return minimum, dims, spacing


def main():
    assert FREEZE['decision'] == 'AOD_R2_F0_METADATA_FROZEN_NO_TARGET_READ'
    runlist = TOOLS / 'AOD_R2_F0_FORWARD_RUNLIST.tsv'
    assert sha(runlist) == FREEZE['output_sha256'][runlist.name]
    with runlist.open(newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    assert len(rows) == FREEZE['pmfs_forward_rows'] == 3168
    assert set(r['context'] for r in rows) == {f'X{i:02d}' for i in range(8)}
    assert BIN.is_file()
    INPUTS.mkdir(parents=True, exist_ok=False)
    inventory = {}
    raw_wind_sha = {}
    binary_sha = sha(BIN)
    for context in range(8):
        spec = S2[context]
        house = spec['house']
        hi = 0 if house == 'House01' else 1
        bank = LEGAL['banks'][hi]
        meta = ENVS[hi]['metadata']
        n = int(meta['width']) * int(meta['height'])
        legal_ids = bank['source_ids']
        assert len(legal_ids) == bank['candidates'] == (596 if hi == 0 else 630)
        context_rows = [r for r in rows if r['context'] == f'X{context:02d}']
        chosen = {(r['source_id'], int(r['full_legal_index'])) for r in context_rows}
        assert len(context_rows) == len(chosen) * 88
        assert all(legal_ids[index] == sid for sid, index in chosen)
        assert all(r['wind'] == spec['wind_id'] and r['house'] == house for r in context_rows)
        folder = INPUTS / f'X{context:02d}'
        folder.mkdir()
        (folder / 'meta.json').write_text(json.dumps(meta, indent=2, sort_keys=True)+'\n')
        with (folder / 'meta.csv').open('w', newline='') as f:
            w = csv.writer(f); w.writerow(meta); w.writerow(meta.values())
        maskpath = MASK_ROOT / f'env_{hi}_occupancy.u8'
        mask = np.fromfile(maskpath, np.uint8)
        assert mask.size == n and set(np.unique(mask)).issubset({0, 1})
        legal_cells = np.flatnonzero(mask == 1)
        assert len(legal_cells) == len(legal_ids)
        derived = [f'pmfs_{int(c)%meta["width"]}_{int(c)//meta["width"]}' for c in legal_cells]
        assert derived == legal_ids
        shutil.copyfile(maskpath, folder / 'occupancy.u8')
        x = float(meta['origin_x']) + (legal_cells % meta['width'] + .5) * float(meta['resolution'])
        y = float(meta['origin_y']) + (legal_cells // meta['width'] + .5) * float(meta['resolution'])
        with (folder / 'sources.csv').open('w', newline='') as f:
            w = csv.writer(f); w.writerow(['source_index', 'source_id', 'x', 'y', 'z', 'pair_id'])
            for idx, (sid, xx, yy) in enumerate(zip(legal_ids, x, y)):
                w.writerow([idx, sid, repr(float(xx)), repr(float(yy)), '.2', ''])
        minimum, dims, spacing = env3d(spec['occupancy_path'])
        assert np.prod(dims) == spec['wind_cells_per_state']
        xyz = np.column_stack((x, y, np.full(x.shape, .2)))
        ijk = np.trunc((xyz - minimum) / spacing).astype(np.int64)
        assert np.all(ijk >= 0) and np.all(ijk < np.asarray(dims))
        wind_offset = ijk[:, 0] + ijk[:, 1]*dims[0] + ijk[:, 2]*dims[0]*dims[1]
        asset_rows = {(int(a['state']), a['axis']): a for a in spec['wind_files']}
        for state in range(11):
            uv = []
            for axis in 'UV':
                p = Path(f"{spec['wind_prefix']}_{state}.csv_{axis}")
                expected = asset_rows[state, axis]['sha256']
                assert sha(p) == expected
                b = p.read_bytes()
                assert len(b) == 4 + 8*int(np.prod(dims)) and struct.unpack_from('<I', b)[0] == 999
                values = np.frombuffer(b, '<f8', offset=4)
                picked = values[wind_offset]
                assert np.isfinite(picked).all()
                uv.append(picked)
                raw_wind_sha[f'X{context:02d}/{state}/{axis}'] = expected
            with (folder / f'wind_{state}.csv').open('w', newline='') as f:
                w = csv.writer(f); w.writerow(['cell_index', 'u', 'v'])
                for cell, u, v in zip(legal_cells, *uv):
                    w.writerow([int(cell), repr(float(np.float32(u))), repr(float(np.float32(v)))])
        inventory[f'X{context:02d}'] = dict(house=house, wind=spec['wind_id'], gas=context_rows[0]['gas'],
                                           canonical_wind_bundle_sha256=spec['wind_bundle_sha256'],
                                           source_count=len(legal_ids), selected_candidate_count=len(chosen),
                                           selected_candidates=sorted(sid for sid, _ in chosen),
                                           pmfs_forward_rows=len(context_rows), occupancy_mask_sha256=sha(maskpath),
                                           native_3d_occupancy_sha256=spec['occupancy_sha256'],
                                           z_m=.2, wind_index_rule='trunc((xyz-origin)/0.1), x-fastest then y then z',
                                           files={p.name: sha(p) for p in sorted(folder.iterdir()) if p.is_file()})
    result = dict(decision='AOD_R2_F0_FORWARD_INPUTS_FROZEN', model_binary_sha256=binary_sha,
                  runlist_sha256=sha(runlist), metadata_freeze_sha256=sha(TOOLS / 'AOD_R2_F0_PRE_TARGET_FREEZE.json'),
                  builder_sha256=sha(__file__), full_legal_order=True, paired_u_rawu=True,
                  selected_forward_rows=sum(v['pmfs_forward_rows'] for v in inventory.values()),
                  contexts=inventory, canonical_axis_sha256=raw_wind_sha,
                  target_concentration_read=False, new_gaden=0)
    out = ROOT / 'AOD_R2_F0_PRE_FORWARD_INPUTS.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(decision=result['decision'], rows=result['selected_forward_rows'],
                          sha256=sha(out)), sort_keys=True))


if __name__ == '__main__':
    main()
