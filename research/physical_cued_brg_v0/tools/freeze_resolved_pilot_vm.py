"""Bind resolved support without changing any original plume case or truth."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927');sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    old=ROOT/'campaign_contract';out=ROOT/'pilot_contract_resolved';out.mkdir(exist_ok=False)
    b=TemplateBank.load(ROOT/'legal_support_v2/h03_native_legal_bank.npz');assert len(b.ids)==615
    cases=[]
    for path in sorted(old.glob('source_*.json')):
        c=json.loads(path.read_text());c['candidate_support_id']=b.fingerprint;c['truth_in_support']=c['source_id'] in b.ids
        c['reporting_stratum']='in_support' if c['truth_in_support'] else 'support_misspecification'
        (out/path.name).write_text(json.dumps(c,indent=2,sort_keys=True)+'\n');cases.append(c)
    assert len(cases)==96 and sum(not c['truth_in_support'] for c in cases)==8
    schedule=['source_0_replica_0','source_0_replica_1','source_3_replica_0','source_3_replica_1']
    report={'authorization_sha256':sha(ROOT/'amendment/08_SIGNED_NATIVE_SUPPORT_RESOLUTION.json'),
        'unchanged_geometric_endpoint_sha256':sha(ROOT/'amendment/06_GEOMETRIC_SUCCESS_CLARIFICATION.md'),
        'historical_hold_preserved':True,'all_cases_retained':96,'in_support':88,'support_misspecification':8,'support_count':615,'support_id':b.fingerprint,
        'bank_sha256':sha(ROOT/'legal_support_v2/h03_native_legal_bank.npz'),'case_sha256':{p.name:sha(p) for p in sorted(out.glob('source_*.json'))},
        'P0_cases':schedule[:1],'P1_cumulative_cases':schedule,'P1_cumulative_runs':16,'P1_STOP_NO_AUTOMATIC_FULL_CAMPAIGN':True,
        'P0_reused_in_P1_only_if_same_frozen_version':True,'arms':['native_pmfs','candidate_gru','brg','brg_ungated'],
        'budget_s':300,'radius_m':.5,'source_truth_and_support_flag_are_evaluation_only':True,'new_plumes':0,
        'mode':'VGR interactive closed-loop development campaign, not Gazebo physics'}
    (out/'PILOT_PRETRAIN_BINDING.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
