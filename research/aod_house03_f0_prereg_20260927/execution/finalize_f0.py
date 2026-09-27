#!/usr/bin/env python3
"""Finalize frozen manifests and hashes; do not execute scientific work."""
from pathlib import Path
import csv,hashlib,json,subprocess,sys
W=Path(__file__).resolve().parents[3]
R=W/'research/aod_house03_f0_prereg_20260927';E=W/'evidence/aod_house03_f0_prereg_20260927'
BASE='25803d287aa299f78a06458e37437a91c3fa3890'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=W,text=True).strip()
def table(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def main():
    assert git('rev-parse','HEAD')==BASE
    assert git('branch','--show-current')=='research/aod-house03-f0-prereg-20260927'
    assert not git('diff',BASE,'--','research/amplitude_operator_decoupling_v0','research/marked_encounter_pmfs_d0')
    verify=json.loads((E/'INDEPENDENT_F0_VERIFICATION.json').read_text());assert verify['passed']
    source=json.loads((E/'SOURCE_PANEL_SELECTION_LOG.json').read_text());path=json.loads((E/'PATH_FREEZE_AUDIT.json').read_text());wind=json.loads((E/'inputs/WIND_ASSET_AUDIT.json').read_text());seeds=json.loads((E/'FUTURE_SEED_MANIFEST_AUDIT.json').read_text())
    rows=[]
    for r in wind['states']:
        rows.append({k:r[k] for k in ['state','csv_path','csv_bytes','csv_sha256','preprocessed_path','preprocessed_bytes','preprocessed_sha256']})
    with (E/'HOUSE03_WIND_HASHES_11.tsv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
    preserved={}
    for name in ['research/amplitude_operator_decoupling_v0/amplitude_readout.py','research/marked_encounter_pmfs_d0/execution/marked_forward.cpp','research/marked_encounter_pmfs_d0/execution/Simulations_marked.cpp']:
        p=W/name;assert p.is_file();preserved[name]=dict(working_file_sha256=sha(p),base_git_blob=git('rev-parse',BASE+':'+name),working_git_blob=git('hash-object',name))
        assert preserved[name]['base_git_blob']==preserved[name]['working_git_blob']
    result=dict(decision='AOD_H03_F0_READY_FOR_PREREG',branch=git('branch','--show-current'),base_commit=BASE,final_commit_record='see post-commit GIT_STATE.json in review ZIP',source_count=12,pair_count=6,source_panel=source['selection_log'],minimum_pair_center_separation_m=source['minimum_pair_center_separation_m'],path_A=path['paths']['A'],path_B=path['paths']['B'],path_overlap=path['overlap_count'],navigation_speed_m_s=path['navigation_speed_m_s'],wind_family='1-2,5_fast',wind_state_count=11,wind_hashes_file='HOUSE03_WIND_HASHES_11.tsv',wind_hashes_sha256=sha(E/'HOUSE03_WIND_HASHES_11.tsv'),future_seed_manifest_hashes=seeds['hashes'],future_gaden_realizations=96,future_pmfs_forwards=1056,source_bank_sha256=sha(E/'HOUSE03_CANONICAL_SOURCE_GEOMETRY_BANK_624.tsv'),source_panel_sha256=sha(E/'HOUSE03_F1_SOURCE_PANEL_12.tsv'),path_hashes={p.name:sha(p) for p in [E/'HOUSE03_PATH_A_10.tsv',E/'HOUSE03_PATH_B_10.tsv']},independent_verification_passed=True,implementation_preserved=preserved,fresh_gaden_generated=0,scientific_pmfs_forwards_executed=0,house03_gas_arrays_opened=0,source_scores_computed=0,F1_authorized=False,F1_required_timebase_binding='Bind frozen relative slots 50,100,...,500 seconds to physical simulator timestamps and sufficient generation duration; do not reuse legacy frame indices as seconds or the 300-second generation duration without explicit F1 configuration.')
    (E/'F0_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# AOD House03 F0 freeze report','', '**Decision: AOD_H03_F0_READY_FOR_PREREG**','',f'Branch: `{result["branch"]}`',f'Base: `{BASE}`','Final commit: recorded after committing in review ZIP `GIT_STATE.json`.','',f'Source panel: 12 sources, 6 disjoint 0.30 m neighbour pairs. Minimum pair-center spacing: {result["minimum_pair_center_separation_m"]:.12f} m.','', '| Pair | Source A | Source B |','| --- | --- | --- |']
    for r in source['selection_log']:lines.append(f'| {r["pair_id"]} | {r["source_a"]} | {r["source_b"]} |')
    lines+=['','## Paths','',f'Nominal speed: {path["navigation_speed_m_s"]:.6f} m/s. Start: (2,0). Slot: 50 s. Dwell: 3 s. Allowed travel: 47 s.','', '| Path | Ordered probe ranks | Route distance | Maximum segment travel |','| --- | --- | --- | --- |']
    for k in ['A','B']:
        p=path['paths'][k];lines.append(f'| {k} | '+', '.join(map(str,p['ordered_probe_ranks']))+f' | {p["total_route_distance_m"]:.9f} m | {p["max_segment_travel_time_s"]:.9f} s |')
    lines+=['',f'Path overlap: {path["overlap_count"]}. Full xyz, per-segment metric distances and timings are in the two path TSVs. Cell routes are in `PATH_SEGMENT_GEOMETRY.json`.','', '## Wind and future seeds','', 'Family: `1-2,5_fast`; 11 states. CSV and preprocessed GADEN hashes are both recorded in `HOUSE03_WIND_HASHES_11.tsv`.','', 'Nominal: equal 1/11 state weights, 8 replicas per state. Mismatch: state0 only, using the same 8 state0 replicas from the nominal bank.','', 'Future GADEN manifest: 96 rows. Future PMFS manifest: 1056 rows. All seeds are deterministic, positive, unique and domain-separated. Nothing has been executed.','']
    for k,v in seeds['hashes'].items():lines.append(f'- `{k}`: `{v}`')
    lines+=['','## F1 timebase must be signed','',result['F1_required_timebase_binding'],'', 'The historical acquisition code has `sim_time=300.0` and `results_time_step=0.5`. It is archived as provenance, not adopted as a finalized future configuration. F0 keeps the supplied 50-second path budget and leaves physical snapshot binding to the final F1 preregistration.','', '## Stop boundary','', 'No fresh GADEN plume, no PMFS scientific forward, no House03 gas array, no source score, no D1 rerun, and no F1 execution. The unchanged amplitude/B2/Native implementation is preserved at the stated base.','']
    (E/'F0_FREEZE_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    files=sorted(p for folder in [R,E] for p in folder.rglob('*') if p.is_file() and p.name!='F0_SHA256SUMS.txt')
    (E/'F0_SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(W).as_posix()}\n' for p in files),encoding='utf-8')
    for line in (E/'F0_SHA256SUMS.txt').read_text().splitlines():h,n=line.split('  ',1);assert sha(W/n)==h
    print(json.dumps(dict(decision=result['decision'],hashed_final_files=len(files),wind_hash_manifest_sha256=result['wind_hashes_sha256'],source_panel_sha256=result['source_panel_sha256']),indent=2))
if __name__=='__main__':main()
