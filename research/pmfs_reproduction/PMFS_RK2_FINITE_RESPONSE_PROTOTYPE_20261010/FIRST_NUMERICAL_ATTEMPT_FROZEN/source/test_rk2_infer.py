"""Independent infer information-contract software tests; no physical queries."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from rk2_infer import ForecastCandidate, ForecastSet, ObservationSeries, infer, load_forecasts, load_observation, load_forecast_npz, load_observation_json, infer_files

def canonical(result):
    result = dict(result)
    result['candidates'] = sorted(result['candidates'], key=lambda c:c['candidate_id'])
    return json.dumps(result, sort_keys=True, separators=(',',':'))

def check_renaming(before, after, inverse):
    a = {c['candidate_id']:c for c in before['candidates']}
    b = {inverse[c['candidate_id']]:c for c in after['candidates']}
    assert set(a)==set(b)
    for key in a:
        for field in ['reference_events','probability_by_block','observed_events','mean_Bernoulli_log_score','mean_Brier','source_probability','physical_source_xyz']:
            x, y = a[key][field], b[key][field]
            if isinstance(x, (int,float)):
                assert abs(x-y)<=1e-15,(key,field,x,y)
            else:
                assert x==y,(key,field)
    assert set(before['top1_candidate_ids'])=={inverse[k] for k in after['top1_candidate_ids']}

def directory_oracle_checks(reference_dir, observation_dir, hidden_files=(), truth_files=()):
    """Actual directory test reusable on frozen scalar forecast/observation assets.

    Deletion is limited to explicitly named temporary hidden/truth fixture files.
    The runner is responsible for placing these in a new isolated test directory.
    """
    reference_dir, observation_dir = Path(reference_dir), Path(observation_dir)
    baseline = infer(load_forecasts(reference_dir), load_observation(observation_dir))
    for path in hidden_files:
        Path(path).unlink()
    without_hidden = infer(load_forecasts(reference_dir), load_observation(observation_dir))
    if canonical(baseline)!=canonical(without_hidden):
        raise AssertionError('infer changed when hidden state files were removed')
    for path in truth_files:
        Path(path).unlink()
    without_truth = infer(load_forecasts(reference_dir), load_observation(observation_dir))
    if canonical(baseline)!=canonical(without_truth):
        raise AssertionError('infer changed when true-source mappings were removed')
    forecast = load_forecasts(reference_dir)
    renamed = []
    inverse = {}
    for index, c in enumerate(reversed(forecast.candidates)):
        renamed_id = f'AnonymousCandidate{index:03d}'
        inverse[renamed_id]=c.candidate_id
        renamed.append(ForecastCandidate(renamed_id,c.reference_response_ppm,c.physical_source_xyz))
    # Persist the changed forecast set to a new response-only directory, so the
    # permutation test also exercises the on-disk input interface.
    with tempfile.TemporaryDirectory(prefix='rk2_infer_permutation_') as temp:
        changed=Path(temp)
        manifest=dict(model_id=forecast.model_id,candidates=[])
        for index,c in enumerate(renamed):
            name=f'reference_{index:03d}.npz'
            np.savez(changed/name,reference_response_ppm=c.reference_response_ppm)
            manifest['candidates'].append(dict(candidate_id=c.candidate_id,reference_file=name,physical_source_xyz=list(c.physical_source_xyz)))
        (changed/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
        permuted=infer(load_forecasts(changed),load_observation(observation_dir))
    check_renaming(baseline,permuted,inverse)
    return dict(hidden_state_removal='PASS',truth_mapping_removal='PASS',candidate_rename_and_permutation='PASS',
                real_directory_loads=True,normalized_probability_tolerance=1e-15)

def file_oracle_checks(forecast_npz, observation_json, model_id, hidden_files=(), truth_files=()):
    """Three oracle checks on actual frozen per-model and per-observation files.

    Hidden/truth paths MUST be isolated, disposable test fixtures supplied by
    the caller. Existing physical/evaluation evidence is never required here.
    """
    baseline=infer_files(forecast_npz,observation_json,model_id)
    for p in hidden_files:Path(p).unlink()
    without_hidden=infer_files(forecast_npz,observation_json,model_id)
    if canonical(baseline)!=canonical(without_hidden):raise AssertionError('hidden state removal changed infer')
    for p in truth_files:Path(p).unlink()
    without_truth=infer_files(forecast_npz,observation_json,model_id)
    if canonical(baseline)!=canonical(without_truth):raise AssertionError('truth mapping removal changed infer')
    forecast,plan=load_forecast_npz(forecast_npz,model_id)
    candidates=list(reversed(forecast.candidates));names=[f'AnonymousCandidate{i:03d}' for i in range(len(candidates))]
    inverse={name:c.candidate_id for name,c in zip(names,candidates)}
    with tempfile.TemporaryDirectory(prefix='rk2_infer_actual_permutation_') as tmp:
        changed=Path(tmp)/'renamed_forecasts.npz'
        np.savez(changed,candidate_ids=np.array(names,dtype='U'),source_xyz=np.array([c.physical_source_xyz for c in candidates],dtype=np.float64),
                 reference_response_ppm=np.stack([c.reference_response_ppm for c in candidates]),receiver_plan_id=np.array(plan,dtype='U'))
        renamed=infer_files(changed,observation_json,model_id)
    check_renaming(baseline,renamed,inverse)
    return dict(hidden_state_removal='PASS',truth_mapping_removal='PASS',candidate_rename_and_permutation='PASS',
                actual_forecast_and_observation_files=True,normalized_probability_tolerance=1e-15,
                observation_id=baseline['observation_id'],model_id=model_id)

class InferContractTests(unittest.TestCase):
    def fixture(self, root, tie=False):
        reference=root/'reference_forecasts'; observation=root/'observed_scalars'
        reference.mkdir(); observation.mkdir()
        a=np.zeros((2,50),dtype=np.float32);a[:,::2]=0.2
        b=a.copy() if tie else np.full((2,50),0.2,dtype=np.float32)
        np.savez(reference/'r0.npz',reference_response_ppm=a)
        np.savez(reference/'r1.npz',reference_response_ppm=b)
        manifest=dict(model_id='software_fixture',candidates=[dict(candidate_id='C7',reference_file='r0.npz',physical_source_xyz=[0,0,0]),dict(candidate_id='K2',reference_file='r1.npz',physical_source_xyz=[1,1,1])])
        (reference/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
        np.savez(observation/'observed.npz',observed_ppm=a[0])
        (observation/'manifest.json').write_text(json.dumps(dict(observation_id='O00',receiver_plan_id='P00',response_file='observed.npz')),encoding='utf-8')
        np.savez(observation/'hidden_particle_state.npz',filaments=np.full((5,4),123))
        (observation/'true_source_mapping.json').write_text('{"O00":"C7"}',encoding='utf-8')
        return reference,observation

    def test_three_directory_information_checks(self):
        with tempfile.TemporaryDirectory(prefix='rk2_infer_contract_') as tmp:
            reference,observation=self.fixture(Path(tmp))
            result=directory_oracle_checks(reference,observation,
                [observation/'hidden_particle_state.npz'],[observation/'true_source_mapping.json'])
            self.assertEqual(result['hidden_state_removal'],'PASS')

    def test_ties_share_probability_and_top1_is_set(self):
        with tempfile.TemporaryDirectory(prefix='rk2_infer_tie_') as tmp:
            reference,observation=self.fixture(Path(tmp),tie=True)
            result=infer(load_forecasts(reference),load_observation(observation))
            self.assertEqual(set(result['top1_candidate_ids']),{'C7','K2'})
            self.assertEqual([c['source_probability'] for c in result['candidates']],[.5,.5])
            directory_oracle_checks(reference,observation)

    def test_each_reference_thresholded_before_averaging(self):
        reference=np.array([[0.0]*50,[0.15]*50],dtype=np.float32)
        forecast=ForecastSet('M',(ForecastCandidate('A',reference,(0,0,0)),))
        obs=ObservationSeries('O',np.full(50,.2,dtype=np.float32),'P')
        result=infer(forecast,obs)
        self.assertEqual(result['candidates'][0]['probability_by_block'],[.5]*50)

    def test_float32_strict_threshold(self):
        values=np.full((2,50),np.float32(.1),dtype=np.float32)
        result=infer(ForecastSet('M',(ForecastCandidate('A',values,(0,0,0)),)),ObservationSeries('O',values[0],'P'))
        self.assertEqual(result['candidates'][0]['probability_by_block'],[1/6]*50)

    def test_reject_forbidden_npz_fields(self):
        with tempfile.TemporaryDirectory(prefix='rk2_infer_reject_') as tmp:
            reference,observation=self.fixture(Path(tmp))
            np.savez(observation/'observed.npz',observed_ppm=np.zeros(50),filaments=np.zeros((3,4)))
            with self.assertRaises(ValueError):load_observation(observation)

    def test_reject_truth_manifest_field(self):
        with tempfile.TemporaryDirectory(prefix='rk2_infer_reject_') as tmp:
            reference,observation=self.fixture(Path(tmp))
            obj=json.loads((observation/'manifest.json').read_text());obj['truth_source']='C7'
            (observation/'manifest.json').write_text(json.dumps(obj),encoding='utf-8')
            with self.assertRaises(ValueError):load_observation(observation)

    def test_reject_observation_with_dictionary_state(self):
        with self.assertRaises(TypeError):
            infer(ForecastSet('M',(ForecastCandidate('A',np.zeros((2,50)),(0,0,0)),)),{'observed_ppm':np.zeros(50),'filaments':[]})

    def test_nonfinite_negative_duplicate_and_shape_rejected(self):
        with self.assertRaises(ValueError):ForecastCandidate('A',np.zeros((2,49)),(0,0,0))
        with self.assertRaises(ValueError):ObservationSeries('O',np.full(50,np.nan),'P')
        with self.assertRaises(ValueError):ObservationSeries('O',np.full(50,-1.0),'P')
        candidate=ForecastCandidate('A',np.zeros((2,50)),(0,0,0))
        with self.assertRaises(ValueError):ForecastSet('M',(candidate,candidate))

    def test_explicit_file_schema_three_checks(self):
        with tempfile.TemporaryDirectory(prefix='rk2_infer_actual_schema_') as tmp:
            root=Path(tmp);ref=root/'reference';obs=root/'observations';ref.mkdir();obs.mkdir()
            responses=np.zeros((2,2,50),dtype=np.float64);responses[0,:,::2]=.2;responses[1,:,:]=.2
            p=ref/'M.npz';q=obs/'O00.json'
            np.savez(p,candidate_ids=np.array(['C7','K2'],dtype='U'),source_xyz=np.array([[0,0,0],[1,1,1]],dtype=np.float64),
                reference_response_ppm=responses,receiver_plan_id=np.array('P00',dtype='U'))
            q.write_text(json.dumps(dict(observation_id='O00',observed_ppm=responses[0,0].tolist(),receiver_plan_id='P00')),encoding='utf-8')
            forbidden=obs/'forbidden_hidden';forbidden.mkdir();hidden=forbidden/'particles.npz';truth=obs/'truthmap.json'
            np.savez(hidden,filaments=np.ones((3,4)));truth.write_text('{"O00":"C7"}',encoding='utf-8')
            result=file_oracle_checks(p,q,'M',[hidden],[truth])
            self.assertEqual(result['candidate_rename_and_permutation'],'PASS')

    def test_explicit_file_schema_rejects_plan_mismatch(self):
        with tempfile.TemporaryDirectory(prefix='rk2_infer_actual_schema_') as tmp:
            root=Path(tmp);p=root/'M.npz';q=root/'O00.json'
            np.savez(p,candidate_ids=np.array(['A'],dtype='U'),source_xyz=np.zeros((1,3)),reference_response_ppm=np.zeros((1,2,50)),receiver_plan_id=np.array('P00',dtype='U'))
            q.write_text(json.dumps(dict(observation_id='O00',observed_ppm=[0.0]*50,receiver_plan_id='P99')),encoding='utf-8')
            with self.assertRaises(ValueError):infer_files(p,q,'M')

if __name__=='__main__':unittest.main(verbosity=2)
