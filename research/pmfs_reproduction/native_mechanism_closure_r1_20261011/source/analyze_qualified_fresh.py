from common_n import *
import subprocess
src=(WORK/'analyze_fresh_confirmation.py').read_text().replace("D/'native_results'","D/'native_cold_results'").replace("D/'point_scores'","D/'point_corrected_scores'").replace("DATA+'/point_scores/'","DATA+'/point_corrected_scores/'")
src=src.replace("CORE/'FRESH_N0_COMPLETE_MAP_RESULTS.csv'","CORE/'QUALIFIED_FRESH_N0_COMPLETE_MAP_RESULTS.csv'")
src=src.replace("(oid+'_FRESH_OUTPUT_FREEZE_BEFORE_METRICS.json')","(oid+'_QUALIFIED_FRESH_OUTPUT_FREEZE.json')")
(WORK/'analyze_qualified_fresh_impl.py').write_text(src,encoding='utf-8');p=subprocess.run([sys.executable,'-B','-X','utf8',str(WORK/'analyze_qualified_fresh_impl.py')],capture_output=True,text=True);print(p.stdout);assert p.returncode==0,p.stderr
