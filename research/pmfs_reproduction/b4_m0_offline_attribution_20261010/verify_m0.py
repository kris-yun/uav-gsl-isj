"""B4-M0: read-only attribution of frozen native maps; no ROS or forward simulation.

Run: python -X utf8 verify_m0.py
Requires numpy. Default: verifies hashes and recomputes all saved source scores,
posteriors and attribution results, with no writes. --evidence selects the frozen
input folder; --write-derived DIR explicitly writes arithmetic outputs to DIR.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import numpy as np

TRUTH = np.array([-3.2, -3.3], dtype=float)
D = .4
FINAL_PEAK_INDEX = 1281
TRUE_CELL_INDEX = 629
ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def array(path, dtype):
    result = np.frombuffer(path.read_bytes(), dtype=dtype)
    assert np.isfinite(result).all(), path
    return result


def factors(measured, simulated, confidence):
    # Same evaluation order as Utils::lerp(1, 1-|p-h|*D, confidence).
    weight = np.where(confidence >= 0, np.minimum(confidence, 1), 0)
    return 1 + ((1 - np.abs(measured - simulated) * D) - 1) * weight


def leaf_for(tree, index, width):
    i, j = index % width, index // width
    match = [r for r in tree if r['has_children'] == '0'
             and int(r['origin_i']) <= i < int(r['origin_i']) + int(r['size_i'])
             and int(r['origin_j']) <= j < int(r['origin_j']) + int(r['size_j'])]
    assert len(match) == 1 and match[0]['value'] == '1', (index, match)
    return match[0]


def indices_for(node, width):
    x, y, w, h = [int(node[k]) for k in ('origin_i', 'origin_j', 'size_i', 'size_j')]
    return np.array([i + j * width for j in range(y, y + h) for i in range(x, x + w)])


def ancestor_chain(tree, node_id):
    lookup = {r['node_id']: r for r in tree}
    result = []
    while node_id != 'ROOT':
        assert node_id not in result, 'tree cycle'
        result.append(node_id)
        node_id = lookup[node_id]['parent_id']
    return list(reversed(result))


def measure_events(evidence):
    with (evidence / 'runtime/measurement_events.csv').open(encoding='utf-8', newline='') as handle:
        raw = list(csv.reader(handle))
    events = [dict(stamp_ns=int(r[0]), concentration_ppm=float(r[1]), wind_speed=float(r[2]),
                   wind_direction=float(r[3]), x=float(r[4]), y=float(r[5]),
                   stop=int(r[6]), block=int(r[7])) for r in raw]
    stops = []
    for stop_id in sorted(set(r['stop'] for r in events)):
        group = [r for r in events if r['stop'] == stop_id]
        assert len(group) == 5
        assert max(abs(r['x'] - group[0]['x']) + abs(r['y'] - group[0]['y']) for r in group) < 1e-7
        stops.append(dict(stop=stop_id, x=group[0]['x'], y=group[0]['y'],
                          blocks=len(group), positives=sum(r['concentration_ppm'] > .1 for r in group),
                          first_ROS_s=group[0]['stamp_ns'] / 1e9, last_ROS_s=group[-1]['stamp_ns'] / 1e9,
                          concentration_min_ppm=min(r['concentration_ppm'] for r in group),
                          concentration_max_ppm=max(r['concentration_ppm'] for r in group),
                          true_source_distance_m=float(np.linalg.norm(np.array([group[0]['x'], group[0]['y']]) - TRUTH))))
    return events, stops


def histogram(delta, free, xy, direct):
    # Predeclared user band, fixed metre bins, and direct-stop vs propagated cells.
    y = xy[:, 1]
    definitions = [('USER_Y_1.7_TO_2.7', (y >= 1.7) & (y <= 2.7)),
                   ('OUTSIDE_USER_BAND', ~((y >= 1.7) & (y <= 2.7))),
                   ('DIRECT_STOP_CELLS', direct), ('OTHER_FREE_CELLS', ~direct)]
    definitions += [(f'Y_[{b},{b+1})', (y >= b) & (y < b + 1)) for b in range(-8, 4)]
    result = []
    for name, mask in definitions:
        mask = mask & free
        values = delta[mask]
        result.append(dict(region=name, free_cells=int(mask.sum()), net_log_ratio=float(values.sum()),
                           positive_log_ratio=float(values[values > 0].sum()),
                           negative_log_ratio=float(values[values < 0].sum()),
                           ratio=float(np.exp(values.sum()))))
    return result


def node_summary(node, candidate, update, free, xy, posterior, input_data):
    indices = indices_for(node, update['width'])
    assert free[indices].all(), node['node_id']
    points = array(update['path'] / candidate['points_file'], '<f4').reshape(-1, 2)
    x, y, w, h = [int(node[k]) for k in ('origin_i', 'origin_j', 'size_i', 'size_j')]
    bounds = [update['origin_x'] + x * .25, update['origin_y'] + y * .25,
              update['origin_x'] + (x + w) * .25, update['origin_y'] + (y + h) * .25]
    assert len(points) == int(candidate['point_count'])
    assert ((points[:, 0] >= bounds[0] - 2e-6) & (points[:, 0] <= bounds[2] + 2e-6)
            & (points[:, 1] >= bounds[1] - 2e-6) & (points[:, 1] <= bounds[3] + 2e-6)).all()
    return dict(candidate_id=node['node_id'], origin_ij=[x, y], size_ij=[w, h],
                free_cell_count=len(indices), bounds_xy=bounds, saved_score=float(candidate['score']),
                candidate_serial=int(candidate['serial']), leaf_probability_mass=float(posterior[indices].sum()),
                per_cell_probability=float(posterior[indices[0]]), captured_release_points=len(points),
                release_point_mean_xy=points.astype(float).mean(axis=0).tolist(),
                release_point_min_xy=points.min(axis=0).tolist(), release_point_max_xy=points.max(axis=0).tolist(),
                rng_before=candidate['rng_before'], rng_after=candidate['rng_after'],
                gaussian_index_before=int(candidate['gaussian_index_before']),
                gaussian_index_after=int(candidate['gaussian_index_after']),
                source_mode='UNIFORM_WITHIN_RECTANGLE_NOT_EXACT_PHYSICAL_SOURCE',
                confidence_at_selected_cell=float(input_data[indices[0]]['confidence']))


def analyse(evidence):
    events, stops = measure_events(evidence)
    assert len(events) == 50 and len(stops) == 10 and sum(s['positives'] for s in stops) == 50
    updates = []
    cell_tables, region_tables, cross_tables, chain_tables = {}, {}, [], []
    selected = {}
    max_score_error = 0.
    max_post_error = 0.
    all_candidates = 0
    coarse_hashes = []
    saved_winds = []
    for path in sorted((evidence / 'runtime/updates').glob('update_*')):
        meta = read_json(path / 'metadata.json')
        assert [meta['width'], meta['height']] == [34, 45] and meta['cell_size'] == .25
        assert (path / 'COMPLETE.txt').exists()
        width, n = meta['width'], meta['width'] * meta['height']
        data = rows(path / 'input.csv')
        assert [int(r['cell_index']) for r in data] == list(range(n))
        free = np.array([r['occupancy'] == '1' for r in data])
        assert free.sum() == 447 and free[TRUE_CELL_INDEX] and free[FINAL_PEAK_INDEX]
        xy = np.column_stack([meta['origin_x'] + (np.arange(n) % width + .5) * .25,
                              meta['origin_y'] + (np.arange(n) // width + .5) * .25])
        assert np.array_equal(((TRUTH - [meta['origin_x'], meta['origin_y']]) / .25).astype(int), [17, 18])
        measured = 1 - 1 / (1 + np.exp(np.array([float(r['logOdds']) for r in data])))
        confidence = np.array([float(r['confidence']) for r in data])
        saved_winds.append(np.array([[float(r['u']), float(r['v'])] for r in data]))
        assert np.isfinite(measured).all() and np.isfinite(confidence).all()
        candidates = rows(path / 'candidates.csv')
        candidate_lookup = {r['candidate_id']: r for r in candidates}
        assert len(candidate_lookup) == len(candidates), 'overwritten maps from duplicate IDs'
        posterior = array(path / 'posterior.f64', '<f8')
        scores = np.zeros(n, dtype=np.longdouble)
        for candidate in candidates:
            hit = array(path / candidate['map_file'], '<f4')
            assert len(hit) == n and hit.min() >= 0 and hit.max() <= 1 + 2e-6
            factor = factors(measured, hit, confidence)
            assert factor[free].min() > 0
            computed = np.prod(factor[free].astype(np.longdouble), dtype=np.longdouble)
            saved = np.longdouble(candidate['score'])
            error = float(abs(computed - saved) / saved)
            max_score_error = max(max_score_error, error)
            assert error < 5e-12, candidate['candidate_id']
            scores[indices_for(candidate, width)] = saved
        raw = np.array([np.longdouble(r['score']) for r in rows(path / 'raw_cell_scores.csv')])
        assert np.allclose(scores, raw, rtol=1e-15, atol=0)
        rebuilt = np.where(free, scores / scores[free].sum(dtype=np.longdouble), 0)
        max_post_error = max(max_post_error, float(np.max(np.abs(rebuilt - posterior))))
        assert np.max(np.abs(rebuilt - posterior)) < 1e-12
        assert np.all(posterior[~free] == 0) and abs(posterior.sum() - 1) < 1e-12
        all_candidates += len(candidates)
        tree = rows(path / 'final_tree.csv')
        coarse_hashes.append(sha(path / 'coarse_tree.csv'))
        current_map_index = int(posterior.argmax())  # Fixed tie rule: lowest flattened index.
        visited = [s for s in stops if s['last_ROS_s'] <= meta['stamp_ns'] / 1e9 + 1e-6]
        direct = np.zeros(n, dtype=bool)
        for stop in visited:
            i, j = ((np.array([stop['x'], stop['y']]) - [meta['origin_x'], meta['origin_y']]) / .25).astype(int)
            assert 0 <= i < 34 and 0 <= j < 45
            direct[i + j * width] = True
        source_node = leaf_for(tree, TRUE_CELL_INDEX, width)
        own = dict(path=path, width=width, origin_x=meta['origin_x'], origin_y=meta['origin_y'])
        truth_summary = node_summary(source_node, candidate_lookup[source_node['node_id']], own, free, xy, posterior, data)
        pairs = {}
        for pair_name, wrong_index in [('FINAL_PEAK_FIXED', FINAL_PEAK_INDEX), ('CURRENT_MAP', current_map_index)]:
            wrong_node = leaf_for(tree, wrong_index, width)
            wrong_summary = node_summary(wrong_node, candidate_lookup[wrong_node['node_id']], own, free, xy, posterior, data)
            true_hit = array(path / candidate_lookup[source_node['node_id']]['map_file'], '<f4')
            wrong_hit = array(path / candidate_lookup[wrong_node['node_id']]['map_file'], '<f4')
            true_factor, wrong_factor = factors(measured, true_hit, confidence), factors(measured, wrong_hit, confidence)
            delta = np.where(free, np.log(wrong_factor) - np.log(true_factor), 0)
            saved_ratio = wrong_summary['saved_score'] / truth_summary['saved_score']
            post_ratio = posterior[wrong_index] / posterior[TRUE_CELL_INDEX]
            assert abs(float(delta.sum()) - math.log(saved_ratio)) < 5e-12
            assert abs(post_ratio / saved_ratio - 1) < 1e-12
            regions = histogram(delta, free, xy, direct)
            top_positive = np.flatnonzero(delta > 0)
            top_positive = sorted(top_positive, key=lambda k: (-delta[k], int(k)))[:20]
            top_negative = np.flatnonzero(delta < 0)
            top_negative = sorted(top_negative, key=lambda k: (delta[k], int(k)))[:20]
            pairs[pair_name] = dict(true_leaf=truth_summary, wrong_leaf=wrong_summary,
                wrong_cell_index=wrong_index, wrong_cell_xy=xy[wrong_index].tolist(),
                score_ratio_wrong_over_true=saved_ratio, per_cell_posterior_ratio=post_ratio,
                leaf_mass_ratio_wrong_over_true=wrong_summary['leaf_probability_mass'] / truth_summary['leaf_probability_mass'],
                total_log_ratio=float(delta.sum()), positive_log_ratio=float(delta[delta > 0].sum()),
                negative_log_ratio=float(delta[delta < 0].sum()),
                cells_favour_wrong=int((delta > 0).sum()), cells_favour_true=int((delta < 0).sum()),
                active_confidence_free_cells=int((free & (confidence > 0)).sum()),
                zero_contribution_free_cells=int((free & (delta == 0)).sum()),
                minimum_true_factor=float(true_factor[free].min()), minimum_wrong_factor=float(wrong_factor[free].min()),
                true_log_score=float(np.log(true_factor[free]).sum()), wrong_log_score=float(np.log(wrong_factor[free]).sum()),
                hard_zero_factor_count=int((true_factor[free] == 0).sum() + (wrong_factor[free] == 0).sum()),
                predefined_band_net_fraction=regions[0]['net_log_ratio'] / float(delta.sum()),
                top_positive_cell_indices=[int(k) for k in top_positive],
                top_negative_cell_indices=[int(k) for k in top_negative], regions=regions)
            key = path.name + '_' + pair_name
            cell_tables[key] = [dict(cell_index=k, grid_i=k % width, grid_j=k // width,
                x=float(xy[k, 0]), y=float(xy[k, 1]), free=bool(free[k]), direct_stop_cell=bool(direct[k]),
                measured_probability=float(measured[k]), confidence=float(confidence[k]),
                true_hit=float(true_hit[k]), wrong_hit=float(wrong_hit[k]),
                true_factor=float(true_factor[k]), wrong_factor=float(wrong_factor[k]),
                true_log_penalty=float(np.log(true_factor[k])) if free[k] else 0.,
                wrong_log_penalty=float(np.log(wrong_factor[k])) if free[k] else 0.,
                delta_log_wrong_over_true=float(delta[k])) for k in range(n)]
            region_tables[key] = regions
            for role, node in [('TRUE_REGION', source_node), ('WRONG_REGION', wrong_node)]:
                for depth, node_id in enumerate(ancestor_chain(tree, node['node_id'])):
                    record = candidate_lookup[node_id]
                    chain_tables.append(dict(update=path.name, pair=pair_name, role=role, depth=depth,
                        candidate_id=node_id, serial=int(record['serial']), size_i=int(record['size_i']),
                        size_j=int(record['size_j']), score=float(record['score']),
                        point_count=int(record['point_count']), rng_before=record['rng_before'], rng_after=record['rng_after']))
            if pair_name == 'FINAL_PEAK_FIXED':
                selected[path.name] = dict(true_hit=true_hit, wrong_hit=wrong_hit,
                    measured=measured, confidence=confidence, free=free, xy=xy, direct=direct)
        mean = (xy * posterior[:, None]).sum(axis=0)
        updates.append(dict(update=path.name, stamp_ROS_s=meta['stamp_ns'] / 1e9,
            complete_ROS_s=int((path / 'COMPLETE.txt').read_text(encoding='utf-8')) / 1e9,
            cumulative_measurement_blocks=sum(e['stamp_ns'] <= meta['stamp_ns'] for e in events),
            distinct_stops=len(visited), direct_stop_grid_cells=int(direct.sum()), candidates=len(candidates),
            variance=float(((xy - mean) ** 2).sum(axis=1) @ posterior),
            MAP_index=current_map_index, MAP_xy=xy[current_map_index].tolist(),
            MAP_error_m=float(np.linalg.norm(xy[current_map_index] - TRUTH)),
            posterior_mean_xy=mean.tolist(), posterior_mean_error_m=float(np.linalg.norm(mean - TRUTH)),
            source_1m_probability=float(posterior[np.linalg.norm(xy - TRUTH, axis=1) <= 1].sum()),
            source_cell_confidence=float(confidence[TRUE_CELL_INDEX]), pairs=pairs))
    assert len(updates) == 3
    # 3x3 fixed physical-region map pairing; score-only, not algorithm branches.
    for observation_name, observation in selected.items():
        for maps_name, maps in selected.items():
            true_factor = factors(observation['measured'], maps['true_hit'], observation['confidence'])
            wrong_factor = factors(observation['measured'], maps['wrong_hit'], observation['confidence'])
            true_score = float(np.prod(true_factor[observation['free']].astype(np.longdouble), dtype=np.longdouble))
            wrong_score = float(np.prod(wrong_factor[observation['free']].astype(np.longdouble), dtype=np.longdouble))
            cross_tables.append(dict(observation_update=observation_name, maps_update=maps_name,
                                     true_score=true_score, wrong_score=wrong_score,
                                     log_ratio=math.log(wrong_score / true_score), ratio=wrong_score / true_score,
                                     scope='CONDITIONAL_FIXED_MAP_SCORING_NOT_NATIVE_BRANCH_OR_CAUSAL_EFFECT'))
    log_matrix = np.array([[next(r['log_ratio'] for r in cross_tables
                           if r['observation_update'] == f'update_{i}' and r['maps_update'] == f'update_{j}')
                           for j in range(3)] for i in range(3)])
    final = updates[-1]['pairs']['FINAL_PEAK_FIXED']
    # Endpoint algebra uses a fixed path; the interaction prevents unique causal allocation.
    l00, l20, l02, l22 = log_matrix[0, 0], log_matrix[2, 0], log_matrix[0, 2], log_matrix[2, 2]
    closest = min(stops, key=lambda s: s['true_source_distance_m'])
    result = dict(verdict='B4_M0_ARITHMETIC_ATTRIBUTION_PASS_PHYSICAL_CAUSE_HOLD',
        experiment_scope='FROZEN_NATIVE_MAP_SCORE_ONLY_NO_NEW_FORWARD_SIMULATION',
        parent_commit='c2aacbac7fb2ef7be4be3c9c7dcfce20c11f823c',
        sourceDiscriminationPower=D, true_source_XYZ=[-3.2, -3.3, -.5], true_cell_index=TRUE_CELL_INDEX,
        fixed_final_wrong_cell_index=FINAL_PEAK_INDEX, wrong_peak_selected_posthoc_for_diagnosis=True,
        coordinate_convention='Saved rounded origin, 0.25 m centres; native float32 rounding is sub-micrometre here.',
        all_candidate_scores_recomputed=all_candidates, maximum_relative_score_error=max_score_error,
        maximum_posterior_absolute_error=max_post_error,
        coarse_tree_sha256=coarse_hashes, all_updates_restart_same_coarse_tree=len(set(coarse_hashes)) == 1,
        saved_2D_wind_max_abs_difference_vs_update0=[float(np.abs(wind-saved_winds[0]).max()) for wind in saved_winds],
        all_three_captured_2D_wind_fields_identical=all(np.array_equal(wind, saved_winds[0]) for wind in saved_winds),
        observation=dict(blocks=50, positive_blocks=50, negative_blocks=0, distinct_stop_count=10,
                         closest_stop=closest, stops=stops, independent_experiment_count=1,
                         correlated_stop_blocks_are_not_independent=True),
        updates=updates, fixed_region_cross_map_scoring=cross_tables,
        endpoint_log_ratio_decomposition=dict(total_change=float(l22-l00),
            observation_change_at_update0_maps=float(l20-l00),
            map_and_resolution_change_at_update0_observation=float(l02-l00),
            interaction=float(l22-l20-l02+l00),
            interpretation='Arithmetic only. Map change includes RNG and source-region resolution; captured 2D winds are identical. No independent isolation.'),
        final_score_ratio=final['score_ratio_wrong_over_true'],
        final_predefined_band_net_log_fraction=final['predefined_band_net_fraction'],
        claims=dict(score_winning_spatial_regions='PASS', posterior_arithmetic='PASS',
                    hard_zero_explanation='FAIL_NOT_PRESENT_WITH_D_0.4',
                    cross_update_tree_persistence='FAIL_COARSE_TREE_RESTARTS',
                    within_update_adaptive_refinement_causal_bias='HOLD',
                    finite_forward_sampling_causal_effect='HOLD',
                    true_source_point_forward_response='HOLD_REGION_MIXTURE_ONLY',
                    observation_identifiability='HOLD_NO_INDEPENDENT_PHYSICAL_REFERENCE',
                    three_dimensional_model_mismatch_cause='HOLD',
                    time_varying_wind_history_mismatch='NOT_TESTED_STATIC_FRAME10'),
        execution_ledger=dict(new_ROS_processes=0, VM_commands=0, new_GADEN_or_CFD=0,
                              new_PMFS_source_updates=0, new_goals=0, new_seeds=0, training=0,
                              changed_frozen_raw_data=0, historical_STOP_verdicts_changed=0))
    assert result['all_updates_restart_same_coarse_tree']
    assert result['all_three_captured_2D_wind_fields_identical']
    assert final['hard_zero_factor_count'] == 0 and abs(result['final_score_ratio'] - 14874.5986951951) < 1e-7
    return result, cell_tables, region_tables, cross_tables, chain_tables


def write_csv(path, items):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(items[0]))
        writer.writeheader()
        writer.writerows(items)


def export(result, cells, regions, cross, chains, destination):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'B4_M0_RESULT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for key, records in cells.items():
        write_csv(destination / (key + '_CELL_ATTRIBUTION.csv'), records)
    for key, records in regions.items():
        write_csv(destination / (key + '_REGION_ATTRIBUTION.csv'), records)
    write_csv(destination / 'FIXED_REGION_CROSS_MAP_SCORING.csv', cross)
    write_csv(destination / 'SOURCE_LEAF_AND_REFINEMENT_TRACE.csv', chains)
    write_csv(destination / 'DIRECT_STOPS_AND_COVERAGE.csv', result['observation']['stops'])


def compare(actual, expected, path='result'):
    if isinstance(actual, dict):
        assert actual.keys() == expected.keys(), path
        for key in actual:
            compare(actual[key], expected[key], path + '.' + key)
    elif isinstance(actual, list):
        assert len(actual) == len(expected), path
        for k, value in enumerate(actual):
            compare(value, expected[k], f'{path}[{k}]')
    elif isinstance(actual, float):
        assert math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12), (path, actual, expected)
    else:
        assert actual == expected, (path, actual, expected)


def verify_csv(path, records):
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
    assert path.read_bytes() == buffer.getvalue().encode('utf-8'), path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT / 'evidence')
    parser.add_argument('--write-derived', type=Path, help='Explicit opt-in arithmetic output folder; does not alter raw inputs.')
    parser.add_argument('--skip-package-manifest', action='store_true')
    args = parser.parse_args()
    count = 0
    if not args.skip_package_manifest and (ROOT / 'SHA256_MANIFEST.json').exists():
        manifest = read_json(ROOT / 'SHA256_MANIFEST.json')
        actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p != ROOT / 'SHA256_MANIFEST.json'}
        assert actual == set(manifest), 'package manifest coverage'
        for name, digest in manifest.items():
            assert sha(ROOT / name) == digest, name
        count = len(manifest)
    outputs = analyse(args.evidence.resolve())
    if (ROOT / 'derived/B4_M0_RESULT.json').exists():
        compare(outputs[0], read_json(ROOT / 'derived/B4_M0_RESULT.json'))
        for key, records in outputs[1].items():
            verify_csv(ROOT / 'derived' / (key + '_CELL_ATTRIBUTION.csv'), records)
        for key, records in outputs[2].items():
            verify_csv(ROOT / 'derived' / (key + '_REGION_ATTRIBUTION.csv'), records)
        verify_csv(ROOT / 'derived/FIXED_REGION_CROSS_MAP_SCORING.csv', outputs[3])
        verify_csv(ROOT / 'derived/SOURCE_LEAF_AND_REFINEMENT_TRACE.csv', outputs[4])
        verify_csv(ROOT / 'derived/DIRECT_STOPS_AND_COVERAGE.csv', outputs[0]['observation']['stops'])
    if args.write_derived:
        destination = args.write_derived.resolve()
        assert not destination.is_relative_to(args.evidence.resolve()), 'cannot write inside raw evidence'
        assert not destination.is_relative_to(ROOT), 'use a new folder outside this frozen package'
        export(*outputs, args.write_derived.resolve())
    print(json.dumps(dict(verdict='PASS_FROZEN_B4_M0_READONLY_RECOMPUTATION', package_hashes=count,
        candidate_scores=outputs[0]['all_candidate_scores_recomputed'],
        maximum_relative_score_error=outputs[0]['maximum_relative_score_error'],
        maximum_posterior_absolute_error=outputs[0]['maximum_posterior_absolute_error'],
        final_score_ratio=outputs[0]['final_score_ratio'],
        predefined_band_net_log_fraction=outputs[0]['final_predefined_band_net_log_fraction'],
        physical_cause='HOLD', new_simulations=0, new_native_updates=0, writes=bool(args.write_derived)), indent=2))


if __name__ == '__main__':
    main()
