"""Use the task's one isolated code repair, preserve the failed numerical attempt."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,shutil,difflib
BASE=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
OLD=BASE/'outputs/PMFS_RK2_FINITE_RESPONSE_PROTOTYPE_20261010'
NEW=BASE/'outputs/PMFS_RK2_FINITE_RESPONSE_PROTOTYPE_20261010_REPAIR1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not NEW.exists();assert not (OLD/'SOURCE_TASK_PREDICTIONS_BLIND.json').exists();assert not (OLD/'models').exists()
contract=json.loads((OLD/'contract.json').read_text(encoding='utf-8'))
ledger=json.loads((OLD/'EXECUTION_LEDGER.json').read_text(encoding='utf-8'))
assert ledger['exitcode']==1 and ledger['resource_stop'] is None
assert 'Query-fit KKT failed' in (OLD/'RUN_FAILURE.json').read_text(encoding='utf-8')
NEW.mkdir();(NEW/'source').mkdir()
for name,digest in contract['prepared_input_SHA256'].items():
    src=OLD/name;assert sha(src)==digest
    dst=NEW/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for name,digest in contract['source_SHA256'].items():
    assert sha(OLD/'source'/name)==digest
    shutil.copyfile(OLD/'source'/name,NEW/'source'/name)
shutil.copyfile(WORK/'rk2_models.py',NEW/'source/rk2_models.py')
diff=''.join(difflib.unified_diff((OLD/'source/rk2_models.py').read_text(encoding='utf-8').splitlines(True),(NEW/'source/rk2_models.py').read_text(encoding='utf-8').splitlines(True),fromfile='frozen_first/rk2_models.py',tofile='repair1/rk2_models.py'))
(NEW/'NUMERICAL_IMPLEMENTATION_REPAIR.diff').write_text(diff,encoding='utf-8')
new=dict(contract);new['source_SHA256']={p.name:sha(p) for p in (NEW/'source').iterdir()}
new['repair_of_contract_SHA256']=sha(OLD/'contract.json');new['allowed_isolated_code_repair']=1
new['numerical_repair']='Identical primal query-ridge objective solved to the same frozen KKT threshold using a deterministic at-most32-step n=20 convex-dual Newton polish after the original SciPy solve.'
new['wall_limit_s']=contract['wall_limit_s']-ledger['wall_s'];new['output_limit_bytes']=contract['output_limit_bytes']-sum(p.stat().st_size for p in OLD.rglob('*') if p.is_file())
new['first_attempt_wall_s']=ledger['wall_s'];new['combined_attempts_within_original_budget']=True
(NEW/'contract.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(NEW/'PRE_RUN_CONTRACT_SHA256.txt').write_text(sha(NEW/'contract.json')+'  contract.json\n',encoding='utf-8')
(NEW/'NUMERICAL_REPAIR_PROVENANCE.json').write_text(json.dumps(dict(first_attempt_hashes={p.relative_to(OLD).as_posix():sha(p) for p in OLD.rglob('*') if p.is_file()},first_attempt_failed_before_any_test_or_source_prediction=True,
    regularization_loss_routing_capacity_task_score_or_KKT_tolerance_changed=False,original_frozen_files_modified=False,
    no_second_L_constructed=True,remaining_wall_s=new['wall_limit_s']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='ONE_NUMERICAL_REPAIR_FROZEN',new=str(NEW),contract_SHA256=sha(NEW/'contract.json'),remaining_wall_s=new['wall_limit_s']),ensure_ascii=False))
