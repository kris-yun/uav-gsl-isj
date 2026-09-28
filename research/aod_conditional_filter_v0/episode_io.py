"""Read frozen VGR episodes and align event samples to sensor publications."""
from __future__ import annotations

import csv
import io
import json
import subprocess
import tarfile
from functools import lru_cache
from pathlib import Path

import numpy as np


def csv_rows(blob: bytes):
    return list(csv.DictReader(io.StringIO(blob.decode())))


def read_archive(path: Path, zstd: str):
    proc = subprocess.run([zstd, '-dc', str(path)], capture_output=True, check=True)
    wanted = ('sim_pose_trace.csv', 'sensor_trace.csv', 'measurement_blocks.csv',
              'measurement_samples.csv')
    found = {}
    with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode='r:') as tar:
        for member in tar:
            for suffix in wanted:
                if member.name.endswith('_raw/' + suffix):
                    found[suffix] = csv_rows(tar.extractfile(member).read())
                    break
    if set(found) != set(wanted):
        raise RuntimeError(f'incomplete archive: {path}')
    return found


def align_publications(samples, sensor_rows, start: float, end: float, xy):
    """Source-blind matching of callback values to distinct VGR publications.

    The published sensor values disambiguate a possible one-tick /clock lag;
    no concentration prediction, source identity, or future publication enters.
    """
    if len(samples) != 10:
        raise ValueError('expected ten measurement samples')
    nearby = [i for i, row in enumerate(sensor_rows)
              if start - .6 <= float(row['t_sim_s']) <= end + .6 and
              np.hypot(float(row['x'])-xy[0], float(row['y'])-xy[1]) <= .02]
    if len(nearby) < 10:
        raise RuntimeError('fewer than ten nearby VGR publications')
    @lru_cache(None)
    def solve(k, begin):
        if k == 10:
            return (0., ())
        best = None
        value = float(samples[k]['measured_gas_ppm'])
        callback_t = float(samples[k]['sim_time'])
        for j in range(begin, len(nearby) - (10-k) + 1):
            row = sensor_rows[nearby[j]]
            sensor_t = float(row['t_sim_s'])
            tol = 2e-5 + 5e-6 * max(1., abs(value))
            if abs(float(row['measured_gas_ppm'])-value) > tol or abs(sensor_t-callback_t) > .6:
                continue
            tail = solve(k+1, j+1)
            if tail is None:
                continue
            candidate = (abs(sensor_t-callback_t)+tail[0], (nearby[j],)+tail[1])
            if best is None or candidate < best:
                best = candidate
        return best
    match = solve(0, 0)
    if match is None:
        raise RuntimeError('measurement samples not found in ordered VGR trace')
    return np.array(match[1], dtype=int)


def episode_events(data):
    sensor = data['sensor_trace.csv']
    blocks = data['measurement_blocks.csv']
    samples = data['measurement_samples.csv']
    by_cycle = {}
    for row in samples:
        by_cycle.setdefault(int(row['measurement_cycle_id']), []).append(row)
    out = []
    for b in blocks:
        cycle = int(b['measurement_cycle_id'])
        ss = sorted(by_cycle[cycle], key=lambda r: int(r['sample_index']))
        xy = (float(b['pose_x']), float(b['pose_y']))
        ids = align_publications(ss, sensor, float(b['sim_time_start']),
                                 float(b['sim_time_end']), xy)
        y = float(b['gas_value_used_by_algorithm'])
        if abs(y - np.mean([float(s['measured_gas_ppm']) for s in ss])) > 2e-5+5e-6*max(1.,abs(y)):
            raise RuntimeError('measurement block/sample mismatch')
        out.append((float(b['sim_time_end']), y, ids))
    if not all(out[i][0] < out[i+1][0] for i in range(len(out)-1)):
        raise RuntimeError('event time not increasing')
    return out


def predict_sensor(bank, sensor_rows, last_index=None):
    """Candidate rawu through the verified 0.2 s, tau=1.2 s, delay=0.4 s FOPDT."""
    limit = len(sensor_rows) if last_index is None else last_index+1
    xy = np.array([(float(r['x']),float(r['y'])) for r in sensor_rows[:limit]])
    _, raw = bank.project(xy, (.2,.2))
    a = np.exp(-.2/1.2)
    state = np.zeros(len(bank.ids))
    result = np.empty_like(raw)
    for k in range(len(raw)):
        state = a*state + (1-a)*(raw[k-2] if k>=2 else 0.)
        result[k] = state
    return result


def predicted_event_means(bank, data):
    events = episode_events(data)
    if not events:
        raise RuntimeError('no deployed events')
    response = predict_sensor(bank, data['sensor_trace.csv'],
                              max(int(i) for _,_,ids in events for i in ids))
    return [(t, y, response[ids].mean(axis=0)) for t,y,ids in events]
