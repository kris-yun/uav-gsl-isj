"""Resume identical preflight after existing VM boot readiness; no science retry."""
from common_n import *
import ast,shutil
tree=ast.parse((WORK/'preflight_n.py').read_text())
tail=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tail' for t in n.targets))
result=json.loads(upload({'CAMPAIGN_CONTRACT.json':(CORE/'CAMPAIGN_CONTRACT.json').read_bytes()},tail,'EXISTING_VM_PREFLIGHT_RETRY_BOOT_READY',45))
dump(CORE/'PREFLIGHT.json',result)
pro=WORK/'pro_handoff/PMFS_NATIVE_MECHANISM_CLOSURE_R1';h=load(pro/'MANIFEST_SHA256.json')
assert all(sha(pro/n)==v for n,v in h.items())
dump(CORE/'PRO_HANDOFF_VERIFICATION.json',dict(status='PASS',manifest_entries=len(h),zip_SHA256=sha(Path('C:/Users/50176/Downloads/PMFS_RK2B_独立审核与原生机制闭合总计划_a5d93c9.zip'))))
dump(CORE/'TECHNICAL_REPAIRS.json',dict(repairs=[dict(kind='Existing VM SSH boot readiness',attempts=1,first_error='SSH ConnectTimeout at192.168.111.128:22',VM_path='D:/Ubuntu/Ubuntu 64 位.vmx',VM_created=False,VM_restarted_by_this_task=False,inputs_or_code_changed=False,new_physical_calls_before_retry=0)]))
print(json.dumps(result,indent=2))
