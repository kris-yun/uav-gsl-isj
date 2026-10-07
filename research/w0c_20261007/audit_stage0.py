"""Read-only eligibility screen for W0C, before any wind intervention."""
from pathlib import Path
import csv
import hashlib
import json
import datetime
import numpy as np

HERE = Path(__file__).resolve().parent
OLD = Path('C:/Users/50176/Documents/Codex/2026-10-05/codex-pmfs-pmfs-task-sufficient-world/outputs')
P0 = OLD / 'P0'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def write_csv(name, rows):
    with (HERE / name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

protocol_path = HERE / 'STAGE0_BOUNDARY_PROTOCOL_FROZEN.json'
protocol = json.loads(protocol_path.read_text())
if (HERE / 'STAGE0_DECISION.json').exists():
    raise RuntimeError('Stage 0 already evaluated; preserve its evidence rather than overwrite.')
write_json('STAGE0_PRE_SCORE_SEAL.json', {
    'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'protocol_sha256': sha(protocol_path), 'audit_code_sha256': sha(__file__),
    'new_simulations': 0, 'perturbations_generated': 0,
    'upstream_gate_sha256': sha(HERE.parents[1] / 'handoff/pro_20261007/W0C_MATCHED_TRANSPORT_ERROR_CAUSAL_GATE.md')
})
runs = json.loads((P0 / 'RUNS_64_FROZEN.json').read_text())
seal = json.loads((P0 / 'EXTRACTION_SEAL_BEFORE_SCORING.json').read_text())
sources = json.loads((OLD / 'R0C/SOURCE_CONTRACT_R0C.json').read_text())
assert sources['decision'] == 'R0C0_SOURCE_CONTRACT_PASS'
source_map = {(h['house'], s['source']): s for h in sources['house_contracts'] for s in [h['source_A'], h['source_B']]}
lineage = []
for p in [protocol_path, Path(__file__), P0/'RUNS_64_FROZEN.json', P0/'EXTRACTION_SEAL_BEFORE_SCORING.json', OLD/'R0C/SOURCE_CONTRACT_R0C.json']:
    lineage.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)})
for h in sources['house_contracts']:
    p = P0/(h['house']+'_OccupancyGrid3D.csv')
    assert sha(p) == h['occupancy_sha256']
    lineage.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)})

groups = {}
for r in runs:
    if r['gas_type'] != protocol['baseline_gas']:
        continue
    p = P0 / 'states' / (r['run_id'] + '.npz')
    digest = sha(p)
    assert digest == seal['state_files'][r['run_id']], f'Original state hash mismatch: {p}'
    lineage.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest})
    with np.load(p) as z:
        valid = (z['times'] >= 100) & (z['times'] <= 700) & z['valid']
        assert valid.sum() == 31
        state = {k: z[k].copy() for k in ['footprint', 'plume_wind', 'raw', 'lo', 'span']}
        state['selected'] = valid
    groups.setdefault((r['house'], r['wind_label'], r['source']), []).append((r, state))

run_rows, cell_rows = [], []
for (house, wind, source), items in sorted(groups.items()):
    assert len(items) == 4 and sorted(r['realization'] for r,z in items) == [1,2,3,4]
    mean_wind = np.mean(np.concatenate([z['plume_wind'][z['selected']] for r,z in items]), axis=0)
    axis = int(np.argmax(np.abs(mean_wind[:2])))
    sign = 1 if mean_wind[axis] > 0 else -1
    side = ('x' if axis == 0 else 'y') + ('max' if sign > 0 else 'min')
    source_info = source_map[(house, source)]
    assert source_info['individually_eligible'] and source_info['raw_3d_free'] and source_info['z'] == 0.3
    pass_runs, scores = [], []
    for r,z in items:
        fp = z['footprint'][z['selected']].astype(np.float64)
        assert fp.shape == (31,32,32) and np.isfinite(fp).all() and (fp >= 0).all()
        total = fp.sum(axis=(1,2)); assert (total > 0).all()
        n = protocol['boundary_band_bins']
        if side == 'xmin': edge = fp[:,:,:n].sum(axis=(1,2))
        elif side == 'xmax': edge = fp[:,:,-n:].sum(axis=(1,2))
        elif side == 'ymin': edge = fp[:,:n,:].sum(axis=(1,2))
        else: edge = fp[:,-n:,:].sum(axis=(1,2))
        fraction = edge / total
        width = z['span'][axis] / 32
        centroid = z['raw'][z['selected'],axis]
        lower = z['lo'][axis]; upper = lower + z['span'][axis]
        distance = (upper-centroid if sign>0 else centroid-lower)/width
        source_coord = source_info['x' if axis == 0 else 'y']
        source_clear = (upper-source_coord if sign>0 else source_coord-lower)/width
        mean = float(np.mean(fraction)); q95 = float(np.quantile(fraction,0.95)); margin = float(distance.min())
        ok = bool(mean <= protocol['edge_mass_mean_max'] and q95 <= protocol['edge_mass_q95_max'] and margin >= protocol['centroid_distance_to_dominant_edge_min_bins'] and source_clear >= n and np.linalg.norm(mean_wind[:2]) > 1e-12)
        row = {'house':house,'wind':wind,'source':source,'gas':13,'run_id':r['run_id'],'realization':r['realization'],'dominant_side':side,'mean_edge_mass_fraction':mean,'q95_edge_mass_fraction':q95,'min_centroid_clearance_bins':margin,'source_downwind_clearance_m':float(source_clear*width),'source_downwind_clearance_bins':float(source_clear),'eligible':ok}
        run_rows.append(row); pass_runs.append(ok); scores.append(row)
    cell_rows.append({'house':house,'wind':wind,'source':source,'gas':13,'dominant_side':side,'mean_wind_u':float(mean_wind[0]),'mean_wind_v':float(mean_wind[1]),'mean_wind_w':float(mean_wind[2]),'worst_run_mean_edge_mass_fraction':max(x['mean_edge_mass_fraction'] for x in scores),'worst_run_q95_edge_mass_fraction':max(x['q95_edge_mass_fraction'] for x in scores),'minimum_centroid_clearance_bins':min(x['min_centroid_clearance_bins'] for x in scores),'eligible_realizations':sum(pass_runs),'eligible':all(pass_runs)})

eligible = [x for x in cell_rows if x['eligible']]
selected = []
for house in protocol['allowed_houses']:
    cases = [x for x in eligible if x['house'] == house]
    if cases: selected.append(cases[0])
if len(selected) == 1:
    selected += [x for x in eligible if x != selected[0]][:1]
verdict = 'W0C_STAGE0_NO_CLEAN_BASE_HOLD' if not selected else 'W0C_STAGE0_CLEAN_BASE_AVAILABLE'
write_csv('STAGE0_RUN_BOUNDARY_SCORES.csv', run_rows)
write_csv('STAGE0_CELL_ELIGIBILITY.csv', cell_rows)
write_csv('STAGE0_INPUT_LINEAGE_SHA256.csv', lineage)
write_json('STAGE0_DECISION.json', {'status':verdict,'protocol_sha256':sha(protocol_path),'audit_code_sha256':sha(__file__),'baseline_runs_checked':len(run_rows),'cells_checked':len(cell_rows),'eligible_cells':len(eligible),'selected_cases':selected,'new_simulations':0,'caveat':'Native footprint edge-support is a conservative truncation proxy; it does not estimate actual mass already lost through outflow.'})
print(json.dumps({'status':verdict,'selected':selected,'cells':cell_rows}, indent=2))
