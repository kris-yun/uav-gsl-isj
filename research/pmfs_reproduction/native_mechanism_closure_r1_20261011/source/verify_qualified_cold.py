from common_n import *
import ast,subprocess
# Reuse independent arithmetic, changing only which isolated outputs are authoritative.
src=(WORK/'verify_completed_native.py').read_text();src=src.replace("HOST_DATA/'native_results'","HOST_DATA/'native_cold_results'")
# Historical score/forward anchors remain in original directory; initialization repair concerns derived histories only.
src=src.replace("new=HOST_DATA/'native_cold_results'/(label+'_saved_map_scores')","new=HOST_DATA/'native_results'/(label+'_saved_map_scores')").replace("forward=HOST_DATA/'native_cold_results'/(label+'_short_forward_OFF')","forward=HOST_DATA/'native_results'/(label+'_short_forward_OFF')")
src=src.replace("CORE/'NATIVE_COMPLETE_MAP_RESULTS.csv'","CORE/'QUALIFIED_N0_COMPLETE_MAP_RESULTS.csv'").replace("CORE/'NATIVE_COMPLETE_MAP_POSTERIORS.csv'","CORE/'QUALIFIED_N0_COMPLETE_MAP_POSTERIORS.csv'")
src=src.replace("(oid+'_NATIVE_OUTPUT_FREEZE_BEFORE_METRICS.json')","(oid+'_QUALIFIED_COLD_OUTPUT_FREEZE.json')")
src=src.replace("classification='N0_NATIVE_CONTROLLED_FIXED50_HISTORY_REPLAY_NOT_OFFICIAL_NEW_ACTION'","classification='N0_VERIFIED_NATIVE_COLD_FIXED50_HISTORY_NOT_OFFICIAL_ACTION'")
(WORK/'verify_cold_arithmetic.py').write_text(src,encoding='utf-8')
p=subprocess.run([sys.executable,'-B','-X','utf8',str(WORK/'verify_cold_arithmetic.py')],capture_output=True,text=True);print(p.stdout);assert p.returncode==0,p.stderr
