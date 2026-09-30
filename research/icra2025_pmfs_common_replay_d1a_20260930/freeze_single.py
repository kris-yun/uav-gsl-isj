"""Freeze one source-blind target and all supplied zero-shot checkpoints."""
import csv,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'comparison_work/official_reproduction'))
from run_official_smoke import EXPECTED,UP,sha
with (ROOT/'freeze/D1A_RUNLIST_64.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
chosen=sorted([r for r in rows if r['house']=='House01'],key=lambda r:r['run_id'])[0]
assert chosen['run_id']=='ocb_r2_cfg00_r01'
weights=[]
for name,(size,digest) in EXPECTED.items():
    p=UP/'model'/name;assert p.stat().st_size==size and sha(p)==digest
    weights.append(dict(file=name,bytes=size,sha256=digest,input_channels=2 if name=='unet_model_final.pth' else 3))
result=dict(stage='D0_LITE',D1A='PAUSED_NOT_EXECUTED',case=chosen,selection='first lexicographic H01 discovery; no endpoint/encounter screening',
    weights=weights,primary_weight=None,weight_selection='all four; upstream default not uniquely identified',
    official_upstream='ca0c387be9f27716a422588ac2299e2d816c3e2a',adapter_commit='9a12cc69833d04cce5c8859ed51764956eeabe92',
    contract_sha256=sha(ROOT/'D0_LITE_AMENDMENT.md'),wind_parity_sha256=sha(ROOT/'freeze/WIND_VECTOR_ANGLE_PARITY.json'),
    logger_build_sha256=sha(ROOT/'freeze/BUILD_PROVENANCE.json'),target_executions_authorized=1,plume_generation=0,
    training=False,confirmation_read=False,house03_read=False,output_root='C:/GADEN_OCB_R2_ARCHIVE/d0_lite_20260930',
    prospective_files={p.name:sha(p) for p in sorted(ROOT.glob('*.py'))})
(ROOT/'freeze/D0_LITE_PRE_TARGET_FREEZE.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('D0_LITE_PRE_TARGET_FREEZE',chosen['run_id'])
