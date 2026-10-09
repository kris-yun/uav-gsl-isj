from pathlib import Path
import subprocess,json,hashlib
task=Path('/home/zyc/pmfs_wind_one_update_r2_20261009')
commands=json.loads((task/'build_commands.json').read_text())
base=Path('/home/zyc/ros2_ws/build/gmrf_wind_mapping')
commands[-1]=[str(base/x) if not x.startswith(('-','/')) and (base/x).is_file() else x for x in commands[-1]]
(task/'build_commands.json').write_text(json.dumps(commands,indent=2))
with (task/'build.log').open('a') as log:p=subprocess.run(commands[-1],stdout=log,stderr=log,timeout=45)
if p.returncode:print((task/'build.log').read_text()[-2000:]);raise SystemExit(p.returncode)
result=dict(verdict='PASS',executables={n:hashlib.sha256((task/n).read_bytes()).hexdigest() for n in ['pmfs_wind_probe','gmrf_wind_observed']})
(task/'BUILD_RESULT.json').write_text(json.dumps(result))
repo=Path('/home/zyc/ros2_ws/src/GMRF-wind')
source=repo/'gmrf_wind_mapping/gmrf_wind_core/src/gmrf_map.cpp'
rel=source.relative_to(repo).as_posix()
gitdata=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+rel])
metadata=dict(core_map_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),core_map_matches_pinned_git=source.read_bytes()==gitdata,
    gmrf_shared_library_sha256=hashlib.sha256((base/'gmrf_wind_core/libgmrf_wind_core.so').read_bytes()).hexdigest(),
    core_library_source_to_ELF_claim='existing compiled shared library reused; SHA frozen; no full clean-build binary parity asserted')
(task/'CORE_LIBRARY_BINDING.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(result));print(json.dumps(metadata))
