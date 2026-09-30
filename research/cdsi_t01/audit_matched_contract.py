"""Metadata-only CDSI-T0.1 prerequisite audit. No tensor loading or simulation."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / 'evidence/ocb_r2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def read_tsv(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8')), delimiter='\t'))


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')


def write_tsv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    paths = [EV/'OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv', EV/'s2x/OCB_R2_S2X_RUNLIST_32.tsv']
    runlists = [read_tsv(p) for p in paths]
    assert [len(rows) for rows in runlists] == [32, 32]
    frozen = read_json(EV/'mechanism_census_r0/R0_INPUT_HASHES.json')
    manifests, inventory, coordinates, pairs, bindings = {}, [], {}, [], []
    for family, rows in zip(('s2', 's2x'), runlists):
        for row in rows:
            rid = row['run_id']
            c = int(row['config_index'] if family == 's2' else row['parent_s2_config_index'])
            r = int(rid[-2:])
            mp = EV / ('s2_runs' if family == 's2' else 's2x/runs') / (rid+'.RUN_MANIFEST.json')
            m = read_json(mp)
            manifests[rid] = m
            archive = Path('C:/GADEN_OCB_R2_ARCHIVE') / ('s2_discovery' if family == 's2' else 's2x_matched_source') / rid / 'RUN_MANIFEST.json'
            assert archive.exists(), f'Archive metadata missing: {archive}'
            assert read_json(archive) == m, f'Archive metadata differs: {rid}'
            assert m['run_id'] == rid and m['house'] == row['house']
            assert m['source_id'] == row['source_id'] and m['wind_id'] == row['wind_id']
            assert int(m['master_seed']) == int(row['master_seed'])
            p = m['simulation_parameters']
            assert p['gas_type'] == row['gas_type']
            xyz = [float(p['source_position_'+axis]) for axis in 'xyz']
            assert xyz == [float(row['source_'+axis]) for axis in 'xyz']
            q = m['qualification_standard']
            assert q['manifest_pass'] and q['record_count'] == 1803
            coords = dict(house=m['house'], source_id=m['source_id'], x=xyz[0], y=xyz[1], z=xyz[2])
            key = (m['house'], m['source_id'])
            assert key not in coordinates or coordinates[key] == coords
            coordinates[key] = coords
            tensor = EV/'mechanism_census_r0/inputs'/(rid+'.pooled.npy')
            # Hash raw bytes only; never deserialize concentration/tensor values.
            tensor_hash = sha(tensor)
            assert tensor_hash == frozen['pooled_tensor_sha256'][rid]
            bindings.append(dict(run_id=rid, file=str(tensor.relative_to(ROOT)).replace('\\','/'), sha256=tensor_hash, frozen_hash_match=True, numerical_values_loaded=False))
            inventory.append(dict(run_id=rid, context=f'X{c:02d}', replicate_ordinal=r,
                family=family, house=m['house'], source_id=m['source_id'], source_x=xyz[0],
                source_y=xyz[1], source_z=xyz[2], wind_id=m['wind_id'], gas_type=p['gas_type'],
                master_seed=m['master_seed'], generator_sha256=m['generator_binary_sha256'],
                record_count=q['record_count'], time_axis_sha256=q['timeline_sha256'],
                wind_index_sha256=q['wind_index_sequence_sha256'],
                metadata_file=str(mp.relative_to(ROOT)).replace('\\','/'), metadata_sha256=sha(mp),
                archive_metadata_path=str(archive), archive_metadata_sha256=sha(archive),
                archive_metadata_semantic_parity=True, frozen_tensor_sha256=tensor_hash))
    assert len(manifests) == 64 and len({m['master_seed'] for m in manifests.values()}) == 64
    for c in range(8):
        for r in range(1,5):
            aid, bid = f'ocb_r2_cfg{c:02d}_r{r:02d}', f'ocb_r2_s2x_x{c:02d}_r{r:02d}'
            a, b = manifests[aid], manifests[bid]
            ap, bp = a['simulation_parameters'], b['simulation_parameters']
            excluded = {'source_position_x','source_position_y','source_position_z','results_location'}
            differences = sorted(k for k in set(ap)|set(bp) if ap.get(k) != bp.get(k))
            checks = dict(same_house=a['house']==b['house'], same_wind=a['wind_id']==b['wind_id'],
                same_gas=ap['gas_type']==bp['gas_type'], same_non_source_parameters=
                {k:v for k,v in ap.items() if k not in excluded}=={k:v for k,v in bp.items() if k not in excluded},
                same_asset_hashes=a['asset_checks']==b['asset_checks'],
                same_generator=a['generator_binary_sha256']==b['generator_binary_sha256'],
                same_time_axis=a['qualification_standard']['timeline_sha256']==b['qualification_standard']['timeline_sha256'],
                same_wind_sequence=a['qualification_standard']['wind_index_sequence_sha256']==b['qualification_standard']['wind_index_sequence_sha256'],
                same_thread_contract=a['omp_num_threads']==b['omp_num_threads']==1,
                crossed_source=a['source_id']!=b['source_id'])
            assert all(checks.values()), (aid, checks)
            assert b['parent_s2_run_id'] == aid
            # The generator folds these 32-bit master seeds and adds fixed salts.
            # Different masters therefore initialize different streams; ordinal r is not a stream key.
            same_master = a['master_seed'] == b['master_seed']
            assert not same_master, 'Unexpected stream match: reassess protocol instead of using this failure-only audit.'
            pairs.append(dict(context=f'X{c:02d}', replicate_ordinal=r, a_run_id=aid, b_run_id=bid,
                **checks, a_master_seed=a['master_seed'], b_master_seed=b['master_seed'],
                same_master_stream_identity=False, same_replicate_ordinal=True,
                parameter_differences=','.join(differences),
                scientific_changes='source_xyz;master_rng_seed', gate_a='FAIL'))
    write_tsv(out/'EXACT_64_RUN_MANIFEST.tsv', inventory)
    write_tsv(out/'PAIRED_AB_AUDIT.tsv', pairs)
    write_tsv(out/'SOURCE_COORDINATES.tsv', sorted(coordinates.values(), key=lambda d:(d['house'],d['source_id'])))
    write_tsv(out/'FROZEN_TENSOR_HASH_BINDING.tsv', bindings)
    inputs = paths + [EV/'mechanism_census_r0/R0_INPUT_HASHES.json',
        ROOT/'research/ocb_r2/OCB_R2_S2X_MATCHED_SOURCE_CROSSOVER_32_PLAN.md',
        ROOT/'research/ocb_r2/OCB_R2_GENERATOR_CONTRACT.md',
        ROOT/'research/ocb_r2/RNG_THREAD_DETERMINISM_AUDIT.md',
        ROOT/'research/ocb_r2/RNG_INVENTORY.tsv',
        ROOT/'research/ocb_r2/run_s2_vm.py', ROOT/'research/ocb_r2/run_s2x_vm.py', Path(__file__)]
    write_tsv(out/'AUDIT_INPUT_SHA256.tsv', [dict(path=str(p.relative_to(ROOT)).replace('\\','/'), sha256=sha(p)) for p in inputs])
    result = dict(decision='CDSI_T01_MATCHED_INTERVENTION_FAIL', run_count=64,
        context_count=8, proposed_pair_count=32, non_source_environment_matched_pairs=32,
        same_master_stream_pairs=0, different_master_stream_pairs=32,
        archive_metadata_semantic_parity_count=64, frozen_tensor_hash_match_count=64,
        reason='S2X deliberately used independent master seeds; matching replicate ordinals do not prove matched exogenous disturbances.',
        gate_a='FAIL', G1='NOT_EXECUTED', G2='NOT_EXECUTED', G3='NOT_EXECUTED',
        source_information_status='NOT_TESTED_BY_THIS_PROTOCOL',
        q_crossnobis_covariance_permutations='NOT_EXECUTED_AFTER_GATE_A_FAIL',
        r3a_geometry_audit='NOT_EXECUTED_AFTER_GATE_A_FAIL',
        new_simulations=0, models_trained=0, pmfs_modified=False,
        confirmation_or_house03_opened=False, numerical_target_values_loaded=False,
        theory_pass_claimed=False)
    write_json(out/'CDSI_T01_RESULT.json', result)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output.resolve())
