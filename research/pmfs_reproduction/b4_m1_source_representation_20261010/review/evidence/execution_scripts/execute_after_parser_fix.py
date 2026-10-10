"""Execute the same approved six jobs after a proven zero-forward input-loader repair."""
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from remote_local import run
W=Path(__file__).resolve().parent;R=W.parents[1];O=R/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
repair=json.loads((O/'INPUT_PARSER_REPAIR.json').read_text(encoding='utf-8'))
assert repair['actual_forward_calls_before_repair']==0 and repair['input_data_modified'] is False
assert repair['native_kernel_modified'] is False and repair['RNG_or_parameters_modified'] is False
old=json.loads((O/'M1_A_EXECUTION_LEDGER.json').read_text(encoding='utf-8'))
assert old['completed_calls']==0 and old['attempted_calls']==1
(O/'M1_A_EXECUTION_LEDGER.json').rename(O/'M1_A_INITIALIZATION_FAILURE_LEDGER.json')
code=(W/'APPROVED_REMOTE_EXECUTION.py').read_text(encoding='utf-8')
code=code.replace("root=target/'forward_calls';assert not root.exists();root.mkdir()",
                  "root=target/'forward_calls_after_input_parser_fix';assert not root.exists();root.mkdir()")
code=code.replace(repair['original_executable_sha256'],repair['executable_sha256'])
needle="ledger=dict(status='RUNNING_APPROVED_ONE_SHOT'"
code=code.replace(needle,"ledger=dict(prior_initialization_launches=1,prior_actual_forward_calls=0,status='RUNNING_APPROVED_ONE_SHOT'")
assert 'forward_calls_after_input_parser_fix' in code
compile(code,'approved_forward_after_loader_repair','exec')
(W/'APPROVED_REMOTE_EXECUTION_AFTER_PARSER_FIX.py').write_text(code,encoding='utf-8')
result=json.loads(run(code,'APPROVED_SIX_AFTER_PARSER_FIX',145))
(O/'M1_A_EXECUTION_LEDGER.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
