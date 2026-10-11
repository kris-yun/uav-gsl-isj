"""Only re-render the saved figure block to remove legend/text collision."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
p=Path(__file__).resolve().parent/'build_rk1_reports.py'
s=p.read_text(encoding='utf-8')
header=s[:s.index('pre = load(')]
setup="""
metrics=rows(OUT/'BANK_METRICS_ANALYSIS.csv')
paired=rows(OUT/'TEST_BANK_PAIRED_COMPARISONS.csv')
banks=[r['bank'] for r in paired]
arms=['U','S','C_ORACLE']
mm={(r['bank'],r['arm']):r for r in metrics if r['role']=='test'}
coverage=rows(OUT/'TEST_COVERAGE_AND_THRESHOLD_SUMMARY.csv')
for r in coverage:
    r['Q_particle_fraction']=float(r['Q_particle_fraction'])
    r['Q_response_fraction']=float(r['Q_response_fraction'])
"""
figure=s[s.index('plt.rcParams.update'):s.index("write(OUT/'RK1_FIGURE_CAPTION_zh.md'")]
figure=figure.replace("assert not (OUT/'RK1_PAIRED_RESPONSE_DIAGNOSTIC.png').exists()",'')
exec(compile(header+setup+figure,str(p),'exec'),{'__file__':str(p)})
caption=Path(__file__).resolve().parents[2]/'outputs/PMFS_RK1_MATCHED_SUPPORT_CROSSFIT_20261010/RK1_FIGURE_CAPTION_zh.md'
caption.write_text(caption.read_text(encoding='utf-8').replace('图顶文字','横轴附注'),encoding='utf-8')
print('FIGURE_LAYOUT_REPAIRED_ONLY_NO_RESULT_CHANGE')
