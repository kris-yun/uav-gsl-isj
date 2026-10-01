"""Read-only R1 asset audit. No plume, forward, ranking or training calls."""
import argparse,csv,hashlib,json,math,re,shutil
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument('--root',type=Path,default=Path('/mnt/hgfs/workspace/TNQC_R2_SIX_OFFLINE_20260921_authoritative/native'))
ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args()
def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cases=[]; declared=json.loads((a.root.parent/'SHA256SUMS.json').read_text())
for house in ('House01','House02'):
    for seed in (0,1):
        p=a.root/f'{house}_seed{seed}_off_off'
        runtime=json.loads((p/'runtime_manifest.json').read_text())
        bank=p/'context_bank'; timing=rows(bank/'source_update_timing.csv')
        terminal=max((r for r in timing if float(r['sim_time'])<=300+1e-9),key=lambda r:(float(r['sim_time']),int(r['source_update_id'])))
        snap=bank/f"source_update_{int(terminal['source_update_id']):04d}"
        candidates=rows(snap/'candidate_manifest.csv')
        cells=[r for r in rows(snap/'measured_hit_probability.csv') if r['occupancy']=='Free']
        active=set()
        for cell in cells:
            i,j=int(cell['grid_i']),int(cell['grid_j'])
            covers=[r for r in candidates if int(r['origin_i'])<=i<int(r['origin_i'])+int(r['size_i']) and int(r['origin_j'])<=j<int(r['origin_j'])+int(r['size_j'])]
            assert covers, (house,seed,cell)
            owner=min(covers,key=lambda r:(int(r['size_i'])*int(r['size_j']),r['candidate_id']))
            active.add(owner['candidate_id'])
        alignment=rows(snap/'candidate_support_alignment.csv')
        per_candidate={r['candidate_id']:[] for r in candidates}
        measured={int(r['cell_index']):r for r in cells}
        for row in alignment:
            if int(row['cell_index']) in measured:
                per_candidate[row['candidate_id']].append(row)
        parameters={}
        for file in sorted((p/'resolved_runtime').glob('launch_params_*')):
            for line in file.read_text().splitlines():
                match=re.match(r'\s+([A-Za-z_][A-Za-z_0-9]*):\s*(.*?)\s*$',line)
                if match and match[1] in ('useWindGroundTruth','sourceDiscriminationPower','noiseSTDev','deltaTime','iterationsToRecord','maxWarmupIterations','minWarmupIterations','blurSigmaX','blurSigmaY','ground_truth_x','ground_truth_y','ground_truth_z','flight_z','data_folder','gas_simulation','gas_data_dir'):
                    parameters[match[1]]=match[2]
        power=float(parameters['sourceDiscriminationPower'])
        scores={}
        for cid,values in per_candidate.items():
            assert values, cid
            factors=[1-float(r['measured_confidence'])*abs(float(r['measured_probability'])-float(r['simulated_hit_probability']))*power for r in values]
            assert all(f>0 and math.isfinite(f) for f in factors)
            scores[cid]=sum(math.log(f) for f in factors)
        partition={}
        for cell in cells:
            i,j=int(cell['grid_i']),int(cell['grid_j'])
            covers=[r for r in candidates if int(r['origin_i'])<=i<int(r['origin_i'])+int(r['size_i']) and int(r['origin_j'])<=j<int(r['origin_j'])+int(r['size_j'])]
            partition[int(cell['cell_index'])]=min(covers,key=lambda r:(int(r['size_i'])*int(r['size_j']),r['candidate_id']))['candidate_id']
        peak=max(scores[cid] for cid in partition.values())
        probabilities={idx:math.exp(scores[cid]-peak) for idx,cid in partition.items()}
        total=sum(probabilities.values()); probabilities={idx:value/total for idx,value in probabilities.items()}
        exported={int(r['cell_index']):float(r['source_probability']) for r in rows(snap/'source_posterior.csv')}
        total_export=sum(exported.values()); exported={idx:value/total_export for idx,value in exported.items()}
        differences=[abs(probabilities.get(idx,0)-exported.get(idx,0)) for idx in set(probabilities)|set(exported)]
        parity={'max_abs':max(differences),'l1':sum(differences),'pass':max(differences)<1e-10,
                'comparison':'exact Native scorer and sourceProbability reconstruction, no new source-rank outcome'}
        assert parity['pass'], parity
        files=[]
        for file in sorted(p.iterdir()):
            if file.is_file(): files.append({'path':str(file),'bytes':file.stat().st_size,'sha256':sha(file)})
        snapshot_files=[]
        for file in sorted(snap.iterdir()):
            if file.is_file(): snapshot_files.append({'path':str(file),'bytes':file.stat().st_size,'sha256':sha(file)})
        record={'case':p.name,'root':str(p),'runtime':runtime,'terminal':terminal,
                'context_contract':json.loads((bank/'context_bank_contract.json').read_text()),
                'evaluated_candidates':len({r['candidate_id'] for r in candidates}),
                'active_leaf_count':len(active),'free_cell_count':len(cells),
                'map_file_count':len(list((snap/'candidate_maps').iterdir())),
                'files':files,'snapshot_files':snapshot_files,
                'snapshot_headers':{name:rows(snap/name)[:1] for name in ('candidate_manifest.csv','candidate_support_alignment.csv','estimated_wind.csv','measured_hit_probability.csv')},
                'trace_headers':{name:rows(p/name)[:1] for name in ('sensor_trace.csv','wind_trace.csv','sim_pose_trace.csv') if (p/name).is_file()}}
        record['resolved_parameters']=parameters; record['native_posterior_parity']=parity
        selected=[p/'runtime_manifest.json',p/'sensor_trace.csv',p/'wind_trace.csv',p/'sim_pose_trace.csv',bank/'source_update_timing.csv',bank/'context_bank_contract.json']
        selected += [f for f in snap.iterdir() if f.is_file()]
        selected += list((p/'resolved_runtime').glob('launch_params_*'))
        verified=[]
        for file in selected:
            relative=file.relative_to(a.root.parent).as_posix()
            assert relative in declared, relative
            assert sha(file)==declared[relative], relative
            dest=a.out.parent/'frozen_inputs'/file.relative_to(a.root)
            dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(file,dest)
            verified.append({'original':str(file),'archive_relative':relative,'sha256':sha(file),'bytes':file.stat().st_size})
        record['historical_manifest_verified_inputs']=verified
        record['active_candidates']=[r for r in candidates if r['candidate_id'] in active]
        cases.append(record)
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps({'cases':cases,'scientific_scoring_executed':False},indent=2,sort_keys=True)+'\n')
for case in cases:
    print(json.dumps({k:case[k] for k in ('case','terminal','evaluated_candidates','active_leaf_count','free_cell_count','map_file_count','resolved_parameters','native_posterior_parity')},indent=2))
