"""Evaluator-only support audit; never reconstruct an unrecorded posterior.

The caller names the previously documented truth-region candidate. That label
is used only to select diagnostic records and is never an algorithm input.
Counts are deduplicated within exported update/block/cell observations; they
are not claimed to be statistically independent physical observations.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def audit(path, candidate):
    events = {}
    candidate_xy = set()
    candidates = set()
    selected_rows = 0
    nonzero_rows = 0
    with path.open(encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            candidates.add(row['candidate_id'])
            nonzero_rows += float(row['aggregate_raw_exposure']) > 0
            if row['candidate_id'] != candidate:
                continue
            selected_rows += 1
            candidate_xy.add((float(row['candidate_x']), float(row['candidate_y'])))
            key = (row['source_update_id'], row['block_id'], row['cell_index'])
            observation = (float(row['sim_time_s']), int(row['observed_hit']),
                           float(row['concentration']), float(row['threshold']))
            event = events.setdefault(key, {'observation': observation, 'members': {}})
            if event['observation'] != observation:
                raise ValueError('inconsistent observation across members')
            member = row['member_index']
            if member in event['members']:
                raise ValueError('duplicate member for exported event')
            event['members'][member] = float(row['aggregate_raw_exposure'])
    if not events or len(candidate_xy) != 1:
        raise ValueError('missing or ambiguous evaluator candidate')
    conflicts = []
    for key, event in events.items():
        t, hit, concentration, threshold = event['observation']
        if hit and all(v == 0 for v in event['members'].values()):
            conflicts.append(dict(update_id=int(key[0]), block_id=int(key[1]),
                                  cell_index=int(key[2]), time_s=t,
                                  concentration=concentration, threshold=threshold,
                                  member_count=len(event['members'])))
    return dict(contract='M1_PHIC_MODEL_SUPPORT_DIAGNOSTIC_V1',
                input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                candidate_evaluator_only=candidate, candidate_xy=list(candidate_xy)[0],
                candidates_in_export=len(candidates), selected_rows=selected_rows,
                selected_exported_events=len(events),
                distinct_time_cell_records=len({(e['observation'][0], key[2]) for key, e in events.items()}),
                distinct_positive_time_cell_records=len({(e['observation'][0], key[2]) for key, e in events.items() if e['observation'][1]}),
                selected_positive_events=sum(e['observation'][1] for e in events.values()),
                selected_nonzero_exposure_rows=sum(v > 0 for e in events.values() for v in e['members'].values()),
                all_candidates_nonzero_exposure_rows=nonzero_rows,
                all_member_zero_positive_events=len(conflicts),
                first_conflict=min(conflicts, key=lambda x:x['time_s']) if conflicts else None,
                verdict='MODEL_ZERO_WITH_OBSERVED_HITS' if conflicts else 'NO_HIT_ZERO_CONTRADICTION_FOUND',
                limits=['Zero surrogate exposure is not evidence that the physical route contains no source information.',
                        'Exports include historical events across updates; counts are not independent samples or counts of actual likelihood applications.',
                        'Cannot distinguish transport mismatch, source discretization, sensor memory, or event alignment from this export alone.',
                        'No per-candidate posterior recorded here: time of truth exclusion remains unknown.',
                        'Positive hits alone do not establish distinguishability among all candidate sources.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('refuse to overwrite previous evidence')
    result = audit(args.input, args.candidate)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
