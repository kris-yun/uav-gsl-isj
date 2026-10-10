"""Produce auditable tables and a non-recursive delivery from this child audit."""
import csv,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(name,a,b=None):return f'source/{name}:{a}'+(f'-{b}' if b else '')
R=[]
def row(item,p,g,ps,gs,impact,boundary):
    R.append(dict(item=item,PMFS_actual=p,GADEN_actual=g,PMFS_source=ps,GADEN_source=gs,potential_effect_chain=impact,inference_boundary=boundary))
row('emission_rate','5 centres/step; record 50/s, warmup25/s','7/s; fractional accumulator floor',lines('Simulations_native_with_state_access.cpp',291,384),lines('RunningSimulation.cpp',116,138),'particle stock -> occupancy saturation -> candidate scores','Neither has a scientifically interchangeable release-rate/ppm calibration')
row('source_region','native uniform fresh leaf draw; C7 coarse5x1=.3125m2, K2 fine1x1=.0625m2; Point mode available','point XYZ for both M2 candidates z=-.5',lines('Simulations_native_with_state_access.cpp',387,399),lines('PointSource.hpp',1,50),'region mixing -> simulated plume diversity -> ranking','Point-source exact truth is oracle diagnosis, not deployment input')
row('state','Vector2 filament centre only','Vector3 centre + sigma in cm; total moles constant',lines('Simulations_native_with_state_access.cpp',276,283),lines('Filament.hpp',7,19),'missing Z/age/size/mass -> no 2D ppm operator','A fixed full-field blur exists; do not say no Gaussian at all')
row('wind_height_and_projection','0.25m cell centres; actual anemometerZ=-.2; u/v only','0.1m actual XYZ voxel u/v/w + zero-initialized disturbances',lines('PMFSLib.cpp',295,349),lines('RunningSimulation.cpp',107,113),'Z evolution -> horizontal wind changes -> projected transition depends on hidden state','447 saved u/v values match native queries exactly; this is not a z=0 input bug')
row('noise_record','STD .2m/s times dt .1 = .02m x/y','YAML .02 times constructor10 times dt.1 = .02m x/y/z',lines('Simulations_native_with_state_access.cpp',276,283),lines('RunningSimulation.cpp',16,26)+';'+lines('RunningSimulation.cpp',198,202),'GADEN z noise changes altitude; horizontal per-step scale already matches','Do not interpret YAML .02 vs PMFS .2 as tenfold horizontal noise mismatch')
row('noise_warmup','STD .2m/s times dt .2 = .04m x/y','same .02m every dt .1 step',lines('Simulations_native_with_state_access.cpp',330),lines('RunningSimulation.cpp',198,202),'different warmup random displacement increments -> plume initialization','Descriptive difference, not isolated root cause')
row('buoyancy','absent','gas13 smoke; SpecificGravity=.89; initial10ppm gives +.0379822m/s; decays with sigma^-3',lines('Simulations_native_with_state_access.cpp',276,283),lines('RunningSimulation.cpp',176,195)+';'+lines('GasTypes.hpp',36,50),'z drift -> different subsequent u/v and geometry -> occupancy','Initial velocity is not constant throughout filament lifetime')
row('growth','no per-filament sigma or mass','initial10cm; gamma15cm2/s; sigma+=gamma/(2sigma)*dt',lines('Simulations_native_with_state_access.cpp',291,384),lines('RunningSimulation.cpp',214,220),'shape expands, centre ppm decays -> receptor hit semantics','Observed pooled sigma range10.075-90.065cm does not measure independent realizations')
row('wall_and_exit','same-cell/visible-end exact; fallback <=.125m floor/trunc steps, obstacle backtrack, no slide; any outside2D deleted','ceil(distance/.1), obstacle/out-of-bound backtrack plus recursive tangential residual; only Outlet deletes',lines('Simulations_native_with_state_access.cpp',402,458)+';'+lines('Simulations_native_with_state_access.cpp',285,289),lines('RunningSimulation.cpp',228,280),'wall residence and path access -> centre field -> likelihood','USE_DDA=0; inactive .7 rule not executed; locked vmath projection retained')
row('warmup_and_horizon','all6 M1 forwards200warmup*.2=40s, 200record*.1=20s; new empty plume each call','physical time0 continuous emission; saved receivers322.9166-534.0861s',lines('Simulations_native_with_state_access.cpp',291,384),'M2 QUERY_PHYSICAL_LINEAGE.csv; M1 RESULT.json','history/age mixture -> state distribution -> candidate score','Bool warmup argument does not disable native block; static current wind does not erase history')
row('time_order','emit -> record cell occupancy -> move','emit -> move/grow -> save -> wind advance -> clock increment',lines('Simulations_native_with_state_access.cpp',350,377),lines('RunningSimulation.cpp',75,102),'phase shifts differ between centre-state and concentration readout','No time-alignment repair fabricated in this audit')
row('readout','per cell per timestep max1 centre hit; divide200; field blur1.5cells=.375m','3D Gaussian contributions/ppm with strict3sigma support and LOS; sumfloat in stored order',lines('Simulations_native_with_state_access.cpp',356,384)+';'+lines('Simulations_native_with_state_access.cpp',510,522),lines('Simulation.cpp',6,81),'operator semantics -> thresholds and source-conditioned maps','Do not invent mass/sigma for PMFS and call it a native PID operator')
row('scoring','D=.4; product over447free spatial cells: 1-D*confidence*abs(measuredProb-hitMap)','native physical ppm becomes thresholded event and is separately map-replayed',lines('Simulations_native_with_state_access.cpp',236,271),lines('Simulation.cpp',34,81),'spatial propagation dependence -> effective evidence repetition','Grid cells are not independent physical measurements; observed weighting effect not yet exclusive root cause')
row('random_cache','thread-local PrecalculatedGaussian<2500>;2axes + uniform leaf release','thread-local PrecalculatedGaussian<1000>;3axes; M2 seeded wrapper preserves default draw path',lines('Simulations_native_with_state_access.cpp',26),lines('RunningSimulation.cpp',14),'dimension/path-dependent draw consumption -> different trajectories','Same seed across two different simulators does not imply same trajectory-noise coupling')
row('geometry_support','2D native free447/1530; same source projection accepted','3D native free at actual centre; voxel support differs by height','M1 snapshot/input.csv','M2 OccupancyGrid3D.csv and392snapshots','3D legal pathways may project through2D nonfree support -> blocked2D trajectories','Do not add truth-labelled free cells or alter frozen geometry to manufacture improvement')
with (W/'FORWARD_CONTRACT_DIFFERENCE_TABLE.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(R[0]));w.writeheader();w.writerows(R)
prov=[]
remote='/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/src/gaden_common/third_party/gaden_core'
remotenames={}
for name in ['SOURCE_HASHES.json','GAS_CONFIGURATION_HEADER_HASHES.json']:
    remotenames.update(json.loads((W/'source'/name).read_text()))
for line in (W/'M3_WIND_SOURCE_CAPTURE.stdout').read_text().splitlines():
    if line.startswith('{'):
        r=json.loads(line);remotenames[r['name']]=r['sha256']
for rp,h in remotenames.items():
    local=W/'source'/Path(rp).name;assert local.exists() and sha(local)==h
    prov.append(dict(local_path=str(local.relative_to(W)).replace('\\','/'),original_path=remote+'/'+rp,SHA256=h,method='read-only VM source capture; exact bytes'))
local_origins={
 'Simulations_native_with_state_access.cpp':'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010/source/Simulations_native_with_state_access.cpp',
 'PMFSLib.cpp':'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010/frozen_M0/evidence/source/gsl/PMFS/PMFSLib.cpp',
 'Grid2D.hpp':'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010/frozen_M0/evidence/source/gsl/Common/Grid2D.hpp',
 'PMFS_Math.hpp':'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010/evidence/sdk/include/gsl_server/algorithms/Common/Utils/Math.hpp',
 'verify_raw_receiver_queries.py':'work/pmfs_m2_observation_discrimination_20261010/independent_raw_query_verify/verify_raw_receiver_queries.py'}
for local,rp in local_origins.items():
    assert sha(W/'source'/local)==sha(ROOT/rp)
    prov.append(dict(local_path='source/'+local,original_path=rp,SHA256=sha(W/'source'/local),method='copy of frozen local source; exact bytes'))
(W/'SOURCE_PROVENANCE.json').write_text(json.dumps(dict(qualification='LOCKED_RUNNING_SOURCE_TEXT_AND_FROZEN_COPY_NOT_RECLAIMED_AS_UNINSTRUMENTED_UPSTREAM',sources=prov),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
dest=W/'delivery'
assert dest.resolve().is_relative_to(W.resolve())
dest.mkdir(exist_ok=True)
files=[p for p in W.rglob('*') if p.is_file() and not set(['delivery','verification_repeat','__pycache__']).intersection(p.relative_to(W).parts)]
for p in files:
    t=dest/p.relative_to(W);t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,t)
manifest=[]
for p in sorted(dest.rglob('*')):
    if p.is_file() and p.name!='SHA256SUMS.csv':manifest.append(dict(path=str(p.relative_to(dest)).replace('\\','/'),bytes=p.stat().st_size,SHA256=sha(p)))
with (dest/'SHA256SUMS.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['path','bytes','SHA256']);w.writeheader();w.writerows(manifest)
assert all(sha(dest/r['path'])==r['SHA256'] for r in manifest)
print(json.dumps(dict(delivery=str(dest.resolve()),files=len(manifest),bytes=sum(r['bytes'] for r in manifest),manifest_SHA256=sha(dest/'SHA256SUMS.csv')),ensure_ascii=False))
