#!/usr/bin/env python3
"""V1 sidecar with the same causal event and timing encoder as offline VGR logs.

The C++ STEP protocol is unchanged. The PMFS measurement block and its ten raw
samples have already been flushed by the time STEP is sent. This sidecar reads
that current block only; no future event or source label is available here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import socket
import sys

import numpy as np
import torch

ROOT = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
sys.path.insert(0, str(ROOT))
from pmfs_brg.bank import TemplateBank
from pmfs_brg.features import FeatureConfig, encode
from pmfs_brg.model import load_checkpoint, log_posterior
from tools.serve import text_reply
from sample_time_contract import verify_distinct_vgr_samples


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


class V1Session:
    def __init__(self, model, metadata: dict, bank: TemplateBank,
                 blocks: Path, samples: Path, sensor_trace: Path,
                 start_xy: tuple[float, float]):
        if model.cfg.obs_dim != 6 or model.cfg.cue_dim != 6:
            raise RuntimeError('V1 checkpoint must have six observation and cue channels')
        if metadata.get('observation_contract_id') != 'VGR_FOPDT_300S_PHYSICAL_FRAME_V1':
            raise RuntimeError('checkpoint event/time contract mismatch')
        if metadata.get('bank_fingerprint') not in (None, bank.fingerprint):
            raise RuntimeError('checkpoint candidate bank mismatch')
        self.model = model.eval()
        self.metadata = metadata
        self.bank = bank
        self.blocks = blocks
        self.samples = samples
        self.sensor_trace = sensor_trace
        self.start_xy = np.asarray(start_xy, dtype=np.float64)
        self.feature_cfg = FeatureConfig(**metadata['feature_config'])
        self.temperature = float(metadata.get('temperature', 1.0))
        self.reset_run = None

    def reset(self, run_id: str, expected_bank: str, prior=None) -> dict:
        if expected_bank != self.bank.fingerprint or not run_id:
            raise ValueError('bank or run identity mismatch')
        if prior is None:
            self.prior = np.ones(len(self.bank.ids), dtype=np.float64) / len(self.bank.ids)
        else:
            self.prior = np.asarray(prior, dtype=np.float64)
            if (self.prior.shape != (len(self.bank.ids),) or
                    not np.isfinite(self.prior).all() or (self.prior <= 0).any()):
                raise ValueError('invalid fixed prior')
            self.prior /= self.prior.sum()
        self.reset_run = run_id
        self.h = self.model.initial(1, len(self.bank.ids))
        self.last_event = None
        self.last_digest = None
        self.last_response = None
        self.last_time = -math.inf
        self.previous_end = 0.0
        self.previous_xy = self.start_xy.copy()
        self.count = 0
        return {'status': 'RESET', 'bank_id': self.bank.fingerprint,
                'sources': len(self.bank.ids), 'map_cells': self.bank.n}

    def _current_window(self, cycle: int, event: dict) -> tuple[float, float, np.ndarray]:
        matching = [r for r in rows(self.blocks) if int(r['measurement_cycle_id']) == cycle]
        if len(matching) != 1:
            raise RuntimeError('STEP arrived before its measurement block was flushed')
        block = matching[0]
        sample_rows = [r for r in rows(self.samples)
                       if int(r['measurement_cycle_id']) == cycle]
        if len(sample_rows) != 10 or [int(r['sample_index']) for r in sample_rows] != list(range(10)):
            raise RuntimeError('current deployment block lacks ten raw readings')
        times = [float(r['sim_time']) for r in sample_rows]
        start, end = float(block['sim_time_start']), float(block['sim_time_end'])
        if not (start >= self.previous_end - 1e-6 and end > start and
                start <= times[0] + 1e-6 and times[-1] <= end + 1e-6 and
                end <= 300.0 + 1e-6):
            raise RuntimeError('noncausal measurement window')
        xy = np.asarray([float(block['pose_x']), float(block['pose_y'])], dtype=np.float64)
        step_xy = np.asarray([event['x'], event['y']], dtype=np.float64)
        if np.linalg.norm(xy - step_xy) > .01:
            raise RuntimeError('STEP position differs from deployed measurement block')
        ppm = float(event['concentration_ppm'])
        block_ppm = float(block['gas_value_used_by_algorithm'])
        mean = sum(float(r['measured_gas_ppm']) for r in sample_rows) / 10
        tolerance = 2e-5 + 5e-6 * max(1.0, abs(ppm))
        if abs(ppm - block_ppm) > tolerance or abs(ppm - mean) > tolerance:
            raise RuntimeError('STEP gas differs from ten-sample deployed measurement')
        verify_distinct_vgr_samples(sample_rows, rows(self.sensor_trace), start, end,
                                    (float(xy[0]), float(xy[1])))
        return start, end, xy

    @torch.inference_mode()
    def observe(self, event: dict) -> dict:
        allowed = {'run_id', 'event_id', 'time_s', 'x', 'y', 'z', 'concentration_ppm'}
        if set(event) != allowed or self.reset_run is None or event['run_id'] != self.reset_run:
            raise ValueError('event schema/run identity mismatch')
        eid = event['event_id']
        if not isinstance(eid, int) or eid < 0:
            raise ValueError('invalid event identity')
        values = [float(event[k]) for k in ('time_s', 'x', 'y', 'z', 'concentration_ppm')]
        if not all(math.isfinite(x) for x in values) or values[-1] < 0:
            raise ValueError('nonfinite or negative observation')
        digest = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()
        if eid == self.last_event:
            if digest != self.last_digest:
                raise ValueError('same event ID changed contents')
            return self.last_response
        if (self.last_event is not None and eid <= self.last_event) or values[0] <= self.last_time:
            raise ValueError('reordered event')
        if self.count >= 128 or abs(values[3] - float(self.bank.meta['height_m'])) > 1e-4:
            raise ValueError('history/height contract violated')
        start, end, xy = self._current_window(eid + 1, event)
        dt = end - self.previous_end
        duration = end - start
        displacement = float(np.linalg.norm(xy - self.previous_xy))
        if min(dt, duration) <= 0:
            raise RuntimeError('invalid event timing')
        timing = np.log1p([dt, duration, displacement / .30]) / 8.
        footprint = (float(self.bank.meta.get('footprint_x_m', .2)),
                     float(self.bank.meta.get('footprint_y_m', .2)))
        p, u = self.bank.project([xy], footprint)
        obs3, cues = encode([values[4]], [xy], self.bank.xy, p, u, self.feature_cfg)
        obs = np.concatenate((obs3, np.asarray(timing, dtype=np.float32).reshape(1, 3)), axis=1)
        logits, h = self.model.step(torch.from_numpy(obs), torch.from_numpy(cues), self.h)
        lp = log_posterior(logits.double(), self.prior, self.temperature)[0]
        q = lp.exp().cpu().numpy()
        if not np.isfinite(q).all() or abs(q.sum() - 1) > 1e-8:
            raise RuntimeError('invalid candidate posterior')
        src, var = self.bank.planner_maps(q)
        self.h = h
        self.count += 1
        self.last_event, self.last_digest, self.last_time = eid, digest, values[0]
        self.previous_end, self.previous_xy = end, xy
        response = {'status': 'OK', 'run_id': self.reset_run, 'event_id': eid,
                    'bank_id': self.bank.fingerprint, 'q': q.tolist(),
                    'log_q': lp.cpu().numpy().tolist(), 'source_map': src.tolist(),
                    'variance_of_hit_prob': var.tolist(), 'observations': self.count,
                    'history_extrapolated': self.count > int(self.metadata.get('max_tested_history', 10))}
        self.last_response = response
        return response


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--bank', required=True)
    ap.add_argument('--measurement-blocks', required=True)
    ap.add_argument('--measurement-samples', required=True)
    ap.add_argument('--sensor-trace', required=True)
    ap.add_argument('--start-x', type=float, required=True)
    ap.add_argument('--start-y', type=float, required=True)
    ap.add_argument('--tcp-port', type=int, required=True)
    ap.add_argument('--threads', type=int, default=1)
    ap.add_argument('--log', required=True)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    model, meta = load_checkpoint(args.checkpoint)
    bank = TemplateBank.load(args.bank)
    session = V1Session(model, meta, bank, Path(args.measurement_blocks),
                        Path(args.measurement_samples), Path(args.sensor_trace),
                        (args.start_x, args.start_y))
    with open(args.log, 'a', buffering=1) as log, socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', args.tcp_port))
        server.listen(1)
        while True:
            conn, _ = server.accept()
            with conn:
                conn.settimeout(30)
                with conn.makefile('r', encoding='ascii') as stream:
                    while True:
                        line = stream.readline(4097)
                        if not line:
                            break
                        try:
                            if len(line) > 4096 or not line.endswith('\n'):
                                raise ValueError('oversized or incomplete request')
                            answer = text_reply(line, session)
                            status = answer.split()[0]
                        except Exception as exc:
                            status = 'ERROR'
                            answer = 'ERROR ' + str(exc).replace('\n', ' ') + '\n'
                        log.write(json.dumps({'text': line.strip(), 'status': status}) + '\n')
                        conn.sendall(answer.encode('ascii'))


if __name__ == '__main__':
    main()
