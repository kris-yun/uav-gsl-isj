from common_n import *
import subprocess
src=(WORK/'native_evidence_diagnostics.py').read_text().replace("f'native_results/N0_","f'native_cold_results/N0_")
for n in ['NATIVE_LEAF_SUPPORT_AND_RELEASE.csv','NATIVE_PAIR_CELL_CONTRIBUTIONS.csv','NATIVE_MEASUREMENT_BLOCK_MARGIN_LINEAGE.csv','NATIVE_FIXED_LIBRARY_PREFIX_SCORES.csv','D_STAGE_SCOPE.json']:
 src=src.replace(n,'QUALIFIED_'+n)
(WORK/'qualified_lineage_impl.py').write_text(src,encoding='utf-8')
p=subprocess.run([sys.executable,'-B','-X','utf8',str(WORK/'qualified_lineage_impl.py')],capture_output=True,text=True)
print(p.stdout);assert p.returncode==0,p.stderr
