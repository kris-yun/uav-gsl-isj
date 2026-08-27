#!/usr/bin/env python3
"""Independent verifier for H02_RECONSTRUCTED_CHALLENGE_V1 banks."""
from __future__ import annotations
import argparse,csv,hashlib,json,struct
from pathlib import Path

MAGIC=0x32564B4E42545443
HEADER=struct.Struct('<7Q')

def sha256(path:Path)->str:
    digest=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()

def csv_rows(path:Path):
    with path.open(newline='',encoding='utf-8-sig') as handle:return list(csv.DictReader(handle))

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--context-manifest',type=Path,required=True);p.add_argument('--carrier-manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    contexts=csv_rows(a.context_manifest);carriers=csv_rows(a.carrier_manifest)
    if len(contexts)<18:raise SystemExit(f'expected >=18 frozen contexts, got {len(contexts)}')
    if len(carriers)!=201:raise SystemExit(f'expected 201 geometry carriers, got {len(carriers)}')
    identities={(r['run_uuid'],int(r['source_update_id'])) for r in contexts}
    if len(identities)!=len(contexts):raise SystemExit('duplicate (run_uuid, source_update_id) in frozen manifest')
    if any('h02' not in r['context_dir'].lower() and 'house02' not in r['context_dir'].lower() for r in contexts):raise SystemExit('non-H02 context in frozen manifest')
    master=sha256(a.carrier_manifest);total_records=0;total_bytes=0;digests=[]
    for context in contexts:
        case=context['case_id'];matches=sorted((a.root/'banks').glob(f'{case}_*'))
        if len(matches)!=1:raise SystemExit(f'{case}: expected one bank directory, got {len(matches)}')
        bank=matches[0];contract=json.loads((bank/'ctt_trace_bank_contract.json').read_text())
        expected={'contract':'CTT_V13_TRUTH_FREE_TRACE_BANK_V1','run_uuid':context['run_uuid'],'source_update_id':int(context['source_update_id']),'source_truth_used':False,'method_seed':20260818,'transport_substream':6077111455669390931,'transport_members':8,'timesteps':200,'delta_time':0.2,'noise_standard_deviation':0.5,'carrier_count':201}
        for k,v in expected.items():
            if contract.get(k)!=v:raise SystemExit(f'{case}: contract mismatch {k}: {contract.get(k)!r} != {v!r}')
        if sha256(bank/'carrier_manifest.csv')!=master:raise SystemExit(f'{case}: carrier manifest drift')
        rec=csv_rows(bank/'ctt_trace_records.csv')
        if len(rec)!=201*8:raise SystemExit(f'{case}: record manifest count {len(rec)}')
        keys={(int(r['carrier_index']),int(r['transport_member'])) for r in rec};expected_keys={(s,m) for s in range(201) for m in range(8)}
        if keys!=expected_keys:raise SystemExit(f'{case}: carrier/member coverage mismatch')
        if any(float(r['reconstruction_max_abs'])!=0.0 for r in rec):raise SystemExit(f'{case}: nonzero reconstruction error')
        case_hash=hashlib.sha256()
        for carrier,member in sorted(keys):
            path=bank/'records'/f'carrier_{carrier:04d}_member_{member:02d}.cttbin'
            with path.open('rb') as h:raw=h.read(HEADER.size)
            if len(raw)!=HEADER.size:raise SystemExit(f'{case}: short trace header {path.name}')
            magic,version,got_carrier,got_member,steps,cells,words=HEADER.unpack(raw)
            if (magic,version,got_carrier,got_member,steps)!=(MAGIC,1,carrier,member,200):raise SystemExit(f'{case}: trace identity/header mismatch {path.name}')
            expected_size=HEADER.size+4*steps+4*cells+8*steps*words
            if path.stat().st_size!=expected_size:raise SystemExit(f'{case}: trace size mismatch {path.name}')
            fh=sha256(path);case_hash.update(path.name.encode());case_hash.update(fh.encode('ascii'));total_records+=1;total_bytes+=path.stat().st_size
        digests.append({'case_id':case,'bank_dir':str(bank),'records_sha256':case_hash.hexdigest()})
    tmp=list(a.root.rglob('*.tmp'))
    if tmp:raise SystemExit(f'temporary trace files remain: {len(tmp)}')
    payload={'verdict':'H02_RECONSTRUCTED_CHALLENGE_V1_BANK_VERIFY_PASS','legacy_hard28_recreated':False,'context_count':len(contexts),'carrier_count':len(carriers),'members':8,'records':total_records,'trace_bytes':total_bytes,'context_manifest_sha256':sha256(a.context_manifest),'carrier_manifest_sha256':master,'bank_digests':digests}
    a.out.write_text(json.dumps(payload,indent=2));print(json.dumps({k:v for k,v in payload.items() if k!='bank_digests'},indent=2))
if __name__=='__main__':main()
