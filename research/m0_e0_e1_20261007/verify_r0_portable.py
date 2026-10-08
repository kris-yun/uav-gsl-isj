"""External archive/provenance verifier; never edits or executes the R0 builder.

Handles Windows provenance strings with PureWindowsPath on any platform.
Original freeze_design.py --verify remains the canonical archive integrity check.
"""
from pathlib import Path,PureWindowsPath
import argparse,csv,hashlib,json
parser=argparse.ArgumentParser();parser.add_argument('frozen',nargs='?',default=str(Path(__file__).resolve().parent.parent/'m0_clean_support_r0_20261007'));args=parser.parse_args();R=Path(args.frozen)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze=json.loads((R/'M0_R0_FREEZE.json').read_text(encoding='utf-8'));assert sha(R/'M0_R0_FILES_SHA256.csv')==freeze['manifest_sha256']
with (R/'M0_R0_FILES_SHA256.csv').open(encoding='utf-8') as f:files=list(csv.DictReader(f))
for q in files:
    p=R/q['path'];assert p.stat().st_size==int(q['bytes']) and sha(p)==q['sha256']
with (R/'M0_PARENT_INPUTS_SHA256.csv').open(encoding='utf-8') as f:parents=list(csv.DictReader(f))
for q in parents:
    text=q['path'];name=PureWindowsPath(text).name if '\\' in text or (len(text)>1 and text[1]==':') else Path(text).name
    if q['role']=='frozen historical decision':name='W0C_'+name
    assert sha(R/'provenance'/name)==q['sha256'],name
print(json.dumps({'portable_archive_and_provenance':'PASS','frozen_files':len(files),'parent_inputs':len(parents),'R0_unchanged':True,'scientific_verdict':'NOT_TESTED','scope':'Archive integrity + portable provenance lookup; not a replacement for scientific experiment gates.'},indent=2))
