#!/usr/bin/env python3
"""Read-only adapter for *exported* source-blind E2 discovery virtual-probe ppm.

Historical E2 concentrations are NOT bundled with frozen O24. This program
will not read sealed House03 or within-House confirmation arrays. No solver,
GADEN, ROS or truth-conditioned source selection.  E2 fixed panel is not a
Native PMFS adaptive flight and cannot establish a UAV localization gain.

Expected files:
  manifest.csv: run_id,house,wind,source_id,replicate_id,role,
                source_x_m,source_y_m,source_z_m,release_rate,
                release_unit,concentration_unit,forcing_id,
                solver_sha256,operator_sha256,timebase_sha256,
                probe_contract_sha256,data_file,data_sha256
  probes.csv: house,probe_id,x_m,y_m,z_m
  timebase.csv: save_record_id,clock_before_s,active_wind_index,state_stage
  data_file: save_record_id,probe_id,ppm (10*30 rows)
Data must be exporter-verified true GADEN ppm, not O24 2D hit maps.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
import numpy as np

TIMES=(100,150,200,250,300,350,400,450,500,550)
REQ_COLS=('run_id','house','wind','source_id','replicate_id','role','source_x_m','source_y_m','source_z_m','release_rate','release_unit','concentration_unit','forcing_id','solver_sha256','operator_sha256','timebase_sha256','probe_contract_sha256','data_file','data_sha256')

ALLOWED_OPEN_CANONICAL_CONTEXTS = {('House01','1,3-2,4_fast'), ('House02','3,5-1_slow')}  # E2C-R1 canonical discovery contexts ONLY

class ContractFail(ValueError):pass

def sha256_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):h.update(b)
    return h.hexdigest()

def readcsv(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

@dataclass(frozen=True)
class Run:
    run_id:str
    house:str
    wind:str
    source_id:str
    replicate_id:str
    role:str
    source_xyz:tuple[float,float,float]
    release_rate:float
    release_unit:str
    concentration_unit:str
    forcing_id:str
    solver_sha256:str
    operator_sha256:str
    timebase_sha256:str
    probe_contract_sha256:str
    data_file:str
    data_sha256:str


def parse_manifest(path):
    rows=readcsv(path)
    if not rows:raise ContractFail('empty manifest')
    if any(set(REQ_COLS)-r.keys() for r in rows):raise ContractFail('missing manifest fields')
    result=[]; ids=set()
    for r in rows:
        if r['run_id'] in ids:raise ContractFail('duplicated run ID')
        ids.add(r['run_id'])
        try:
            xyz=tuple(float(r[f'source_{v}_m']) for v in 'xyz')
            q=float(r['release_rate'])
        except Exception as e:raise ContractFail('invalid source location or release') from e
        if len(xyz)!=3 or not np.isfinite(xyz).all() or not np.isfinite(q) or q<=0:raise ContractFail('invalid source physical quantities')
        if any(not r[f] for f in ('run_id','house','wind','source_id','replicate_id','role','release_unit','concentration_unit','forcing_id','solver_sha256','operator_sha256','timebase_sha256','probe_contract_sha256','data_file','data_sha256')):
            raise ContractFail('blank provenance field')
        result.append(Run(r['run_id'],r['house'],r['wind'],r['source_id'],r['replicate_id'],r['role'],xyz,q,r['release_unit'],r['concentration_unit'],r['forcing_id'],r['solver_sha256'],r['operator_sha256'],r['timebase_sha256'],r['probe_contract_sha256'],r['data_file'],r['data_sha256']))
    return result


def load_timebase(path):
    t=readcsv(path)
    if tuple(int(x['save_record_id']) for x in t)!=TIMES:raise ContractFail('E2 writer IDs out of order')
    clocks=np.array([float(x['clock_before_s']) for x in t]);wind=np.array([int(x['active_wind_index']) for x in t]);stages=[x['state_stage'] for x in t]
    if not np.isfinite(clocks).all() or not np.all(np.diff(clocks)>0):raise ContractFail('invalid writer timeline')
    if any(s!='POST_MOVE_PRE_WIND_PRE_CLOCK' for s in stages):raise ContractFail('unknown writer stage')
    if tuple(wind.tolist())!=(2,9,6,2,7,2,7,2,7,2):raise ContractFail('E2 frozen wind index sequence mismatch')
    return clocks


def load_probes(path,house):
    rows=[x for x in readcsv(path) if x['house']==house]
    if len(rows)!=30:raise ContractFail('Expected 30 frozen E1 probes for each House')
    probe_ids=[r['probe_id'] for r in rows]
    if len(probe_ids)!=len(set(probe_ids)):raise ContractFail('repeated probe id')
    xyz=np.array([[float(r[k]) for k in ('x_m','y_m','z_m')] for r in rows])
    if not np.isfinite(xyz).all() or not np.allclose(xyz[:,2],0.2,atol=1e-6):raise ContractFail('Invalid z=0.20 E1 probe geometry')
    return probe_ids,xyz


def check_discovery(rows):
    # Must be called before opening any concentration file.
    if any(x.role!='DISCOVERY' for x in rows):
        raise ContractFail('Input manifest contains sealed/confirmation run; provide only OPEN DISCOVERY manifest')
    if any((x.house,x.wind) not in ALLOWED_OPEN_CANONICAL_CONTEXTS for x in rows):raise ContractFail('Context is not on conservative verified OPEN discovery whitelist; sealed/DEV data must not be read')
    if any(x.concentration_unit!='ppm' for x in rows):raise ContractFail('GADEN concentration unit not verified ppm; forbid raw hit/count substitution')
    if len({x.release_unit for x in rows})!=1:raise ContractFail('release unit inconsistent')
    if any(x.release_unit in ('unknown','hit','hit/s','occupancy') for x in rows):raise ContractFail('unqualified release unit')
    if any(x.data_file.startswith('/') or '..' in Path(x.data_file).parts or Path(x.data_file).is_absolute() for x in rows):raise ContractFail('unsafe data path')
    if any(len(x.data_sha256)!=64 or any(ch not in '0123456789abcdef' for ch in x.data_sha256.lower()) for x in rows):raise ContractFail('Missing content hash for concentration export')
    for x in rows:
        for name in ('solver_sha256','operator_sha256','timebase_sha256','probe_contract_sha256'):
            v=getattr(x,name)
            if len(v)!=64 or any(ch not in '0123456789abcdef' for ch in v.lower()):raise ContractFail('Malformed provenance digest '+name)
    groups=defaultdict(list)
    for x in rows:groups[(x.house,x.wind)].append(x)
    for key,rs in groups.items():
        for field in ('forcing_id','solver_sha256','operator_sha256','timebase_sha256','probe_contract_sha256','concentration_unit','release_unit'):
            if len({getattr(x,field) for x in rs})!=1:raise ContractFail(f'Not matched common physics {key}: {field}')
        by_src=defaultdict(list)
        for x in rs:by_src[x.source_id].append(x)
        if len(by_src)<2:raise ContractFail('Need two different physical source responses')
        refrep=None
        for source, ss in by_src.items():
            if len(ss)!=4:raise ContractFail(f'Need four independent replicates for source {source}')
            rr=[x.replicate_id for x in ss]
            if len(set(rr))!=4:raise ContractFail('Repeated replicate identity')
            if len({x.source_xyz for x in ss})!=1:raise ContractFail('Source coordinates drift within reps')
            if len({x.release_rate for x in ss})!=1:raise ContractFail('Source emission drift within reps')
            # Require matched omission view over candidate sources.
            if refrep is None:refrep=set(rr)
            if set(rr)!=refrep:raise ContractFail('Unaligned source replicate indices')
    return groups


def concentration_vector(root,rsrc,probe_ids):
    path=root/rsrc.data_file
    if not path.resolve().is_relative_to(root.resolve()):raise ContractFail('Data file is not inside the qualified discovery export root')
    if not path.is_file():raise ContractFail(f'missing run data: {rsrc.run_id}')
    if sha256_file(path)!=rsrc.data_sha256:raise ContractFail('Exported concentration file SHA256 mismatch')
    rows=readcsv(path)
    if len(rows)!=len(TIMES)*30:raise ContractFail('Expected 300 concentration rows per independent physical realization')
    lookup={};allowed_probes=set(probe_ids)
    for row in rows:
        rec=int(row['save_record_id']);sensor=row['probe_id'];key=(rec,sensor)
        if rec not in TIMES or sensor not in allowed_probes or key in lookup:raise ContractFail('Invalid or duplicate source-blind virtual probe event')
        v=float(row['ppm'])
        if not np.isfinite(v) or v<0:raise ContractFail('Invalid physical ppm; no clipping')
        lookup[key]=v
    if len(lookup)!=300:raise ContractFail('missing receptor-time pairs')
    return np.array([lookup[t,p] for t in TIMES for p in probe_ids],dtype=np.float64)


def whitelisted_bank(manifest_path,probes_path,timebase_path,root):
    runs=parse_manifest(manifest_path)
    groups=check_discovery(runs) # Before reading any values, refuse sealed.
    times=load_timebase(timebase_path)
    timehash=sha256_file(timebase_path);probehash=sha256_file(probes_path)
    if any(x.timebase_sha256!=timehash for x in runs):raise ContractFail('E2 writer timeline bytes SHA256 mismatch')
    if any(x.probe_contract_sha256!=probehash for x in runs):raise ContractFail('E1 probe contract bytes SHA256 mismatch')
    matrices={};metas={}
    for (house,wind),rs in groups.items():
        probe_ids,xyz=load_probes(probes_path,house)
        rr=defaultdict(dict)
        for x in rs:
            if x.replicate_id in rr[x.source_id]:raise ContractFail('Duplicate realization')
            rr[x.source_id][x.replicate_id]=(concentration_vector(root,x,probe_ids),x)
        matrices[(house,wind)]=rr
        metas[(house,wind)]={'house':house,'wind':wind,'probes':len(probe_ids),'records':len(times),'writer_clocks_s':times.tolist(),'probe_xyz_m':xyz.tolist()}
    return matrices,metas


def mse_rankings(bank,sigma_ppm):
    if not np.isfinite(sigma_ppm) or sigma_ppm<=0:raise ContractFail('sigma from calibrated sensor must be positive')
    outcomes=[]
    for (house,wind),all_sources in sorted(bank.items()):
        sources=sorted(all_sources)
        reps=sorted(all_sources[sources[0]])
        for omit in reps:
            refs=[];source_xyz=[];ref_ids=[]
            for sid in sources:
                other=[(v,meta) for rep,(v,meta) in sorted(all_sources[sid].items()) if rep!=omit]
                if len(other)!=3:raise ContractFail('Target omission incomplete')
                refs.append(np.mean([v/meta.release_rate for v,meta in other],axis=0)); source_xyz.append(other[0][1].source_xyz);ref_ids.extend([x[1].run_id for x in other])
            K=np.column_stack(refs)
            # For each held-out truth source, never include its test realization
            # in ANY candidate reference (including wrong candidates).
            for truth in sources:
                y,tm=all_sources[truth][omit]
                if tm.run_id in ref_ids:raise AssertionError('target leak')
                emission=tm.release_rate
                mu=K*emission
                fixed_loss=((mu-y[:,None])**2).sum(axis=0)/(2*sigma_ppm**2)
                pK=np.maximum(0,K.T@y)
                den=(K*K).sum(axis=0)
                q=np.divide(pK,den,out=np.zeros_like(pK),where=den>0)
                profile_loss=((K*q-y[:,None])**2).sum(axis=0)/(2*sigma_ppm**2)
                # Ordinary E1-type marginal Brier on B=1[ppm>0].
                bp=np.column_stack([np.mean([np.array(v)>0 for r,(v,m) in sorted(all_sources[sid].items()) if r!=omit],axis=0) for sid in sources])
                brier=((bp-(y>0)[:,None])**2).mean(axis=0)
                for method,loss in [('ordinary_fixed_emission_Gaussian',fixed_loss),('ordinary_nonnegative_emission_profile_Gaussian',profile_loss),('ordinary_binary_marginal_Brier',brier)]:
                    idx=int(np.argmin(loss));truth_idx=sources.index(truth); order=np.argsort(loss)
                    outcomes.append({'house':house,'wind':wind,'true_source':truth,'test_replicate':omit,
                        'method':method,'pred_source':sources[idx],'is_top1_correct':int(idx==truth_idx),
                        'truth_rank':int(np.where(order==truth_idx)[0][0])+1,
                        'n_candidate_sources':len(sources),'n_observations':len(y),
                        'target_run_id':tm.run_id,'candidate_ref_realization_count_per_source':3,
                        'target_in_candidate_refs':False,
                        'no_probes_selected_using_source_truth':True,
                        'requires_counterfactual_source_plumes':True,
                        'reported_unit':'ppm', 'calibration_sigma_ppm':sigma_ppm,
                        'not_Native_PMFS_closed_loop':True})
    return outcomes


def main():
    ap=argparse.ArgumentParser()
    for key in ('manifest','probes','timebase','root','out'):ap.add_argument('--'+key,required=True,type=Path)
    ap.add_argument('--sigma-ppm',type=float,required=True,
                    help='Must be external sensor-calibration value, NOT fitted on targets. If unknown, do not claim calibrated posterior.')
    a=ap.parse_args();banks,info=whitelisted_bank(a.manifest,a.probes,a.timebase,a.root)
    rows=mse_rankings(banks,a.sigma_ppm)
    summary=[]
    for method in sorted({r['method'] for r in rows}):
        for house in sorted({r['house'] for r in rows}):
            rr=[r for r in rows if r['method']==method and r['house']==house]
            summary.append({'house':house,'method':method,'n_trials':len(rr),'n_sources':len(set(x['true_source'] for x in rr)),
                            'top1_correct':sum(r['is_top1_correct'] for r in rr),
                            'median_truth_rank':float(np.median([r['truth_rank'] for r in rr]))})
    out={'status':'E2_OPEN_DISCOVERY_FIXED_PROBE_ORDINARY_BASELINES_ONLY',
         'groups':list(info.values()),'trials':rows,'summary':summary,
         'scientific_limits':['Not native PMFS adaptive-trajectory input/output','Frozen O24 A is not directly comparable without same data contract','Reference and target are different stochastic realizations under the same external condition','No source-unseen generalization demonstrated by LOO realization','No B train or physical-world reconstruction','No sealed House03 read','No posterior calibration without validated sensor noise and release model']}
    a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'status':out['status'],'summary':summary},ensure_ascii=False))
if __name__=='__main__':main()
