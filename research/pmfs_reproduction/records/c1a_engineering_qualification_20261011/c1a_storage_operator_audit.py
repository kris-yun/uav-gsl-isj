import pathlib,subprocess,json,hashlib,time,uuid
from datetime import datetime,timezone
BASE=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/'outputs/PMFS_C1A_ENGINEERING_QUALIFICATION_20261011';SHARE=pathlib.Path('D:/ZYC/A-gas/workspace/PMFS_C1A_ENGINEERING_20261011')
def remote(s):
    return subprocess.run(['ssh','-T','-i','C:/Users/50176/.ssh/id_ed25519_vm','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=6','-o','StrictHostKeyChecking=yes','zyc@192.168.111.128','python3 -'],input=s,text=True,encoding='utf-8',capture_output=True,timeout=30)
def main():
    start=time.monotonic();SHARE.mkdir(exist_ok=True);token=uuid.uuid4().hex;data=('C1A_SHARED_MAPPING_'+token).encode();p=SHARE/'HOST_WRITE_PROBE.bin';assert not p.exists();p.write_bytes(data);expected=hashlib.sha256(data).hexdigest()
    script='''import pathlib,json,hashlib,shutil
p=pathlib.Path('/mnt/hgfs/workspace/PMFS_C1A_ENGINEERING_20261011');f=p/'HOST_WRITE_PROBE.bin';expected=EXPECT
actual=hashlib.sha256(f.read_bytes()).hexdigest();assert actual==expected
reply=('VM_READ_MATCH_'+actual).encode();(p/'VM_WRITE_PROBE.bin').write_bytes(reply)
print(json.dumps({'VM_path':str(p),'host_marker_sha256':actual,'reply_sha256':hashlib.sha256(reply).hexdigest(),'free_bytes':shutil.disk_usage(p).free,'round_trip':'PASS'}))
'''.replace('EXPECT',repr(expected))
    r=remote(script);assert r.returncode==0,r.stderr;reply=json.loads(r.stdout);assert hashlib.sha256((SHARE/'VM_WRITE_PROBE.bin').read_bytes()).hexdigest()==reply['reply_sha256'];(OUT/'C1A_SHARED_STORAGE_PASS.json').write_text(json.dumps(reply,indent=2)+'\n',encoding='utf-8')
    script=r'''import pathlib,json,hashlib
root=pathlib.Path('/home/zyc/ros2_ws/src/GADEN')
names=['gaden_common/third_party/gaden_core/include/gaden/RunningSimulation.hpp','gaden_common/third_party/gaden_core/include/gaden/Simulation.hpp','gaden_common/third_party/gaden_core/src/RunningSimulation.cpp','gaden_common/third_party/gaden_core/src/Simulation.cpp','gaden_common/third_party/gaden_core/src/PlaybackSimulation.cpp','simulated_gas_sensor/src/fake_gas_sensor.cpp']
d={}
for n in names:
 p=root/n;text=p.read_text(errors='replace');lines=text.splitlines();keys=['advance','iterate','step','wind','concentration','Concentration','RunningSimulation(','getGas','sensor_model','PID','Correction','getConcentration']
 selected=[{'line':i+1,'text':'\n'.join(lines[max(0,i-1):min(len(lines),i+3)])} for i,x in enumerate(lines) if any(k in x for k in keys)]
 d[n]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'lines':len(lines),'selected':selected[:70]}
print(json.dumps(d))
'''
    r=remote(script);assert r.returncode==0,r.stderr;obj=json.loads(r.stdout);(OUT/'C1A_GADEN_OPERATOR_SOURCE_AUDIT.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'C1A_STORAGE_AND_SOURCE_RECEIPT.json').write_text(json.dumps({'UTC':datetime.now(timezone.utc).isoformat(),'wall_s':time.monotonic()-start,'root_writes':0,'shared_marker_bytes':len(data)+(SHARE/'VM_WRITE_PROBE.bin').stat().st_size,'physics_calls':0,'goals':0,'operator_read_only':True},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'shared_roundtrip':'PASS','source_files_read':len(obj),'wall_s':time.monotonic()-start}))
if __name__=='__main__':main()
