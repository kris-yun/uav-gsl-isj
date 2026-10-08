from pathlib import Path
import hashlib,json,shlex,subprocess
R=Path('/home/zyc/ros2_ws/m0_clean_support_r0_20261007');B=Path('/home/zyc/ocb_r2_seeded_gaden')
lines=(B/'build/gaden_common/third_party/gaden_core/CMakeFiles/gaden.dir/flags.make').read_text().splitlines();inc=next(q.split(' = ',1)[1] for q in lines if q.startswith('CXX_INCLUDES'));lib=B/'install/gaden_common/lib';bsc=B/'build/gaden_common/third_party/gaden_core/third_party/libbsc'
argv=['g++','-std=c++20','-O3','-DGADEN_ROS=1',*shlex.split(inc),str(R/'native_e1_audit.cpp'),'-L'+str(lib),'-Wl,-rpath,'+str(lib),'-Wl,-rpath,'+str(bsc),'-Wl,-rpath-link,'+str(bsc),'-lgaden','-o',str(R/'bin/native_e1_audit')]
with (R/'e1_helper_build.log').open('wb') as f:subprocess.run(argv,check=True,stdout=f,stderr=subprocess.STDOUT)
(R/'E1_HELPER_BUILD.json').write_text(json.dumps({'argv':argv,'source_sha256':hashlib.sha256((R/'native_e1_audit.cpp').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256((R/'bin/native_e1_audit').read_bytes()).hexdigest(),'libgaden_unchanged':True,'science_runs':0},indent=2)+'\n')
print('E1_READ_ONLY_HELPER_BUILT_NO_SIMULATION')
