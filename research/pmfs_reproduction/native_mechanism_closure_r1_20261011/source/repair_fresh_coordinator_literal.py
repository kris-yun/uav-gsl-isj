from common_n import *
src=(CORE/'source/coordinate_qualified_fresh_cold.py').read_text()
bad="'TOTAL_TIME_CAP_WAITING_FRESH_'/mnt/hgfs/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011''"
assert bad in src
src=src.replace(bad,"'TOTAL_TIME_CAP_WAITING_FRESH_WORLD'")
compile(src,'fresh_coordinator_literal_fixed','exec')
(CORE/'source/coordinate_qualified_fresh_cold_literal_fixed.py').write_text(src,encoding='utf-8')
code='''import subprocess
assert not (t/'COLD_FRESH_TASKS.json').exists(), 'No science was started by malformed coordinator'
p=subprocess.Popen(['python3',str(t/'coordinate_qualified_fresh_cold_literal_fixed.py')],stdout=(t/'qualified_fresh_cold_literal_fixed.stdout').open('w'),stderr=(t/'qualified_fresh_cold_literal_fixed.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'repair':'Syntax-only message literal; original failed before importing or executing any task','new_physical_generation':0,'same_registered_fresh6':True}))
'''
receipt=json.loads(upload({'coordinate_qualified_fresh_cold_literal_fixed.py':src.encode()},code,'repair_fresh_coordinator_literal_and_start',30))
dump(CORE/'FRESH_COORDINATOR_LITERAL_REPAIR.json',receipt)
print(json.dumps(receipt))
