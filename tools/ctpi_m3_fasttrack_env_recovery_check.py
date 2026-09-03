#!/usr/bin/env python3
"""Verify that post-bcd56dd changes are VM-environment-only."""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path

SCIENCE_ANCHOR='bcd56dd276e0e29a22399d695203101e7c09022f'
AUTHORIZED_ROOT='/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install'
ALLOWED_CHANGED={
 'tools/ctpi_vm_dependency_qualifier.py',
 'tools/ctpi_m3_fasttrack_env_recovery_check.py',
 'closed_loop/ctpi/prepare_ctpi_m3_fasttrack_vm_20260903.sh',
 'docs/CTPI_M3_FASTTRACK_VM_ENV_RECOVERY_V4_20260903.json',
 'docs/CODEX_CTPI_M3_FASTTRACK_PHASE1_ENV_RECOVERY_V4_20260903.md',
 'docs/CTPI_M3_FASTTRACK_CODEX_HANDOFF_READY_20260903.json',
}

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',type=Path,required=True); ap.add_argument('--output',type=Path); a=ap.parse_args(); root=a.repo_root.resolve(); checks={}
 checks['clean_worktree']=subprocess.run(['git','-C',str(root),'status','--porcelain'],capture_output=True,text=True,check=True).stdout.strip()==''
 checks['science_anchor_is_ancestor']=subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',SCIENCE_ANCHOR,'HEAD']).returncode==0
 changed=set(subprocess.run(['git','-C',str(root),'diff','--name-only',f'{SCIENCE_ANCHOR}..HEAD'],capture_output=True,text=True,check=True).stdout.splitlines())
 checks['environment_only_diff']=bool(changed) and changed.issubset(ALLOWED_CHANGED)
 checks['qualifier_present']=(root/'tools/ctpi_vm_dependency_qualifier.py').is_file()
 prep=(root/'closed_loop/ctpi/prepare_ctpi_m3_fasttrack_vm_20260903.sh').read_text(encoding='utf-8')
 checks['authorized_candidate_frozen']=AUTHORIZED_ROOT in prep
 checks['qualifier_called']='ctpi_vm_dependency_qualifier.py' in prep
 checks['broken_aggregate_setup_not_sourced']='source /home/zyc/ros2_ws/install/setup.bash' not in prep
 checks['compat_overlay_fail_closed']='CTPI_PREP_GADEN_COMPAT_REFUSE_EXISTING_NONLINK' in prep
 contract_path=root/'docs/CTPI_M3_FASTTRACK_VM_ENV_RECOVERY_V4_20260903.json'
 contract=json.loads(contract_path.read_text(encoding='utf-8')) if contract_path.is_file() else {}
 checks['recovery_contract_status']=contract.get('status')=='VM_ENVIRONMENT_RECOVERY_AUTHORIZED'
 checks['recovery_contract_candidate']=contract.get('authorized_gaden_overlay_root')==AUTHORIZED_ROOT
 passed=all(checks.values()); out={'contract':'CTPI_M3_FASTTRACK_ENV_RECOVERY_HANDOFF_V1','science_anchor':SCIENCE_ANCHOR,'changed_files':sorted(changed),'checks':checks,'pass':passed,'verdict':'CTPI_M3_FASTTRACK_ENV_RECOVERY_HANDOFF=PASS' if passed else 'CTPI_M3_FASTTRACK_ENV_RECOVERY_HANDOFF=FAIL'}
 if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(out['verdict'])
 if not passed:
  for k,v in checks.items():
   if not v: print('FAILED='+k)
 return 0 if passed else 2

if __name__=='__main__': raise SystemExit(main())
