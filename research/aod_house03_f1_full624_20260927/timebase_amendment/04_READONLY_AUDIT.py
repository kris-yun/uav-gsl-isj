#!/usr/bin/env python3
"""Read-only audit of AOD F1 time metadata; NEVER load concentration arrays.

Usage:
  python 04_READONLY_AUDIT.py /path/to/AOD_HOUSE03_F1_FULL624_REVIEW_20260927.zip --out out

Only Python standard library is used. ZIP members are streamed for hashing;
scientific arrays are never decoded. No RNG, no model, no subprocess, no simulator.
The draft schedule is a PROPOSAL requiring sign-off, not a passed original gate.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, struct, zipfile
from pathlib import Path
from typing import Any

EXPECTED_SHA = 'de4fe418b9c4cf4b9377349436516bb77be0952bac1708be23f0308ea775d0b7'
META = 'review_metadata/source_0_replica_0/'

def f32(x: float) -> float:
    return struct.unpack('<f', struct.pack('<f', x))[0]

def digest_stream(f: Any) -> str:
    h = hashlib.sha256()
    for block in iter(lambda: f.read(1 << 20), b''):
        h.update(block)
    return h.hexdigest()

def records(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text), delimiter='\t'))

def dump(out: Path, name: str, obj: Any) -> None:
    (out / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def reconstruct() -> tuple[list[dict[str, Any]], list[float], tuple[int, float, int]]:
    # Snapshot 0 is anchored to the observed initial write. Header initializers
    # are not in the supplied archive, so we do NOT claim to reconstruct them.
    dt, save_dt, wind_dt = f32(.1), f32(.5), f32(1.)
    t, last_save, last_wind, acc = f32(0), f32(0), f32(0), f32(0)
    wind, step = 0, 0
    saved, ticks = [], []
    first_batch = None
    while t < 510.:
        ticks.append(t)
        acc = f32(acc + f32(f32(7.) * dt))
        count = math.floor(acc)
        if count and first_batch is None:
            first_batch = (step, t, count)
        acc = f32(acc - count)
        if step == 0 or t > f32(last_save + save_dt):
            saved.append(dict(save_record_id=len(saved), clock_before_s=t,
                              wind_before=wind, integration_step=step))
            last_save = t
        if t > f32(last_wind + wind_dt):
            wind = wind + 1 if wind < 10 else 1
            last_wind = t
        t = f32(t + dt)
        step += 1
    if first_batch is None:
        raise RuntimeError('No predicted emission')
    return saved, ticks, first_batch

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review_zip', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not args.review_zip.is_file():
        parser.error('Input ZIP does not exist')
    out = args.out.resolve()
    if out == args.review_zip.resolve():
        parser.error('Output must not be the input file')
    out.mkdir(parents=True, exist_ok=True)
    with args.review_zip.open('rb') as f:
        archive_sha = digest_stream(f)
    if archive_sha != EXPECTED_SHA:
        raise ValueError('Unexpected archive SHA256; stop, do not silently change the input contract')

    with zipfile.ZipFile(args.review_zip) as z:
        text = lambda n: z.read(n).decode('utf-8')
        jread = lambda n: json.loads(text(n))
        hashes = []
        for ln in text('SHA256SUMS').splitlines():
            if not ln.strip():
                continue
            expected, name = ln.split(maxsplit=1)
            name = name.lstrip('*')
            with z.open(name) as f:
                actual = digest_stream(f)
            hashes.append(dict(path=name, expected=expected, actual=actual, matched=expected == actual))
        if not all(x['matched'] for x in hashes):
            raise ValueError('Internal hash mismatch')
        dump(out, 'ARCHIVE_HASH_CHECK.json', hashes)

        rows = records(text(META + 'RESULT_TIME_MAP.tsv'))
        release = records(text(META + 'RELEASE_TIME_METADATA.tsv'))
        observed = [dict(save_record_id=int(r['save_record_id']), clock_before_s=float(r['physical_sim_time_s']),
                         wind_before=int(r['wind_index']), integration_step=int(r['integration_step'])) for r in rows]
        predicted, ticks, first_batch = reconstruct()
        if observed != predicted:
            raise ValueError('Source-based clock reconstruction disagrees with metadata')
        actual_first = next(r for r in release if r['event'] == 'first_nonzero_filament_count')
        if first_batch[1] != float(actual_first['physical_sim_time_s']):
            raise ValueError('Release accumulator / log mismatch')
        enable = next(r for r in release if r['event'] == 'release_enabled_first_step')
        targets = list(range(50, 501, 50))
        saved_counts = [sum(abs(r['clock_before_s'] - t) <= 1e-9 for r in observed) for t in targets]
        tick_counts = [sum(abs(v - t) <= 1e-9 for v in ticks) for t in targets]
        old_pass = abs(float(enable['physical_sim_time_s'])) <= 1e-9 and abs(first_batch[1]) <= 1e-9 and saved_counts == [1]*10
        old_gate = dict(decision='TIMEBASE_METADATA_VALID' if old_pass else 'AOD_F1_HOLD_TIMEBASE',
                        scientific_pass_or_fail=None, writer_records=len(observed),
                        integration_ticks=len(ticks), exact_saved_counts=saved_counts,
                        exact_integration_clock_counts=tick_counts,
                        configured_start_s=float(enable['physical_sim_time_s']), first_nonempty_log=actual_first,
                        predicted_first_emission_batch=dict(integration_step=first_batch[0], clock_before_s=first_batch[1], n=first_batch[2]),
                        all_writer_time_step_wind_tuples_identical=True,
                        initial_write_anchor='observed record 0; header initializers not supplied',
                        stage='Add -> Move -> Save -> Wind update -> Clock update')
        if old_gate['decision'] != jread('RESULT.json')['decision']:
            raise ValueError('Recomputed original gate differs')
        dump(out, 'OLD_GATE_AND_CLOCK_REPLAY.json', old_gate)

        # PROPOSED once-for-all acquisition schedule. No nearest selection,
        # interpolation, rounding, target values, or per-realization tuning.
        schedule = []
        for slot, tau in enumerate(targets, 1):
            r = max((r for r in observed if r['clock_before_s'] <= tau), key=lambda r: r['clock_before_s'])
            d = dict(slot=slot, nominal_request_s=tau, **r,
                     signed_clock_offset_s=r['clock_before_s'] - tau,
                     completed_integration_steps=r['integration_step'] + 1,
                     nominal_post_update_time_s=(r['integration_step'] + 1) / 10.,
                     state_stage='POST_MOVE_PRE_WIND_PRE_CLOCK',
                     filename='iteration_' + str(r['save_record_id']),
                     status='PROPOSED_NOT_AUTHORIZED')
            # Both labels precede the request for this exact frozen schedule.
            if d['nominal_post_update_time_s'] > tau:
                raise ValueError('Proposed state extends beyond requested slot')
            schedule.append(d)
        with (out / 'NATIVE_SNAPSHOT_SCHEDULE_PROPOSED.tsv').open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(schedule[0]), delimiter='\t'); w.writeheader(); w.writerows(schedule)

        feasibility = []
        for pname in ['A', 'B']:
            pr = records(text(f'protocol/frozen/HOUSE03_PATH_{pname}_10.tsv'))
            previous = 0.
            for row, sample in zip(pr, schedule, strict=True):
                gap = sample['clock_before_s'] - previous
                dwell, travel = float(row['reserved_dwell_s']), float(row['travel_time_s'])
                margin = gap - dwell - travel
                feasibility.append(dict(path=pname, slot=sample['slot'], probe_rank=int(row['probe_rank']),
                                        sample_clock_before_s=sample['clock_before_s'], interval_s=gap,
                                        travel_time_s=travel, dwell_s=dwell, time_margin_s=margin,
                                        feasible_under_proposed_clock=margin >= 0))
                previous = sample['clock_before_s']
        if not all(x['feasible_under_proposed_clock'] for x in feasibility):
            raise ValueError('Draft time amendment breaks fixed path feasibility')
        dump(out, 'PROPOSED_PATH_TIME_FEASIBILITY.json', feasibility)

        audit = jread('CANDIDATE_BANK_AUDIT.json')
        seedrows = records(text('protocol/frozen/HOUSE03_FUTURE_PMFS_SEEDS_FULL624_54912.tsv'))
        key = lambda r: (r['source_id'], int(r['wind_state']), int(r['transport_replica_index']))
        expected_keys = {key(r): int(r['requested_seed']) for r in seedrows}
        actual_keys = {key(r): int(r['requested_seed']) for r in audit['records']}
        if len(actual_keys) != 54912 or actual_keys != expected_keys or len(seedrows) != 54912:
            raise ValueError('Candidate manifest key/seed mismatch')
        for r in audit['records']:
            if set(r['hashes']) != {'p', 'rawp', 'u', 'rawu'}:
                raise ValueError('Candidate record missing channels')
        dump(out, 'CANDIDATE_RECORD_AUDIT.json', dict(records=len(audit['records']),
             unique_keys=len(actual_keys), candidates=len({k[0] for k in actual_keys}),
             manifest_key_seed_match=True, map_channels_per_record=4,
             raw_vm_maps_rehashed=False, note='Registry check, NOT an independent rehash of the 1.90 GiB VM bank'))

        summary = dict(original_zip_sha256=archive_sha, internal_hashes=len(hashes),
                       original_decision_preserved=old_gate['decision'], scientific_decision=None,
                       matched_writer_records=len(observed), reconstructed_clock_ticks=len(ticks),
                       all_saved_and_integration_exact_requested_time_counts_zero=True,
                       candidate_manifest_records_checked=len(actual_keys),
                       actual_run_generation_count_as_reported=1,
                       review_new_plumes=0, review_new_forwards=0, review_random_draws=0,
                       target_concentration_loaded=False, template_arrays_decoded=False,
                       max_draft_native_time_shift_s=max(-d['signed_clock_offset_s'] for d in schedule),
                       min_draft_path_interval_s=min(x['interval_s'] for x in feasibility),
                       min_draft_motion_margin_s=min(x['time_margin_s'] for x in feasibility),
                       proposed_amendment_authorized=False,
                       recommendation='Preserve old HOLD; sign metadata-only acquisition amendment before gas read; reuse complete bank and first unread run')
        dump(out, 'SUMMARY.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
