from pathlib import Path
import json,hashlib,csv,shutil
R=Path(__file__).resolve().parents[1];F=R.parent/'ICQA17/INTERMITTENCY_CAUSAL_AUDIT_20261017';P=F.parent/'PORTABLE_REPRODUCTION_PASS.json';assert P.exists();receipt=json.loads(P.read_text());assert receipt['status']=='PASS_ALL_REPRODUCTION_COMMANDS';rows=[]
for name in ['STRONG_CONTROLS.csv','STOP_INFLUENCE.csv','EVIDENCE_MATRIX.csv','OBSERVATION_WINDOWS.csv','RAW_PID_MESSAGES.csv','SOURCE_SCORE_PARITY.json','FINAL_DECISION.json','03_OPERATOR_TO_SOURCE_SCORE_TRACE.csv']:
 a=R/'results'/name;b=F/'results'/name;equal=a.read_bytes()==b.read_bytes();rows.append(dict(file=name,original_sha256=hashlib.sha256(a.read_bytes()).hexdigest(),fresh_sha256=hashlib.sha256(b.read_bytes()).hexdigest(),byte_equal=equal));assert equal,(name,'fresh mismatch')
headers=[]
for p in (R/'cpp/dda').rglob('*'):
 if p.is_file():assert p.read_bytes()==(F/'cpp/dda'/p.relative_to(R/'cpp/dda')).read_bytes();headers.append(p.relative_to(R/'cpp/dda').as_posix())
qadir=R/'results/PORTABLE_QA';qadir.mkdir(exist_ok=True);shutil.copyfile(P,qadir/'PASS.json');shutil.copyfile(F/'EXECUTION.json',qadir/'EXECUTION.json');shutil.copytree(F/'logs',qadir/'logs',dirs_exist_ok=True);(qadir/'PRIMARY_OUTPUT_EQUALITY.json').write_text(json.dumps(dict(status='PASS_ALL_PRIMARY_OUTPUTS_BYTE_IDENTICAL',files=rows,matching_vendored_DDA_headers=len(headers)),indent=2));print('PASS',len(rows),'full-output identities,',len(headers),'DDA headers,',receipt['commands'],'standalone commands')
