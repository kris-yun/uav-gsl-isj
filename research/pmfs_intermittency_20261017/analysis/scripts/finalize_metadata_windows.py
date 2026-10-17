from pathlib import Path
import json,shutil,hashlib,csv
R=Path(__file__).resolve().parents[1];D=R/'DELIVERY';A=D/'analysis'
for n in ['scripts','cpp','lineage']:shutil.copytree(R/n,A/n,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for n in ['CAUSAL_CHAIN_DECISION.md','DATA_IDENTITY_AND_ORIGINAL_RELEASE.md','MINIMUM_SUPPLEMENT.md','IMPLEMENTATION_AND_EVENT_SEMANTICS.md','FAILED_ATTEMPTS_AND_LIMITATIONS.md']:shutil.copyfile(R/n,A/n)
shutil.copyfile(R/'README_给Pro先读.md',D/'README.md');shutil.copyfile(R/'reproduce_all.py',D/'reproduce_all.py');shutil.copytree(R/'results/PORTABLE_QA',A/'results/PORTABLE_QA',dirs_exist_ok=True);shutil.copytree(R/'logs',A/'logs',dirs_exist_ok=True);shutil.copyfile(R/'GITHUB_PUBLICATION.json',A/'INITIAL_PUBLICATION_RECEIPT.json')
p=A/'COMMANDS_AND_EXIT_CODES.csv';rows=list(csv.DictReader(p.open()));rows += [dict(scientific_command='reproduce_all.py --out ICQA17 [15 offline commands]',preserved_log_or_receipt='results/PORTABLE_QA/EXECUTION.json',exit_code=0),dict(scientific_command='package_qa_windows.py [8 full output byte identities]',preserved_log_or_receipt='results/PORTABLE_QA/PRIMARY_OUTPUT_EQUALITY.json',exit_code=0),dict(scientific_command='prepare_native.py [prefer bundled headers]; build; ctest',preserved_log_or_receipt='logs/ctest_bundled.stdout',exit_code=0)]
with p.open('w',newline='') as f:w=csv.DictWriter(f,rows[0]);w.writeheader();w.writerows(rows)
manifest={}
for p in sorted(D.rglob('*')):
 if p.is_file() and p.name!='MANIFEST_SHA256.json':manifest[p.relative_to(D).as_posix()]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(D/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2));print('FINAL',len(manifest),sum(v['bytes'] for v in manifest.values()))
