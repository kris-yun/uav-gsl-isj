"""Metadata/raw-byte audit and prospective replay manifest; no plume generation."""
import csv,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=Path('D:/ZYC/A-gas/_worktrees/ocb-r2-census-20260930')
ARCH=Path('C:/GADEN_OCB_R2_ARCHIVE')
OUT=ROOT/'freeze'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def main():
    OUT.mkdir(exist_ok=True)
    files=[REPO/'evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv',REPO/'evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv']
    data=[]
    for phase,p,sub in zip(['S2','S2X'],files,['s2_discovery','s2x_matched_source']):
        for r in rows(p):
            leaf=ARCH/sub/r['run_id'];manifest=json.loads((leaf/'RUN_MANIFEST.json').read_text())
            assert manifest['run_id']==r['run_id'] and manifest['house']==r['house']
            assert manifest['master_seed']==int(r['master_seed'])
            assert manifest['generator_binary_sha256']=='ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
            assert manifest['house'] in ('House01','House02')
            pars=manifest['simulation_parameters'];source=[float(pars['source_position_'+a]) for a in 'xyz']
            assert source==[float(r['source_'+a]) for a in 'xyz']
            timeline=rows(leaf/'RECORD_TIMELINE.tsv')
            assert len(timeline)==1803 and float(timeline[0]['internal_simulation_time_s'])==0
            assert all(float(a['internal_simulation_time_s'])<float(b['internal_simulation_time_s']) for a,b in zip(timeline,timeline[1:]))
            # Verify raw bytes against original inventory, without decoding scientific values.
            inventory=rows(leaf/'OUTPUT_SHA256SUMS.tsv')
            assert len(inventory)==1803
            for item in inventory:
                raw=leaf/item['name'];assert raw.stat().st_size==int(item['size_bytes'])
                assert sha(raw)==item['sha256'],raw
            idx=int(r['config_index'] if phase=='S2' else r['parent_s2_config_index'])
            start=[-3.17,-1.75] if r['house']=='House01' else [-.5,-2.5]
            data.append(dict(run_id=r['run_id'],phase=phase,house=r['house'],context=f'X{idx:02d}',
                source_id=r['source_id'],source_x=source[0],source_y=source[1],source_z=source[2],
                replicate=int(r['run_id'].rsplit('_r',1)[1]),master_seed=r['master_seed'],wind_id=r['wind_id'],
                gas_type=pars['gas_type'],archive_path=str(leaf),run_manifest_sha256=sha(leaf/'RUN_MANIFEST.json'),
                raw_inventory_sha256=sha(leaf/'OUTPUT_SHA256SUMS.tsv'),timeline_sha256=sha(leaf/'RECORD_TIMELINE.tsv'),
                generator_sha256=manifest['generator_binary_sha256'],occupancy_sha256=manifest['asset_checks']['occupancy_sha256'],
                start_x=start[0],start_y=start[1],flight_height_m=.3,nav_seed=0,budget_s=300.,
                role='DISCOVERY_ONLY',native_result='NOT_RUN'))
    assert len(data)==64 and len({r['run_id'] for r in data})==64
    # Four source-blind fixed cases: both Houses, both configured sources, fast and slow.
    smoke=['ocb_r2_cfg00_r01','ocb_r2_cfg03_r01','ocb_r2_cfg04_r01','ocb_r2_cfg07_r01']
    with (OUT/'D1A_RUNLIST_64.tsv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(data)
    (OUT/'D1A_SMOKE_RUNLIST_4.json').write_text(json.dumps(dict(run_ids=smoke,modes=['off','on'],budget_s=300,
        reuse_on_runs_in_campaign_if_pass=True,retry_on_scientific_failure=False),indent=2)+'\n')
    report=dict(decision='D1A_DISCOVERY_ARCHIVE_IDENTITY_PASS',runs=64,raw_records_verified=64*1803,
        runlist_sha256=sha(OUT/'D1A_RUNLIST_64.tsv'),input_manifests={str(p):sha(p) for p in files},
        concentration_decoded=False,confirmation_read=False,house03_read=False,new_gaden=0,
        windows_free_bytes=shutil.disk_usage(ARCH).free,outputs_location='C:/GADEN_OCB_R2_ARCHIVE/d1a_native_common_replay',
        early_native_stop='preserve variance declaration; final available belief at/before300, no forced continuation',
        scientific_run_authorization='four ON/OFF pairs then remaining60 ON only if all frozen gates PASS')
    (OUT/'D1A_ARCHIVE_AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
