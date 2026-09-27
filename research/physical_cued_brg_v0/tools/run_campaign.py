#!/usr/bin/env python3
"""Run an EXISTING VM closed-loop harness without guessing its executable.

The explicit argv in campaign.json must accept --case-file etc as appropriate.
No shell, no automatic plume generation, no truth fields sent to neural sidecar.
A prepared case may refer to a preserved plume replay. Infrastructure failures
stop campaign assembly; don't silently evaluate successful cases only.
"""
import argparse,json,subprocess,hashlib,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--campaign',required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
 path=Path(a.campaign);cfg=json.loads(path.read_text())
 for k in ['arms','cases','harness_argv','output_directory','radius_m','budget_s','weights_sha256','bank_sha256','observation_contract_id']:
  if k not in cfg:raise ValueError(f'missing {k}')
 if not cfg['cases'] or not cfg['harness_argv'] or any('<' in str(v) for v in cfg['harness_argv']):raise ValueError('explicit existing harness and cases required')
 out=Path(cfg['output_directory']);out.mkdir(parents=True,exist_ok=True)
 lock=hashlib.sha256(path.read_bytes()).hexdigest()
 if (out/'campaign.sha256').exists() and (out/'campaign.sha256').read_text().strip()!=lock:raise ValueError('campaign changed: choose a new output directory/version')
 (out/'campaign.sha256').write_text(lock+'\n')
 results=[]
 for c in cfg['cases']:
  for arm in cfg['arms']:
   case_id=c['case_id'];dest=out/f'{case_id}__{arm}.json'
   if dest.exists():raise FileExistsError(f'no silent reuse: {dest}')
   argv=[v.format(arm=arm,case_file=c['case_file'],output=str(dest),budget_s=cfg['budget_s']) for v in cfg['harness_argv']]
   print(json.dumps({'argv':argv}),flush=True)
   if a.execute:
    start=time.monotonic();run=subprocess.run(argv,timeout=cfg.get('wall_timeout_s',7200),check=False)
    if run.returncode!=0 or not dest.exists():raise RuntimeError(f'harness failed for {case_id}/{arm}; keep logs and stop, no scientific partial result')
    record=json.loads(dest.read_text())
    if record['case_id']!=case_id or record['arm']!=arm:raise ValueError('harness identity mismatch')
    record['orchestrator_wall_s']=time.monotonic()-start;results.append(record)
 if a.execute:(out/'all_results.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in results))
if __name__=='__main__':main()
