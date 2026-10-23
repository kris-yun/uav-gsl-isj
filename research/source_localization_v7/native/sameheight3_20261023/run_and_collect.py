"""Bounded sequential generation and immutable native gas archives."""
from pathlib import Path
import json,subprocess,sys,time,shutil,shlex
from protocol import *

def run(stage):
 c=config();assert json.loads((OUT/'IDENTITY_GATE.json').read_text())['status'].startswith('PASS_')
 if stage=='dev':
  freeze=json.loads((OUT/'SELECTION_FREEZE.json').read_text());model=json.loads((OUT/'MODEL_FREEZE.json').read_text())
  assert model['selection_sha256']==sha(OUT/'SELECTION_FREEZE.json')
  auth={'one_development_check':True,'selection_sha256':sha(OUT/'SELECTION_FREEZE.json'),
  'model_freeze_sha256':sha(OUT/'MODEL_FREEZE.json'),'protocol_sha256':sha(OUT/'PROTOCOL.json')}
  for extra in ('MIRROR_MODEL_FREEZE.json','UNKNOWN_SINGLE_CONTROL_FREEZE.json','MIRROR_USER_STEERING_ADDENDUM.json'):
   assert (OUT/extra).exists(),extra
   auth[extra+'_sha256']=sha(OUT/extra)
  write('DEV_AUTHORIZATION.json',auth)
  subprocess.run(['scp','-i','C:/Users/50176/.ssh/id_ed25519_vm',str(OUT/'DEV_AUTHORIZATION.json'),
  'zyc@192.168.111.128:'+GUEST+'/DEV_AUTHORIZATION.json'],check=True)
 repeats=(1,2) if stage=='train' else (3,4)
 for source in ('B','C'):
  for repeat in repeats:
   key=f'v7h3_{source}_r{repeat:02d}';archive=OUT/'raw_archives'/(key+'.tar.gz')
   assert not archive.exists(),'do not silently repeat completed generation'
   assert shutil.disk_usage('D:/').free>=c['minimum_free_disk_before_run_bytes']
   log=OUT/'logs'/(key+'.host_generation.log');log.parent.mkdir(parents=True,exist_ok=True)
   started=time.monotonic()
   with log.open('wb') as f:
    proc=subprocess.run(SSH+['python3 '+GUEST+'/run_guest.py '+source+' '+str(repeat)],stdout=f,stderr=subprocess.STDOUT)
   if proc.returncode:raise RuntimeError('first generation failure retained: '+key+' '+str(proc.returncode))
   archive.parent.mkdir(exist_ok=True)
   remote='tar -C '+shlex.quote(GUEST+'/runs')+' --exclude='+shlex.quote(key+'/wind')+' -czf - '+shlex.quote(key)
   with archive.open('wb') as f,(OUT/'logs'/(key+'.archive_stderr.log')).open('wb') as err:
    subprocess.run(SSH+[remote],stdout=f,stderr=err,check=True)
   elapsed=time.monotonic()-started
   write('archives/'+key+'.json',{'run_id':key,'archive':str(archive.relative_to(OUT)),
     'sha256':sha(archive),'bytes':archive.stat().st_size,'host_generation_and_transfer_wall_s':elapsed,
     'wind_snapshot_copies_not_duplicated':True,'wind_content_reference':c['expected_wind'],
     'source':source,'repeat':repeat,'split':stage})
   print('ORIGINAL_WORLD_ARCHIVED',key,'wall',round(elapsed,2),'bytes',archive.stat().st_size,flush=True)
 print('BOUNDED_GENERATION_STAGE_COMPLETE',stage,flush=True)

if __name__=='__main__':
 assert sys.argv[1:] in (['train'],['dev'])
 run(sys.argv[1])
