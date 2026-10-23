"""Read-only original M1 audit; exact counterexamples, no replacement fitting."""
import itertools,json
import numpy as np
from common import PROJECT,OUT,write,sha
from gsl_discrimination.m1_opponent.raw_joint import load_observation_model
from gsl_discrimination.m1_opponent.calibration import _js
from gsl_discrimination.data import SynchronousBlock

def main():
    old=PROJECT/'results/native_20261023';model=load_observation_model(old/'models/secondary')
    r1=json.loads((old/'R1_EXTRACTION_RESULT.json').read_text());rows=[]
    for r in r1['blocks']:
        if r['split']!='train':continue
        b=SynchronousBlock.load_npz(old/r['path'])
        e,h=model.bank.extract(b.values,b.times_s,model.contract)
        rows.append({'world_id':r['run_id'],'source':r['source_id'],'even':float(e),
             'static_odd':float(h[0]),'encoded_symbol':int(model.encode(0,b.values,b.times_s)),
             'left_all_zero':bool(np.all(b.values[:,0]==0)),'right_all_zero':bool(np.all(b.values[:,1]==0)),
             'threshold':float(model.even_thresholds[0]),
             'all_coarse_cues':h.tolist()})
    null_cases=[]
    for bits in itertools.product((0,1),repeat=4):
        ka=sum(bits[:2]);kb=sum(bits[2:])
        pa=np.array([2-ka+.5,ka+.5])/3;pb=np.array([2-kb+.5,kb+.5])/3
        js=float(_js(pa,pb))
        null_cases.append({'four_independent_null_world_bits':list(bits),'js':js,'target_saturated':js>=.04})
    # Algebraic loss, not a new gas experiment: source A remains right-only,
    # B remains left-only, while common intensity changes between worlds.
    train=np.array([[[0,1],[0,2]],[[3,0],[4,0]]],float)
    y=np.log1p(train);even=y.mean(-1);threshold=float(np.median(even))
    symbols=(even>threshold).astype(int)
    probabilities=np.array([np.bincount(z,minlength=2)+.5 for z in symbols])/3
    dev=np.array([[0,8],[8,0]],float);de=np.log1p(dev).mean(-1)
    dcode=(de>threshold).astype(int)
    prediction=np.argmax(probabilities[:,dcode],axis=0)
    result={'status':'READONLY_ORIGINAL_M1_STRUCTURE_AUDIT_COMPLETE','original_model_sha256':sha(old/'models/secondary/operator.json'),
       'unchanged_coverage_target':.04,'selection':model.selection,
       'original_train_receipt':model.receipt,'training_rows':rows,
       'exact_null_model':{'description':'each of two sources has two independent world-level Bernoulli(0.5) observations, identical source laws; frozen total smoothing alpha=1',
          'enumerated_cases':len(null_cases),'false_saturation_cases':sum(c['target_saturated'] for c in null_cases),
          'probability_of_saturation_in_this_constructed_null':sum(c['target_saturated'] for c in null_cases)/16,
          'scope':'mathematical finite-sample counterexample, not a measured GADEN false-positive rate','cases':null_cases},
       'common_intensity_loss_counterexample':{'training_readings':train.tolist(),'training_even':even.tolist(),
          'threshold':threshold,'training_symbols':symbols.tolist(),'training_js':float(_js(*probabilities)),
          'new_constructed_readings':dev.tolist(),'new_common_symbols':dcode.tolist(),'predicted_sources':prediction.tolist(),
          'true_sources':[0,1],'opposite_side_information_retained_in_raw_pair':True,
          'dynamic_information_required':False,'scope':'constructed amplitude-shift illustration, not another gas-world result'},
       'separated_findings':{'easy_source_task':'ordinary single point already solved original frozen pair',
          'small_sample_JS':'point estimate has no world-generalization coverage certificate',
          'saturation':'one-pair clipped sum is already at its global maximum, so no additional filter can improve objective',
          'quantization':'even-only one-bit map is many-to-one and discards left/right side; histogram can also tie on unseen symbols',
          'dynamic_necessity':'not established by the previous pair; this audit does not fit a new dynamic model'},
       'no_modified_threshold_or_M1_training':True,'no_new_DEV_read':True}
    write('M1_STRUCTURE_AUDIT.json',result)
    print('M1_STRUCTURE_AUDIT','null_saturation',result['exact_null_model']['false_saturation_cases'],'of16')

if __name__=='__main__':main()
