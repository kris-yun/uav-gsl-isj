from pathlib import Path
import hashlib,json,sys

PROJECT=Path(__file__).resolve().parents[2]
OUT=PROJECT/'results/same_height_three_source_20261023'
NATIVE=PROJECT/'native'
sys.path.insert(0,str(NATIVE));sys.path.insert(0,str(PROJECT/'src'))
sys.path.insert(0,str(NATIVE/'observability_20261023'))
GUEST='/home/zyc/ros2_ws/research_runs/v7_sameheight3_20261023'
BUILD='/home/zyc/ocb_r2_seeded_gaden'
BINARY=BUILD+'/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator'
ELF_SHA='ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','-i','C:/Users/50176/.ssh/id_ed25519_vm','zyc@192.168.111.128']

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def write(name,value):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def config():return json.loads((OUT/'PROTOCOL.json').read_text())
