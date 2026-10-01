"""Read-only P0 source/header provenance; no concentration or ranking computation."""
import argparse,hashlib,json,struct,tarfile,zlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists();a.out.mkdir(parents=True)
paths=[Path('/home/zyc/ocb_r1_historical_gaden_rebuild/source/gaden_filament_simulator/src/filament_simulator.cpp'),Path('/home/zyc/ocb_r1_historical_gaden_rebuild/source/gaden_filament_simulator/src/filament.cpp'),Path('/home/zyc/ros2_ws/src/GADEN/gaden_common/third_party/gaden_core/src/Simulation.cpp'),Path('/home/zyc/ros2_ws/src/GADEN/gaden_common/third_party/gaden_core/src/RunningSimulation.cpp'),Path('/home/zyc/ros2_ws/src/GADEN/gaden_common/third_party/gaden_core/src/PlaybackSimulation.cpp')]
manifest=[];snapshots=[]
sha=lambda data:hashlib.sha256(data).hexdigest()
def save(path,data=None):
 if data is None:data=path.read_bytes()
 dst=a.out/'sources'/path.as_posix().lstrip('/');dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
 manifest.append({'original_path':str(path),'retained_copy':str(dst.relative_to(a.out)),'bytes':len(data),'sha256':sha(data)})
for path in paths:save(path)
for house,config,source in [('House01','2,4-1_fast','-0.40_-2.90_-0.30'),('House02','3,5-1_fast','0.00_-1.00_0.20')]:
 root=Path('/mnt/hgfs/workspace/GADEN_files/scenarios')/house
 for filename in ['GADEN_ros1.launch','GADEN_ros2.launch']:save(root/'launch'/config/filename)
 directory=root/'gas_simulations'/config/('FilamentSimulation_gasType_10_sourcePosition_'+source)
 for iteration in (0,1,2,10):
  path=directory/('iteration_'+str(iteration));data=path.read_bytes();raw=zlib.decompress(data)
  version=struct.unpack_from('<i',raw,0)[0];assert version==1
  moles,airmoles=struct.unpack_from('<dd',raw,116)
  records=[struct.unpack_from('<i4d',raw,off) for off in range(136,len(raw)-35,36)]
  assert (len(raw)-136)%36==0
  sigmas=[r[4] for r in records]
  snapshots.append({'house':house,'iteration_id':iteration,'path':str(path),'sha256':sha(data),'compressed_bytes':len(data),'raw_bytes':len(raw),'version':version,'gas_type':struct.unpack_from('<i',raw,112)[0],'total_moles_per_filament':moles,'all_gas_moles_per_cm3':airmoles,'filament_count':len(records),'sigma_cm_min':min(sigmas) if sigmas else None,'sigma_cm_max':max(sigmas) if sigmas else None,'sigma_first_12':sigmas[:12]})
  save(path,data)
archive=Path('/mnt/hgfs/workspace/TNQC_R2_SIX_OFFLINE_20260921_authoritative/freeze/exact_b24_source.tar.gz')
with tarfile.open(archive) as t:
 for name in ['ros2_package/src/gsl_server/algorithms/Common/Algorithm.cpp','ros2_package/src/gsl_server/algorithms/Common/States/StopAndMeasureState.cpp']:
  data=t.extractfile(name).read();save(Path('/FROZEN_EXACT_B24_SOURCE')/name,data)
(a.out/'RAW_HEADER_AUDIT.json').write_text(json.dumps(snapshots,indent=2,sort_keys=True,allow_nan=False)+'\n')
(a.out/'REMOTE_SOURCE_SHA256.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print(json.dumps(snapshots,indent=2))
