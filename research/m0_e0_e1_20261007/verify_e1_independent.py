"""Independent numerical/checksum qualification using the same eight raw runs.

No simulator. Gaussian bands use stable erfc union bounds. Classification uses
closed-form two-candidate odds and manual variance rather than primary routines.
"""
from pathlib import Path
import csv,hashlib,json,math
import numpy as np
from scipy.special import erfc
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';D=R/'evidence'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rows(p,delimiter=','):
    with Path(p).open(encoding='utf-8') as f:return list(csv.DictReader(f,delimiter=delimiter))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for q in rows(F/'M0_R0_FILES_SHA256.csv'):assert sha(F/q['path'])==q['sha256']
for q in rows(D/'NATIVE_ALL_FILES_SHA256.csv'):assert sha(D/q['path'])==q['sha256'] and (D/q['path']).stat().st_size==int(q['bytes'])
seal=read(R/'E1_EXECUTION_SEAL.json')
for name,value in seal['scripts_sha256'].items():assert sha(R/name)==value and sha(D/name)==value,(name,'pre-run source drift')
assert read(D/'E1_PROGRESS.json')['completed']==8 and read(D/'E1_PROGRESS.json')['intervention_runs']==0
summ=rows(R/'E1_BASELINE_SUMMARY.csv');pred=rows(R/'E1_U0_LORO.csv');domain=read(F/'M0_DOMAIN_ROI_GUARD_CONTRACT.json');E0=read(D/'E0_QUALIFICATION.json')
lo=np.array(domain['effective_outlet_inner_planes_m']['min']);hi=np.array(domain['effective_outlet_inner_planes_m']['max']);obs={};stable_upper_rows=[];difftop=0.;p_diff=0.;relevance_diff=0.
for q in summ:
    rid=q['run_id'];folder=D/'e1_audit'/rid;frames=rows(folder/'native_frames.csv');data=np.fromfile(folder/'filament_states.f32',dtype='<f4').reshape(-1,4)
    for checksum in rows(folder/'RAW_OUTPUT_SHA256.csv'):
        assert sha(D/checksum['path'])==checksum['sha256']
    assert all(int(f['wind_index'])==0 for f in frames);assert len(frames)==246
    assert float(q['band_mean'])<=.05 and float(q['band_q95'])<=.10 and float(q['min_record_3sigma_margin_m'])>=1 and int(q['deletion_count_certified'])==0
    assert q['sigma_age_order_bit_identity']=='True' and q['native_position_exceptions']=='False'
    onseries=[];offseries=[];bounds=[];times=[];worst_margin=math.inf
    for f in frames:
        start=int(f['offset_filaments']);n=int(f['n_filaments']);a=data[start:start+n].astype(float);xyz=a[:,:3];sigma=a[:,3,None]/100
        margins=np.minimum(xyz-lo,hi-xyz)-3*sigma;worst_margin=min(worst_margin,float(margins.min()));times.append(float(f['time_s']))
        # Stable tail probabilities, unlike subtraction of two near-one CDF boxes.
        outer_tail=.5*erfc((xyz-lo)/(sigma*math.sqrt(2)))+.5*erfc((hi-xyz)/(sigma*math.sqrt(2)))
        inset_tail=.5*erfc((xyz-(lo+1))/(sigma*math.sqrt(2)))+.5*erfc(((hi-1)-xyz)/(sigma*math.sqrt(2)))
        bounds.append(float(inset_tail.sum(axis=1).mean()/(1-outer_tail.sum(axis=1).mean())))
        def box(bl,bh):
            # erf-based CDF difference expressed as erfc, independent from ndtr.
            diff=.5*(erfc((np.array(bl)-xyz)/(sigma*math.sqrt(2)))-erfc((np.array(bh)-xyz)/(sigma*math.sqrt(2))))
            return float(np.prod(diff,axis=1).mean())
        onseries.append(box([0,-2,2],[12,2,8]));offseries.append(box([0,3.5,2],[12,7.5,8]))
    selected=[max(i for i,t in enumerate(times) if t<=requested) for requested in range(20,121,2)]
    on=np.array(onseries)[selected];off=np.array(offseries)[selected];upper=np.array(bounds)[selected]
    assert upper.mean()<=.05 and np.quantile(upper,.95,method='linear')<=.10 and on.mean()>=.30 and off.mean()<=.01 and np.quantile(off,.95,method='linear')<=.05
    relevance_diff=max(relevance_diff,abs(on.mean()-float(q['PairA_on_mean'])),abs(off.mean()-float(q['PairA_off_mean'])));difftop=max(difftop,abs(worst_margin-float(q['min_record_3sigma_margin_m'])))
    stable_upper_rows.append({'run_id':rid,'stable_all6_band_mean_upper_bound':float(upper.mean()),'stable_all6_band_q95_upper_bound':float(np.quantile(upper,.95,method='linear')),'max_all_saved_frame_band_upper_bound':max(bounds)})
    route=rows(folder/'route.csv');obs[(q['source_id'],int(q['realization']))]=np.array([float(s['ppm']) for s in route]);assert sum(float(s['ppm'])>=.1 for s in route)==int(q['route_detectable_samples'])
    parity=rows(folder/'sampling_parity.csv');assert len(parity)==2550 and max(float(s['absolute_difference']) for s in parity)==0
