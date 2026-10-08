"""Windows-only materialization of the exact frozen arrays; zero simulation."""
from pathlib import Path
import csv,datetime,hashlib,json,shutil,struct,sys,zipfile,importlib.util
import numpy as np
ROOT=Path(__file__).resolve().parent;FROZEN=ROOT.parent/'m0_clean_support_r0_20261007'
REMOTE='/home/zyc/ros2_ws/m0_clean_support_r0_20261007'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def read(n):return json.loads((FROZEN/n).read_text(encoding='utf-8'))
stage=ROOT/'staging';stage.mkdir(exist_ok=True)
if (ROOT/'ASSET_MANIFEST.json').exists():raise RuntimeError('Assets already materialized; do not overwrite.')
with (FROZEN/'M0_R0_FILES_SHA256.csv').open(encoding='utf-8') as f:
    for r in csv.DictReader(f):assert sha(FROZEN/r['path'])==r['sha256']
spec=importlib.util.spec_from_file_location('frozen_math',FROZEN/'static_design_math.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
S=read('M0_SOURCE_CONTRACT.json');D=read('M0_DOMAIN_ROI_GUARD_CONTRACT.json');P=read('M0_PERTURBATION_CONTRACT.json')
with (FROZEN/'M0_RUNLIST_PREVIEW.csv').open(encoding='utf-8') as f:runs=list(csv.DictReader(f))
assert len(runs)==40 and all(r['wind_arm']=='U0' for r in runs[:8])
base,ag,bg=m.field_recipes();n=D['grid_dimensions_xyz'];cells=np.zeros((n[2],n[1],n[0]),dtype=np.uint8)
cells[[0,-1],:,:]=2;cells[:,[0,-1],:]=2;cells[:,:,[0,-1]]=2
occ=stage/'OccupancyGrid3D.csv'
with occ.open('w',encoding='ascii',newline='') as f:
    f.write('#env_min(m) -16 -20 -8\n#env_max(m) 44 20 16\n#num_cells 240 160 96\n#cell_size(m) 0.25\n')
    for z in range(n[2]):
        for x in range(n[0]):f.write(' '.join(map(str,cells[z,:,x]))+'\n')
        if z<n[2]-1:f.write(';\n')
for arm in P['arms']:
    project=stage/'projects'/arm;(project/'wind').mkdir(parents=True,exist_ok=True);(project/'scenes').mkdir(exist_ok=True);(project/'simulations').mkdir(exist_ok=True)
    shutil.copyfile(occ,project/occ.name)
    (project/'config.yaml').write_bytes(b'models: []\noutlets_models: []\nunprocessed_wind_files: ""\nempty_point: [0, 0, 5]\ncell_size: 0.25\nuniformWind: false\n')
    field=m.make_field(arm,base,ag,bg);wind=project/'wind'/'wind_iteration_0'
    wind.write_bytes(struct.pack('<ii',3,0)+field.tobytes(order='C'));assert sha(wind)==P['expected_modern_wind_sha256'][arm]
for r in runs[:8]:
    cfg=stage/'projects/U0/simulations'/r['run_id']/'sim.yaml'
    text=f'''source:
  sourceType: point
  position: [{r['x_m']}, {r['y_m']}, {r['z_m']}]
  gasType: 12
deltaTime: 0.1
windIterationDeltaTime: 1.0
temperature: 298.0
pressure: 1.0
filamentPPMcenter: 10.0
filamentInitialSigma: 10.0
filamentGrowthGamma: 15.0
filamentNoise_std: 0.01
numFilaments_sec: 10.0
expectedNumIterations: 1400
saveResults: true
saveDeltaTime: 0.5
preCalculateConcentrations: false
windLooping:
  loop: false
  from: 0
  to: 0
'''
    cfg.parent.mkdir(parents=True);cfg.write_bytes(text.encode('ascii'))
    r['effective_output_path']=REMOTE+'/projects/U0/simulations/'+r['run_id']+'/result'
    r['argv']=[ '/home/zyc/ocb_r2_seeded_gaden/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator','--ros-args','-p','projectPath:='+REMOTE+'/projects/U0','-p','simulationID:='+r['run_id'],'-p','sim_time:=140.0','-p','limitRate:=false','-p','verbose:=false','-r','__node:='+r['run_id']]
files=[{'path':p.relative_to(stage).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(stage.rglob('*')) if p.is_file()]
manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'remote_root':REMOTE,'asset_files':files,'base_runs_only':runs[:8],'scientific_budget_this_turn':8,'scientific_runs_at_materialization':0,'intervention_authorized':False,'field_sha256':P['expected_modern_wind_sha256'],'occupancy_sha256':sha(occ),'runtime_contract':S['runtime'],'frozen_dir_sha256':sha(FROZEN/'M0_R0_FREEZE.json'),'math_script_sha256':sha(FROZEN/'static_design_math.py'),'math_numpy_version':np.__version__,'runtime_entry':'Frozen generator native project/YAML path; legacy ROS temperature mapping is bypassed without modifying binaries.'}
write(ROOT/'ASSET_MANIFEST.json',manifest);shutil.copyfile(ROOT/'ASSET_MANIFEST.json',stage/'ASSET_MANIFEST.json')
(ROOT/'M0_AUTHORIZATION_E0_E1.json').write_bytes((json.dumps({'scope':'E0 runtime-only + exactly eight U0 baseline rows; then STOP','user_authorized':True,'R0_unchanged':True,'science_runs_max':8,'E2_authorized':False,'wrong_wind_runs_authorized':0,'planned_future_sentinel':'S0 realization 1, arms A_on/A_off/B_shear/B_speed already in runlist; requires future authorization','handoff_review_head':'dacb4dd68e16417d01c224a088e3c67c76995cd0'},indent=2)+'\n').encode())
archive=ROOT/'M0_E0_ASSETS.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(stage.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(stage).as_posix())
print(json.dumps({'assets':len(files),'native_winds':5,'asset_zip_bytes':archive.stat().st_size,'asset_zip_sha256':sha(archive),'science_runs':0,'baseline_runlist_count':8},indent=2))
