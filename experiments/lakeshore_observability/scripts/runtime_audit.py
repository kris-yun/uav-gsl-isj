"""Read-only audit of the existing VM; never installs or edits runtime packages."""
import subprocess, pathlib, json, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'evidence/lakeshore_observability_r0_r2'
OUT.mkdir(parents=True,exist_ok=True)
commands={
 'runtime': 'source /opt/ros/humble/setup.bash; source ~/ros2_ws/install/setup.bash; uname -a; echo ROS_DISTRO=$ROS_DISTRO; ros2 pkg list | grep gaden; python3 -m pip show gadentools; python3 -c "import importlib.util; print(importlib.util.find_spec(\"gaden_py\"))"',
 'core': 'git -C ~/ros2_ws/src/GADEN rev-parse HEAD; git -C ~/ros2_ws/src/GADEN status --short; git -C ~/ros2_ws/src/GADEN/gaden_common/third_party/gaden_core rev-parse HEAD; cat ~/ros2_ws/src/GADEN/gaden_common/third_party/gaden_core/include/gaden/core/GadenVersion.hpp; cat ~/ros2_ws/src/GADEN/gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp',
 'parser': 'sed -n "55,140p" ~/ros2_ws/src/GADEN/gaden_common/third_party/gaden_core/src/Preprocessing.cpp; cat ~/ros2_ws/src/GADEN/test_env/launch/gaden_preproc_launch.py',
 'seeded_build': 'git -C ~/PF_DEI_V3_GADEN_BUILD/src/GADEN rev-parse HEAD; git -C ~/PF_DEI_V3_GADEN_BUILD/src/GADEN/gaden_common/third_party/gaden_core rev-parse HEAD; cat ~/PF_DEI_V3_GADEN_BUILD/src/GADEN/gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp; sha256sum ~/PF_DEI_V3_GADEN_BUILD/install/lib/libgaden.so; grep -n "InitializeRandom" ~/PF_DEI_V3_GADEN_BUILD/src/GADEN/gaden_common/third_party/gaden_core/src/RunningSimulation.cpp; ls ~/PF_DEI_V3_GADEN_BUILD/install/lib/gaden_filament_simulator',
}
for key,cmd in commands.items():
 r=subprocess.run(['ssh','-o','BatchMode=yes','zyc@192.168.111.128',cmd],capture_output=True,text=True)
 (OUT/f'runtime_{key}.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
house=pathlib.Path(r'D:\ZYC\A-gas\workspace\GADEN_files\scenarios\House01\wind_simulations\2,4-1_fast\2,4-1_fast_0.csv')
with house.open() as f: lines=[next(f) for _ in range(20)]
(OUT/'runtime_house_wind_header.txt').write_text(''.join(lines))
(OUT/'runtime_audit.md').write_text('''# Existing GADEN runtime audit

ROS 2 Humble; installed gadentools 0.1.0 (playback only). GADEN source commit 17adaf650a4f11d29aa049cf0661e9f9ea2e636f; gaden_core commit 9e93c36ae1af74f6a62c42f1c9d7b813153222ed; core format version 3.0. Source trees have historical local modifications: see captured status. gaden_py/cppyy bindings are unavailable; no installation or upgrade performed.

House input header: `U:0,U:1,U:2,Points:0,Points:1,Points:2` (velocity m/s, position m). Native `Preprocessing::ParseOpenFoamVectorCloud` accepts velocity-first or point-first six-column CSV; points map to occupancy cells. Regular cell-centre coordinates avoid lossy nearest-cell aggregation. Existing ROS frontend entry: `test_env/launch/gaden_preproc_launch.py`. Main overlay currently exports common/messages, not a preprocessing executable.

Selected adapter family: **ros2_gaden**, using a minimal C++ command-line adapter linked to an already-built GADEN core library. It calls the installed native preprocessing and query APIs; it does not implement replacement gas physics. Numerical wind parity remains a mandatory N0 gate after R0_GO.

Main core RNG is default-constructed mt19937 without an exposed seed. Existing isolated PF_DEI_V3_GADEN_BUILD has a pre-existing seed interface (`GADEN_RNG_SEED`); reuse only after captured provenance and an actual repeatability check. Neither source tree nor House runtime is edited. New adapter builds/output go to a separate experiment directory. No House experiments are rerun.
''',encoding='utf-8')
print('Runtime audit captured:',OUT)
