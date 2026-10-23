"""Finalize receipts and ZIP; explicit excludes protect raw caches and venvs."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,zipfile
import numpy as np
from recover_assets import ROOT,OUT,PROTO,sha,write

DELIVERY=Path('D:/ZYC/A-gas/_deliverables')
NAME='V7_NATIVE_RECOVERY_M1_BOUNDED_20261023'

def prepare():
    r0=json.loads((OUT/'R0_INPUT_RESULT.json').read_text())
    r1=json.loads((OUT/'R1_EXTRACTION_RESULT.json').read_text())
    fit=json.loads((OUT/'TRAIN_FIT_RECEIPT.json').read_text())
    qa=json.loads((OUT/'INDEPENDENT_QA.json').read_text())
    assert qa['status']=='PASS_WITH_DECLARED_SCIENTIFIC_LIMITS'
    # Compare every recovered world's saved wind against the first saved wind.
    assets=[json.loads((OUT/'assets'/(r['run_id']+'.json')).read_text()) for r in r0['worlds']]
    wind_hashes=[{Path(w['path']).name:w['sha256'] for w in a['wind']} for a in assets]
    assert all(w==wind_hashes[0] for w in wind_hashes)
    write('ALL_WORLD_WIND_IDENTITY.json',{'all_eight_worlds_saved_wind_match':True,'state_count':len(wind_hashes[0]),
          'reference_world':assets[0]['run_id'],'reference_hashes':wind_hashes[0]})
    # PointSource::Emit returns exactly sourcePosition, not an assumed random
    # birth volume. Persist the implementation and its provenance limitation.
    ref=Path('D:/ZYC/A-gas/workspace/E3_APRIME3D_P1_20261019/source_reference')
    target=OUT/'source_reference';target.mkdir(exist_ok=True)
    references=['src/Simulation.cpp','src/WindSequence.cpp','src/Environment.cpp',
                'include/gaden/internal/Serialization.hpp','include/gaden/datatypes/sources/PointSource.hpp']
    hashes={}
    for name in references:
        p=ref/name;q=target/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());hashes[name]=sha(q)
    write('SOURCE_REFERENCE_RECEIPT.json',{'copied_local_reference':str(ref),'files':hashes,
        'original_generator_from_history':{'core_commit':'9e93c36ae1af74f6a62c42f1c9d7b813153222ed',
          'binary_sha256':'ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688'},
        'original_generator_ELF_reverified_this_run':False,
        'equivalent_readout_acceptance':'1200 frozen historical GCC-native concentration comparisons plus occupancy/wind identity',
        'absolute_mol_per_second_or_hardware_PID_certified':False})
    # Preserve all original eight metadata manifests; no gas archive duplicates.
    from recover_assets import run_path
    for run in json.loads(PROTO.read_text())['authorized_runs']:
        for name in ('RUN_MANIFEST.json','RECORD_TIMELINE.tsv'):
            q=OUT/'metadata'/run/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((run_path(run)/name).read_bytes())
    stages=[{'stage':'R0 archive integrity','wall_s':r0['duration_s'],'status':r0['status']},
            {'stage':'R1 readout, wind parity and extraction','wall_s':r1['duration_s'],'status':r1['status']},
            {'stage':'R2 TRAIN-only all models','wall_s':fit['wall_s'],'cpu_s':fit['cpu_s'],'status':'COMPLETE'},
            {'stage':'R2 DEV fixed evaluation','wall_s':json.loads((OUT/'R2_RESULT.json').read_text())['duration_s'],'status':'NO_INDEPENDENT_M1_GAIN'},
            {'stage':'R3 M2/M3 ablations','wall_s':0,'status':'NOT_EXECUTED_SCIENTIFIC_GATE'},
            {'stage':'R4 ROS or active UAV','wall_s':0,'status':'NOT_EXECUTED_SCIENTIFIC_GATE'}]
    write('COSTS.json',{'stages':stages,'peak_RSS_MB':None,'GPU_utilization':None,
           'unmeasured_fields':'not instrumented during first execution; do not fabricate',
           'GPU_required':False,'new_physical_worlds':0,'new_propagation_steps':0,'new_ROS':0})
    commands=[
       ['git fetch --no-tags origin research/active-source-discrimination-v7',0,'input pinned commit verified'],
       ['python -m venv .venv; .venv/Scripts/python -m pip install -r requirements-tested.txt',0,'install-native-v7.log'],
       ['python scripts/run_tests.py --out results/native_20261023/r0_tests',1,'r0_tests/TEST_RECEIPT.json'],
       ['python native/recover_assets.py',0,'recover.log'],
       ['native/build_native.cmd',0,'native_build.log'],
       ['python native/extract_existing_worlds.py',0,'extraction_first.log'],
       ['python scripts/run_tests.py --out results/native_20261023/r0_tests_windows_fixed; V7_OCB_ROOT=local_assets/ocb_x00',0,'r0_tests_windows_fixed/TEST_RECEIPT.json'],
       ['python native/fit_native.py',0,'train.log'],
       ['python native/evaluate_native.py',0,'dev_first.log'],
       ['native/build_native.cmd after adding inference API',0,'native_build_inference.log'],
       ['python native/verify_native.py',0,'native_qa_first.log']]
    write('EXECUTION_COMMANDS.json',{'cwd':str(ROOT),'commands':[dict(command=c,exit_code=e,evidence=l) for c,e,l in commands],
          'inherited_network_credentials_not_recorded':True})
    write('FINAL_DECISION.json',{'R0':'PASS_OPEN_ARCHIVE_INTEGRITY_AND_71_SOFTWARE_TESTS',
       'R1':'PASS_NATIVE_FIXED_PROBE_IDEAL_READOUT_COMPONENT; SENSOR_AND_UAV_LIMITS_RETAINED',
       'R2':'CONDITIONAL_COARSE_NATIVE_PILOT_NO_INDEPENDENT_M1_GAIN',
       'original_fast_M1_profile':'NOT_QUALIFIED_FOR_SAVED_TIME_RESOLUTION',
       'M1_current_implementation':'STOP_NO_INCREMENT_OVER_ORDINARY_CONTROLS',
       'synchronous_dynamic_observation_necessity':'NOT_ESTABLISHED_IN_THIS_TWO_SOURCE_PILOT',
       'R3_R4':'NOT_EXECUTED',
       'main_claim_pass':False,'new_physical_worlds':0,'new_ROS':0,'automatic_followup':False,
       'sealed_or_H03_observations_opened':False,'frozen_O24_modified':False,
       'science_limitations':['two known-source alternatives; TRAIN response calibration required',
          'one House and one original wind sequence','source XY and height jointly differ',
          'two TRAIN and two DEV worlds per source, not frame-independent replication',
          'ideal simulation readout, no hardware bandwidth or rotor-flow qualification',
          'M1 coverage selected zero additional filters; fast dynamics not validated']})
    print('PREPARED',sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()))

def package():
    DELIVERY.mkdir(parents=True,exist_ok=True)
    zip_path=DELIVERY/(NAME+'.zip')
    if zip_path.exists():raise RuntimeError('delivery already exists')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    # Include original frozen project sources/evidence/docs and new scoped
    # evidence. Never walk venv, raw cache, .git or unrelated workspace assets.
    files=[p for p in ROOT.rglob('*') if p.is_file() and not any(x in p.relative_to(ROOT).parts for x in
         ('.venv','local_assets','__pycache__','.pytest_cache')) and p.suffix not in ('.obj','.lib','.exp')]
    # Other temporary outputs are excluded explicitly.
    files=[p for p in files if p.name!='install-native-v7.log']
    entries={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(files)}
    receipt={'git_commit':commit,'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
          'input_commit':'1bfdc6f64c017b520d4a478e07d727d67c2d7675','payloads':len(entries),
          'original_raw_archives_or_reference_arrays_included':False,'new_physics':0,'new_ROS':0}
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:z.write(p,NAME+'/'+str(p.relative_to(ROOT)).replace('\\','/'))
        z.writestr(NAME+'/MANIFEST_SHA256.json',json.dumps(entries,indent=2))
        z.writestr(NAME+'/DELIVERY_RECEIPT.json',json.dumps(receipt,indent=2))
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        for name,h in entries.items():assert hashlib.sha256(z.read(NAME+'/'+name)).hexdigest()==h
    receipt.update({'zip_path':str(zip_path),'zip_bytes':zip_path.stat().st_size,'zip_sha256':sha(zip_path),
                    'payload_sha_verification':'PASS'})
    (DELIVERY/(NAME+'.receipt.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
    if sys.argv[1:] == ['package']: package()
    else:prepare()
