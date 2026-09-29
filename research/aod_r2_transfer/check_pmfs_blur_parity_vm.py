#!/usr/bin/env python3
"""Read-only PMFS u/rawu operator audit; never opens GADEN targets."""
import csv
import json
import platform
from pathlib import Path

import cv2
import numpy as np


BASE = Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
BANK_ROOT = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927/legal_support_v2')


def main():
    results = []
    for env in range(3):
        inp = BASE / f'inputs/env_{env}'
        meta = json.loads((inp / 'meta.json').read_text())
        shape = (int(meta['height']), int(meta['width']))
        mask = np.fromfile(inp / 'occupancy.u8', np.uint8).reshape(shape).astype(np.float32)
        blurred_mask = cv2.GaussianBlur(mask, (0, 0), 1.5, 1.5)
        source_rows = list(csv.DictReader((inp / 'sources.csv').open()))
        max_abs = 0.0
        max_relative_to_u = 0.0
        max_mean_commutation_abs = 0.0
        bank_max_abs_rawu_mean = 0.0
        with np.load(BANK_ROOT / f'env_{env}_bank.npz', allow_pickle=False) as bank:
            bank_ids = [str(x) for x in bank['source_ids']]
            bank_rawu = bank['rawu']
        for source in range(6):
            raw_sum = np.zeros(shape, np.float64)
            u_sum = np.zeros(shape, np.float64)
            for state in range(11):
                for replica in range(1, 9):
                    prefix = BASE / f'forward/env_{env}/source_{source}/state_{state}_replica_{replica}'
                    raw = np.fromfile(str(prefix) + '.rawu.f32', '<f4').reshape(shape)
                    actual = np.fromfile(str(prefix) + '.u.f32', '<f4').reshape(shape)
                    reconstructed = cv2.GaussianBlur(raw, (0, 0), 1.5, 1.5)
                    np.divide(reconstructed, blurred_mask, out=reconstructed, where=blurred_mask != 0)
                    diff = np.abs(actual - reconstructed)
                    max_abs = max(max_abs, float(diff.max()))
                    max_relative_to_u = max(max_relative_to_u, float((diff / np.maximum(np.abs(actual), 1e-6)).max()))
                    raw_sum += raw
                    u_sum += actual
            mean_from_raw = cv2.GaussianBlur((raw_sum / 88).astype(np.float32), (0, 0), 1.5, 1.5)
            np.divide(mean_from_raw, blurred_mask, out=mean_from_raw, where=blurred_mask != 0)
            max_mean_commutation_abs = max(max_mean_commutation_abs,
                                           float(np.max(np.abs(mean_from_raw - u_sum / 88))))
            if env in (1, 2):
                sid = source_rows[source]['source_id']
                idx = bank_ids.index(sid)
                bank_max_abs_rawu_mean = max(bank_max_abs_rawu_mean,
                                              float(np.max(np.abs(bank_rawu[idx].reshape(shape) - raw_sum / 88))))
        results.append(dict(environment=env, checked_maps=6 * 11 * 8,
                            u_from_rawu_max_abs=max_abs,
                            u_from_rawu_max_rel=max_relative_to_u,
                            blur_mean_commutation_max_abs=max_mean_commutation_abs,
                            old_six_vs_full_bank_rawu_mean_max_abs=(bank_max_abs_rawu_mean if env in (1, 2) else None),
                            h01_full_bank_uses_rebuilt_legal_occupancy=(env == 0)))
    print(json.dumps(dict(scope='read-only PMFS model maps; no GADEN targets',
                          runtime=dict(python=platform.python_version(), numpy=np.__version__, opencv=cv2.__version__),
                          results=results),
                     indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
