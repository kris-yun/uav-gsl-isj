from common_r2 import *
import subprocess
counts={};start=time.time()
for folder in [R1,R1RAW]:
 m=load(folder/'FILE_SHA256_MANIFEST.json')
 for rel,value in m.items():assert sha(folder/rel)==value,rel
 counts[folder.name]=len(m)
dump(CORE/'PARENT_IN_PACKAGE_HASH_VERIFICATION.json',dict(status='PASS_PARENT_UNCHANGED',counts=counts,seconds=time.time()-start,external_full_banks_rehashed=False))
cmd=[sys.executable,'-B','-m','unittest','-v','test_source_map_tools.py'];p=subprocess.run(cmd,cwd=WORK/'pro_plan/code',capture_output=True,text=True)
(CORE/'SOURCE_MAP_TOOL_UNIT_TESTS.log').write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0
print(json.dumps({'status':'PASS_PARENT_AND_ORDINARY_TOOL_TESTS','counts':counts,'seconds':time.time()-start}))
