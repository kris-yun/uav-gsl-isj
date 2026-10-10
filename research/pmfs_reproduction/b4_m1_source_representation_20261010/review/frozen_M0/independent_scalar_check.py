"""Independent read-only scalar/Decimal score check. No import of verify_m0."""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import json
import math
import struct
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 45
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--evidence', type=Path, default=Path(__file__).resolve().parent / 'evidence')
args = parser.parse_args()
count = 0
maxrel = Decimal(0)
last = None
for update in sorted((args.evidence / 'runtime/updates').glob('update_*')):
    with (update / 'input.csv').open(encoding='utf-8', newline='') as handle:
        cells = list(csv.DictReader(handle))
    with (update / 'candidates.csv').open(encoding='utf-8', newline='') as handle:
        candidates = list(csv.DictReader(handle))
    calculated = {}
    for candidate in candidates:
        blob = (update / candidate['map_file']).read_bytes()
        hits = struct.unpack('<' + 'f' * (len(blob) // 4), blob)
        score = Decimal(1)
        logs = []
        for cell, simulated in zip(cells, hits):
            if cell['occupancy'] != '1':
                logs.append(0.)
                continue
            measured = 1 - 1 / (1 + math.exp(float(cell['logOdds'])))
            confidence = float(cell['confidence'])
            factor = 1 + ((1 - abs(measured - simulated) * .4) - 1) * min(max(confidence, 0.), 1.)
            assert factor > 0
            score *= Decimal.from_float(factor)
            logs.append(math.log(factor))
        rel = abs(score / Decimal(candidate['score']) - 1)
        maxrel = max(maxrel, rel)
        assert rel < Decimal('5e-12')
        count += 1
        calculated[candidate['candidate_id']] = dict(score=score, logs=logs)
    if update.name == 'update_2':
        true = calculated['quadtree_17_18_5_1']
        wrong = calculated['quadtree_23_37_1_1']
        difference = [w - t for w, t in zip(wrong['logs'], true['logs'])]
        total = math.fsum(difference)
        band = math.fsum(d for k, d in enumerate(difference) if 1.7 <= -7.88 + (k // 34 + .5) * .25 <= 2.7)
        last = dict(final_ratio=float(wrong['score'] / true['score']),
                    final_total_log_ratio=total, band_net_log_ratio=band, band_net_fraction=band / total)
assert count == 388
assert abs(last['final_ratio'] - 14874.5986951951) < 1e-7
print(json.dumps(dict(verdict='PASS_INDEPENDENT_SCALAR_DECIMAL_CHECK', candidate_scores=count,
                     maximum_relative_score_error=float(maxrel), precision_decimal_digits=45,
                     final=last, new_simulations=0, writes=False), indent=2))
