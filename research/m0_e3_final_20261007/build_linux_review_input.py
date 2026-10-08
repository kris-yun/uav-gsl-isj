from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parent;F=R.parent/'m0_clean_support_r0_20261007';OUT=R/'FINAL_LINUX_REVIEW_INPUTS.zip';assert not OUT.exists()
with zipfile.ZipFile(OUT,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(F.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:z.write(p,'m0_clean_support_r0_20261007/'+p.relative_to(F).as_posix())
    for p in sorted(R.rglob('*')):
        if p.is_file() and p!=OUT and not any(q in p.parts for q in ['evidence','frozen','__pycache__']) and not p.name.startswith('M0_NATIVE_') and p.name!='E3_INPUTS.zip':z.write(p,'m0_e3_final_20261007/'+p.relative_to(R).as_posix())
    z.write(R/'M0_NATIVE_PACKAGES_MANIFEST_20261007.json','m0_e3_final_20261007/M0_NATIVE_PACKAGES_MANIFEST_20261007.json')
x={'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'bytes':OUT.stat().st_size,'simulator_runs':0};(R/'LINUX_REVIEW_INPUT_RECEIPT.json').write_bytes((json.dumps(x,indent=2)+'\n').encode());print(json.dumps(x,indent=2))
