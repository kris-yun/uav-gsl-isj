from pathlib import Path
import json,hashlib,shutil,zipfile,ast
from datetime import datetime,timezone

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'outputs/PMFS_C1B_LOCAL_INITIAL_STATE_AUDIT_20261011'
def dump(n,o):(OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    clock=json.loads((OUT/'C1B_ALLOWED_HISTORY_AND_CLOCK.json').read_text())
    init_hi=clock['native_init_observed_physical_s_upper_bound']
    release_rate=7;support=447
    scenarios=[]
    for k in [2,4,8,24]:
        scenarios.append({'reference_count_K':k,'source_support':support,
            'birth_count_per_reference_at_init_no_exit_model':release_rate*init_hi,
            'birth_count_per_reference_after_300s_no_exit_model':release_rate*(init_hi+300),
            'assumed_filament_bytes_range':[32,64],'assumed_simultaneous_buffers':2,
            'initial_state_bytes_range':[math_bytes(release_rate*init_hi,support,k,b) for b in [32,64]],
            'end_state_bytes_range':[math_bytes(release_rate*(init_hi+300),support,k,b) for b in [32,64]],
            'caveat':'planning arithmetic only. Actual exits, Filament sizeof, caching and copy/storage overhead require profiling; not measured RSS or a bound on implementation.'})
    options={
        'status':'DESIGN_OPTIONS_ONLY_NO_PRIOR_OR_REFERENCE_EXECUTED',
        'recommended_next':'L1: register one source-blind generative missing-history law before any reference/score; a 3-anchor x2-reference profile is proposed, not authorized here',
        'locked_constraints':['R5_STOP','same447 source support','no truth/complete CFD/future wind in LOCAL','same source/plant seeds and old results','300s official budget and variance gate unchanged','same main Euclidean-risk endpoint','no new plant realization','remaining compute wallet not reset'],
        'data_fact':{'unobserved_release_prefix_s':267.407159464,'eligible_wind_rows':184,'wind_spatial_positions':1,'vertical_wind_measured':False,'pre_initialize_wind_PMFS_consumed':0},
        'input_distribution_propagation_output':{
            'inputs':['public world geometry/outlets and instrument model','447-cell common support and declared release/height support','public release start/time step/rate and actual frame clock','only received local wind and same permitted history for all arms'],
            'distribution':'one registered π(U_past_and_spatial, X_init, q, height | permitted history, s), same hyperparameters/nuisance law across candidate sources; no test-source calibration',
            'propagation':'begin X=0 at public release t=0, retain old3D state; marginalize unobserved past rather than zeroing at search; use instance-isolated RNG',
            'outputs':['proper sequential response likelihood or preregistered justified proper-composite','normalized447-source mass','conditional receptor hit probability and its between-source variance','MC uncertainty/ESS/state checkpoint'],
            'unresolved_model_parameters':['past wind temporal scale/amplitude','spatial and vertical wind law constrained by geometry/boundaries','relation of local measured wind to entire field','initial height/release nuisance prior','response probability/noise law and finite-reference adequacy'],
            'public_sensor_noise_is_not_wind_process_prior':True,
        },
        'options':[
            {'id':'L0','name':'use complete recorded release-to-search local history','contract_coverage':'principle covered, factual inputs absent','decision':'STOP_THIS_INPUT_PATH','reason':'earliest qualified same-epoch wind267.407s; no observation of release0..267s; do not search old plume/CFD as replacement'},
            {'id':'L1','name':'source-blind generative marginal initialization','contract_coverage':'LOCAL/ordinary filtering principles covered; actual3D latent law not registered','decision':'RECOMMENDED_NEW_MODEL_CONTRACT','needs':['single declared missing-history/spatial/vertical wind prior and its independent basis','same hierarchy across all447 candidates, RNG/checkpoint hook','properppm response predictive law','full-support physical validity and finite-MC acceptance'],
             'calibration_now':'only184 stationary horizontal readings can calibrate recent instrument observation; they cannot qualify unseen past/vertical field','forbidden':['choose prior by B4 location error','fill past with fullCFD10','make past deterministic currentwind','use true plume checkpoint as candidate initial state'],
             'estimated_new_code_lines_range':[800,1600],'estimate_not_measured':True},
            {'id':'L2','name':'stationary conditional initial ensemble from current local wind','contract_coverage':'not originalN0 and not registered; additional stationarity/mixing assumption','decision':'OPTION_REQUIRING_PHYSICAL_FALSIFICATION','reason':'current point wind cannot establish early transient or full3D flow; requires independent mixing-time/readout discrepancy evidence, not B4 staticCFD name','risk':'may erase precisely the missing-history uncertainty under investigation'},
            {'id':'L3','name':'bounded-age finite state initial response approximation','contract_coverage':'not registered; R5 complex memory remains stopped','decision':'OPTION_ONLY_AFTER_ORDINARY_INITIAL_LAW_EXISTS','reason':'must first bound response error relative to L1 with permitted histories and proper predictive calibration; response fidelity alone is not source decision gain'},
            {'id':'L4','name':'play the same frozen gas from release frame0','contract_coverage':'changes frozen official playback500 and acquisition history','decision':'USER_SCIENTIFIC_CONTRACT_CHANGE_REQUIRED','reason':'knownzero at release0 may avoid unknown initialization but does not preserve official run; no automatic goal or physical regeneration'},
            {'id':'L5','name':'append local prerelease/warm-up sampling','contract_coverage':'changes acquisition route/history or elapsed information budget','decision':'USER_SCIENTIFIC_CONTRACT_CHANGE_REQUIRED','reason':'later sampling cannot retroactively observe first267s; new controlled task would require a separate fair budget/initialization design'},
        ],
        'proposed_profile_NOT_EXECUTED':{
            'purpose':'cost/RNG/state/physics checks only, no source-truth evaluation or method selection',
            'atomic_sources':3,'selection_rule':'public447 support indices at fixed quartiles in native order before labels; physical height legality first; do not choose true/wrong peak',
            'references_per_source':2,'new_forward_calls_max':6,
            'physical_prefix_s':'full public release0 to conservative actual search interval316.616..322.117; no267s truncation',
            'active_wall_hard_limit_s':300,'single_thread':True,'RSS_limit_bytes':1073741824,
            'shared_storage_only':True,'root_deletion_or_expansion':False,
            'reference_rng':'new role-isolated keyed references require registration; frozen plant/source/nav seeds stay unchanged. Existing plant RNG never supplied as inference evidence',
            'two_refs_not_sufficient_for_scientific_MC_gate':True,
            'full447_scale_rule':'profile supplies cost estimates only;3anchors do not qualify all-support probabilities. Full447/K must fit remaining budget and independentMC criterion before execution',
        },
        'engineering_implementable_now':['scoped clock/role/unit parser','source-independent initial-law-required gate','schema and future/invalid-input rejection','standalone raw prefix decoding and metadata audit'],
        'done_now':['prefix decoder215winds/186physical/184TF qualified','13SHA independent check','7fail-closed checks','release/playback/init time distinction','archivedinstrument noise law audit'],
        'remaining_after_choice':['instance RNG/state operator change','3D missing-history model and common information adapter','proper response filter','actual native two-port consumer hook','bounded cost and full-support qualification'],
        'code_and_time_estimate':'800–1600 newC++/filter/hook lines is planning range. Actual full implementation/build/physical profile time not measured; no promise of closing within remaining~3.12h',
        'memory_planning_scenarios':scenarios,
        'memory_storage_notes':['shares frozen geometry, never duplicatefullCFD','whole-bank inRAM may exceed1GiB; chunked source/reference checkpoints can trade shared-diskIO forRAM','disk8GiB and reserve4GiB still hard;8GiB sufficiency is not measured','discarding oldfilaments needs physics/response error justification, not memoryconvenience'],
        'new_physics_calls':0,'new_goals':0,'new_scientific_prior_chosen':False,
    }
    dump('C1B_LOCAL_INIT_OPTIONS.json',options)
    archived=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/source/anemometer/fake_anemometer.cpp'
    yamlpath=BASE/'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010/runtime/preflight_PioneerP3DX_Anemometer_parameters.yaml'
    import yaml
    params=yaml.safe_load(yamlpath.read_text());modes={}
    def walk(o):
        if isinstance(o,dict):
            for k,v in o.items():
                if isinstance(v,dict):walk(v)
                elif k in ['use_map_ref_system','noise_std','frequency','use_sim_time','sensor_frame','fixed_frame']:modes[k]=v
    walk(params)
    dump('C1B_INSTRUMENT_SCOPE_SUPPLEMENT.json',{'phase':'read-only supplementary source/parameter audit, before any initial model execution','archived_source_path':str(archived),'archived_source_sha256':hashlib.sha256(archived.read_bytes()).hexdigest(),'parameter_sha256':hashlib.sha256(yamlpath.read_bytes()).hexdigest(),'public_parameters':modes,'new_physics':0,'no_change_to_initial_input_freeze':True})
    for name in ['c1b_local_scope_audit.py','c1b_decode_allowed_prefix.py','c1b_validate_local_prefix.py','c1b_finalize_options.py']:
        p=BASE/'work'/name;ast.parse(p.read_text());shutil.copy2(p,OUT/name)
    dump('C1B_BUDGET_LEDGER.json',{'UTC':datetime.now(timezone.utc).isoformat(),'previous_conservative_balance_s':11526.578,'C1B_readonly_reservation_debit_s':300,'remaining_conservative_s':11226.578,'measured_decoder_active_s':0.18713888101046905,'host_decoder_command_active_s':1.656,'future_profile300s_is_a_separate_proposal_not_executed':True,'no_calendar_reset':True,'no_network_time_used_to_extend_process_deadlines':True,'ROS_nodes_started':0,'physics_calls':0,'new_plant_batches':0,'native_goals':0,'R5':'STOP_PRESERVED'})
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file() and p.name!='C1B_SHA256.json'}
    dump('C1B_SHA256.json',manifest)
    z=OUT.with_suffix('.zip')
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as w:
        for p in sorted(OUT.iterdir()):
            if p.is_file():w.write(p,p.name)
    with zipfile.ZipFile(z) as r:
        assert r.testzip() is None
        for n,h in manifest.items():assert hashlib.sha256(r.read(n)).hexdigest()==h
    h=hashlib.sha256(z.read_bytes()).hexdigest();z.with_suffix('.zip.sha256').write_text(h+'  '+z.name+'\n',encoding='ascii')
    print(json.dumps({'manifest_checked':len(manifest),'zip_bytes':z.stat().st_size,'zip_sha256':h,'physics':0,'goals':0}))

def math_bytes(births,support,k,per_filament):return int(births*support*k*per_filament*2)
if __name__=='__main__':main()
