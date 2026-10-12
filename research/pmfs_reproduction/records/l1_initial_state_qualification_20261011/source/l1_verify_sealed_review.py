"""Offline review of sealed V1 counterexamples; no dynamics, training or ROS."""
from pathlib import Path
import argparse, hashlib, json, math, zipfile
import numpy as np


def verify(root):
    root = Path(root)
    manifest = json.loads((root / 'L1_SHA256.json').read_text(encoding='utf8'))
    bad = [n for n, h in manifest.items()
           if hashlib.sha256((root / n).read_bytes()).hexdigest() != h]
    assert not bad, bad
    contract = json.loads((root / 'L1_PROSPECTIVE_MODEL_CONTRACT_REV1.json').read_text())
    q = json.loads((root / 'L1_WIND_AND_GEOMETRY_QUALIFICATION.json').read_text())
    f = json.loads((root / 'L1_INDEPENDENT_BOUNDARY_AND_ESS_FAIL.json').read_text())
    states = np.fromfile(root / 'public_inputs/geometry_states.u8', dtype=np.uint8)
    nx, ny, nz = q['geometry']['dims']
    assert states.size == nx * ny * nz
    free = np.flatnonzero(states == 0)
    coords = np.column_stack((free % nx, free // nx % ny, free // (nx * ny)))
    expected = []
    for axis, limit in enumerate((nx, ny, nz)):
        for side, level in enumerate((0, limit - 1)):
            ids = free[coords[:, axis] == level]
            expected.append(np.column_stack((ids, np.full(len(ids), axis), np.full(len(ids), side))))
    owners = np.load(root / 'L1_OOB_FACE_OWNERS.npy')
    velocity = np.load(root / 'L1_OOB_FACE_VELOCITIES.npy')
    assert np.array_equal(owners, np.concatenate(expected))
    assert velocity.shape == (24, len(owners))
    assert len(owners) == f['total_free_OOB_faces'] == 18377
    assert np.isclose(np.max(np.abs(velocity)), max(d['max_abs_velocity_m_s_per_unit_mode'] for d in f['OOB_boundary_details']))
    assert np.any(np.abs(velocity) > 1e-7), 'Expected preserved boundary failure'
    logweights = np.array([r['log_importance_weight'] for r in q['wind_refs']])
    weights = np.exp(logweights - logweights.max())
    weights /= weights.sum()
    ess = float(1 / np.dot(weights, weights))
    assert np.allclose(weights, f['wind_probability_weights'], rtol=1e-12, atol=0)
    assert abs(ess - f['ESS']) < 1e-12
    assert ess / len(weights) < contract['qual_gates'].get('ess_numeric_threshold', .8)
    H = np.load(root / 'L1_LOCAL_WIND_OBSERVATION_H.npy')
    rank = int(np.count_nonzero(np.linalg.svd(H, compute_uv=False) > 1e-10))
    assert rank == f['local_wind_linear_observation_rank'] == 2
    for contract_name in ('L1_PROSPECTIVE_MODEL_CONTRACT', 'L1_PROSPECTIVE_MODEL_CONTRACT_REV1'):
        raw = (root / (contract_name + '.json')).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == (root / (contract_name + '.sha256')).read_text().strip()
    rejection = json.loads((root / 'L1_DEPENDENT_EXECUTION_REJECTION.json').read_text())
    assert rejection['fixture_only'] and rejection['actualforwards'] == 0 and rejection['actualgoals'] == 0
    for source in ('public_inputs/RunningSimulation.original.cpp', 'L1_OPERATOR_IMPLEMENTATION_SOURCE.json'):
        assert (root / source).exists()
    native = (root / 'public_inputs/RunningSimulation.original.cpp').read_text()
    block = native[native.index('RunningSimulation::StepTowards('):]
    assert 'cellState == Environment::CellState::Obstacle || cellState == Environment::CellState::OutOfBounds' in block
    assert block.index('Environment::CellState::OutOfBounds') < block.index('else if (cellState == Environment::CellState::Outlet)')
    return {'manifest_members_checked': len(manifest), 'mismatches': bad,
            'OOB_faces_checked': len(owners), 'nonzero_OOB_normal_velocity': True,
            'ESS': ess, 'ESS_over_K': ess / len(weights), 'wind_observation_rank': rank,
            'gas_calls_recorded': 0, 'native_goals_recorded': 0,
            'scope': 'Independent arithmetic/source and archive checks; not physical execution qualification'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('review_directory', type=Path)
    parser.add_argument('--zip', type=Path)
    args = parser.parse_args()
    result = verify(args.review_directory)
    if args.zip:
        with zipfile.ZipFile(args.zip) as z:
            assert z.testzip() is None
            manifest = json.loads(z.read('L1_SHA256.json'))
            assert all(hashlib.sha256(z.read(n)).hexdigest() == h for n, h in manifest.items())
            result['zip_members_checked'] = len(manifest)
            result['zip_crc'] = 'PASS'
        result['zip_sha256'] = hashlib.sha256(args.zip.read_bytes()).hexdigest()
    print(json.dumps(result, indent=2))
