"""Compile only experiment adapter against unchanged pre-existing libgaden."""
import pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=ROOT/'evidence/lakeshore_observability_r0_r2';SRC=pathlib.Path(__file__).parent/'gaden_adapter.cpp'
remote='/home/zyc/lakeshore_observability_20261003'
subprocess.run(['ssh','zyc@192.168.111.128','mkdir -p '+remote],check=True)
subprocess.run(['scp',str(SRC),'zyc@192.168.111.128:'+remote+'/adapter.cpp'],check=True)
cmd='''source /opt/ros/humble/setup.bash
python3 - <<'PY'
import pathlib,shlex,subprocess
base=pathlib.Path('/home/zyc/PF_DEI_V3_GADEN_BUILD')
flags=(base/'build/gaden_common/third_party/gaden_core/CMakeFiles/gaden.dir/flags.make').read_text().splitlines()
includes=next(x.split(' = ',1)[1] for x in flags if x.startswith('CXX_INCLUDES'))
bsc=base/'build/gaden_common/third_party/gaden_core/third_party/libbsc'
cmd=['g++','-std=c++20','-O3','-fopenmp','-DGADEN_ROS=1']+shlex.split(includes)+['/home/zyc/lakeshore_observability_20261003/adapter.cpp','-L'+str(base/'install/lib'),'-Wl,-rpath,'+str(base/'install/lib'),'-Wl,-rpath,'+str(bsc),'-Wl,-rpath-link,'+str(bsc),'-lgaden','-o','/home/zyc/lakeshore_observability_20261003/adapter']
r=subprocess.run(cmd,capture_output=True,text=True); print(r.stdout+r.stderr);raise SystemExit(r.returncode)
PY'''
r=subprocess.run(['ssh','zyc@192.168.111.128',cmd],capture_output=True,text=True);msg=r.stdout+r.stderr;code=r.returncode;(OUT/'adapter_build_log.txt').write_text(msg);print('adapter build exit',code,msg[-3000:]);raise SystemExit(code)
