from pathlib import Path
import datetime,json,os,psutil
def matching(rows,domain,exclude=()):
 return [r for r in rows if r.get('domain')==str(domain)and r['pid']not in exclude]
def inventory(domain,exclude=()):
 uid=os.getuid();rows=[];unreadable=[];block=[];scanned=0
 for p in psutil.process_iter(['pid','name','username','ppid','create_time','status']):
  if p.pid in exclude:continue
  try:
   realuid=p.uids().real;env=p.environ();scanned+=1
   if 'ROS_DOMAIN_ID'in env:
    rows.append(dict(pid=p.pid,uid=realuid,name=p.info['name'],ppid=p.ppid(),create_time=p.create_time(),status=p.status(),domain=env['ROS_DOMAIN_ID'],command=p.cmdline()))
  except(psutil.NoSuchProcess,psutil.ZombieProcess):continue
  except psutil.AccessDenied:
   try:
    realuid=p.uids().real;name=p.name();parent=p.parent();parent_name=parent.name()if parent else None
    # Login's non-dumpable PAM helper cannot create a ROS graph; retain this
    # explicit system-process exception instead of hiding permission failures.
    pam=(realuid==uid and (name,parent_name)in {('(sd-pam)','systemd'),('fusermount3','xdg-document-portal'),('vmtoolsd','systemd'),('sshd','sshd')})
    r=dict(pid=p.pid,uid=realuid,effective_uid=p.uids().effective,name=name,parent_name=parent_name,command=p.cmdline(),reason='ENVIRONMENT_PERMISSION_DENIED',classification='PROTECTED_SYSTEM_SESSION_HELPER'if pam else 'OTHER_UID_SYSTEM_PROCESS'if realuid!=uid else 'UNRESOLVED_SAME_UID')
    unreadable.append(r)
    if realuid==uid and not pam:block.append(r)
   except(psutil.NoSuchProcess,psutil.ZombieProcess):pass
 hits=matching(rows,domain,exclude)
 return dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),domain=domain,environment_entries_scanned=scanned,all_visible_domain_processes=rows,matching_domain_processes=hits,unreadable=unreadable,blocking_unreadable=block,scope='All readable process environments without executable-name filter; unreadable same-UID unknowns block. Protected PAM and other-UID system environment limits disclosed; direct DDS graph checked separately.',vacant=not hits and not block)
def require_vacant(snapshot,path):
 Path(path).write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
 assert snapshot['vacant'],('DOMAIN_NOT_VACANT',snapshot['matching_domain_processes'],snapshot['blocking_unreadable'])
if __name__=='__main__':
 import sys
 # Regression cases that the previous executable-name guard missed.
 assert matching([dict(pid=1,domain='225',name='lifecycle_manager')],225)
 assert matching([dict(pid=2,domain='225',name='arbitrary_worker')],225)
 assert not matching([dict(pid=3,domain='227',name='lifecycle_manager')],225)
 assert not matching([dict(pid=4,domain='225',name='probe')],225,{4})
 R=Path(__file__).resolve().parent
 require_vacant(inventory(225,exclude={os.getpid()}),R/'DOMAIN_PRECHECK_PROCESS_INVENTORY.json')
 print(json.dumps(dict(status='PASS_ALL_READABLE_PROCESS_ENVIRONMENT_GATE_AND_REGRESSION_CASES',domain=225)))