for row in pred:
    s=row['source_id'];r=int(row['realization']);train=[k for k in range(1,5) if k!=r];query=obs[(s,r)];scores=[]
    for cand in ['S0','S1']:
        arrays=[obs[(cand,k)] for k in train]
        if row['family']=='HIT_FORWARD':
            likelihood=[(sum(a[i]>=.1 for a in arrays)+.5)/4 for i in range(51)]
            score=sum(math.log(p if query[i]>=.1 else 1-p) for i,p in enumerate(likelihood))
        else:
            score=0
            for i in range(51):
                vals=[math.log1p(float(a[i])) for a in arrays];mu=sum(vals)/3;variance=max(sum((z-mu)**2 for z in vals)/2,.0625);z=math.log1p(float(query[i]));score-=.5*(math.log(2*math.pi*variance)+(z-mu)**2/variance)
        scores.append(score)
    delta=scores[1]-scores[0];p0=1/(1+math.exp(delta)) if delta<700 else 0.;p1=1-p0;truth=0 if s=='S0' else 1;p=[p0,p1];p_diff=max(p_diff,abs(p0-float(row['p_S0'])),abs(p1-float(row['p_S1'])));assert p[truth]>=.60 and np.argmax(p)==truth
assert difftop<1e-12 and relevance_diff<1e-12 and p_diff<1e-12
# All numeric and implementation guards must resolve to the frozen baseline-qualified verdict.
decision=read(R/'E1_DECISION.json');assert decision['verdict']=='M0_E1_BASELINE_QUALIFIED' and decision['actual_wrong_wind_runs']==0 and decision['all_failures']==[]
report={'status':'INDEPENDENT_E1_VERIFICATION_PASS','U0_runs_verified':8,'wrong_wind_runs':0,'native_files_verified':len(rows(D/'NATIVE_ALL_FILES_SHA256.csv')),'R0_frozen_files_verified':39,'max_margin_difference_m':difftop,'max_relevance_mean_difference':relevance_diff,'max_LORO_posterior_difference':p_diff,'stable_Gaussian_band_upper_bounds':stable_upper_rows,'band_zero_interpretation':'Primary float64 CDF subtraction reports numerical zero; stable erfc bounds are tiny positive values, not a claim of exact physical zero Gaussian tail mass.','scientific_M0_verdict':'NOT_TESTED','E2_authorized':False}
(R/'INDEPENDENT_E1_VERIFICATION.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report,indent=2))
