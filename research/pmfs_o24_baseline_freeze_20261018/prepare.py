from pathlib import Path
import ast,csv,datetime,difflib,hashlib,json,re,shutil,struct,subprocess,time,zipfile
P=Path(__file__).resolve().parent
W=Path(r'D:\ZYC\UAV\.codex\worktrees\pmfs-paper-eq6-20261017\A-gas')
R=W/'research/pmfs_o24_baseline_freeze_20261018'
OLD=Path(r'D:\ZYC\A-gas\workspace\PMFS_PAPER_FIRST_ROS_QUAL_20261017')
AUD=OLD.parent/'PMFS_EARLY_DECLARATION_AUDIT_20261018'
DOC=Path(r'C:\Users\50176\Downloads\PMFS_%E5%AE%98%E6%96%B9%E5%9F%BA%E7%BA%BF%E5%86%BB%E7%BB%93%E8%A3%81%E5%86%B3%E4%B8%8E%E6%89%A7%E8%A1%8C%E5%90%88%E5%90%8C_20261018.md')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def body(s,sig):
 a=s.index(sig);b=s.index('{',a);depth=0
 for j in range(b,len(s)):
  depth+=(s[j]=='{')-(s[j]=='}')
  if depth==0:return s[a:j+1]
 raise ValueError(sig)
assert not (P/'PREPARED_LOCATION.json').exists();R.mkdir(parents=True,exist_ok=True)
shutil.copyfile(DOC,R/'用户采用的执行合同_zh.md')
lock=json.loads((OLD/'SOURCE_LOCK.json').read_text(encoding='utf-8'));assert lock['commit']=='a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533'
verified=[]
for row in lock['files']:
 p=OLD/'official_exact'/row['path'];b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_oid']
 verified.append(row);dst=R/'upstream_readonly'/row['path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
put(R/'UPSTREAM_SOURCE_LOCK.json',dict(commit=lock['commit'],tree=lock['tree'],status='PASS_SHA256_AND_GIT_BLOB_ALL_SELECTED_FILES',selected_files=len(verified),scope='All committed gsl_server/gsl_actions files and selected PMFS configuration assets; not a full entire-repository checkout and not proof of author experimental commit',files=verified))
# Build only a source candidate in this isolated worktree. No ROS compilation.
shutil.copytree(OLD/'source_runtime',R/'o24_port_gmrf_source',dirs_exist_ok=True)
src=R/'o24_port_gmrf_source';rel='src/gsl_server/algorithms/PMFS/PMFSLib.cpp';p=src/rel;s=p.read_text(encoding='utf-8');a='double exponent = -(cell.omega * cell.omega) / std::pow(settings.confidenceMeasurementWeight, 2);';b='double exponent = -cell.omega / std::pow(settings.confidenceMeasurementWeight, 2);';assert s.count(a)==1;p.write_text(s.replace(a,b),encoding='utf-8',newline='\n')
# Keep the audit's exact-response export available but off unless explicitly
# enabled; this is an instrumentation adaptation, not a guarantee of identical
# OpenMP scheduling or time-seeded RNG ownership.
sim='src/gsl_server/algorithms/PMFS/internal/Simulations.cpp';shutil.copyfile(AUD/'source_runtime'/sim,src/sim)
official=(R/'upstream_readonly/gsl_server'/sim).read_text(encoding='utf-8');actual=(src/sim).read_text(encoding='utf-8')
for sig in ['double Simulations::sourceProbFromMaps(','void Simulations::moveFilament(','void Simulations::simulateSourceInPosition(','bool Simulations::moveAlongPath(']:
 assert body(official,sig)==body(actual,sig),('native science function changed',sig)
mathrel='src/gsl_server/algorithms/Common/Utils/Math.cpp';assert (src/mathrel).read_bytes()==(R/'upstream_readonly/gsl_server'/mathrel).read_bytes()
changes=[];patches=R/'patches';patches.mkdir()
category={'CMakeLists.txt':'BUILD_DEPENDENCY_AND_INFORMATION_PERMISSION','src/gsl_server/algorithms/Common/StopAndMeasureState.cpp':'INPUT_TRAJECTORY_ADAPTER_EMPTY_OBSERVATION_GUARD_AND_PASSIVE_TRACE','src/gsl_server/algorithms/PMFS/PMFS.cpp':'STARTUP_MAP_READINESS_ADAPTER','src/gsl_server/algorithms/PMFS/PMFS_utils.cpp':'DISCLOSED_RECTANGULAR_MOMENT_DOMAIN_REPAIR',sim:'PASSIVE_EXPORT_ADAPTER_WITH_SCHEDULING_CAVEAT'}
for p in sorted((R/'upstream_readonly/gsl_server').rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(R/'upstream_readonly/gsl_server');q=src/rel
 if not q.exists():continue
 if p.read_bytes()!=q.read_bytes():
  key=rel.as_posix();assert key in category,key
  diff=''.join(difflib.unified_diff(p.read_text(encoding='utf-8').splitlines(True),q.read_text(encoding='utf-8').splitlines(True),fromfile='PMFS-U24-SOURCE/'+key,tofile='PMFS-O24-PORT-GMRF/'+key))
  dst=patches/(key.replace('/','__')+'.patch');dst.write_text(diff,encoding='utf-8')
  changes.append(dict(path=key,classification=category[key],upstream_sha256=sha(p),prepared_sha256=sha(q),patch_sha256=sha(dst),not_claimed_semantics_preserving_for_all_inputs=key!='CMakeLists.txt'))
assert len(changes)==5 and not any(x['path'].endswith('PMFSLib.cpp')for x in changes)
put(R/'PATCH_CLASSIFICATION.json',dict(status='FIVE_PREPARED_DIFFERENCES_DISCLOSED_NO_PAPER_FORMULA_PATCH',patches=changes,confidence_and_scoring_match_official=True,Math_cpp_byte_identical=True,recording_call_order='No extra direct random calls; OpenMP/time-seeding and I/O scheduling can change which candidate consumes which random state. Not claimed identical RNG trajectory.'))
base=json.loads((OLD/'RUN_PRECOMMIT.json').read_text(encoding='utf-8'))['parameters'];o=base.copy();o.update(sourceDiscriminationPower=.2,convergence_thr=1.5,useWindGroundTruth=False,use_sim_time=False)
identities=[dict(id='PMFS-U24-SOURCE',status='SOURCE_IDENTITY_FROZEN',source=lock['commit'],formula='linear_Omega',D=.2,threshold_m2=1.5,wind='Upstream launch True; effective branch also depends on USE_GADEN',executable='NOT_BUILT_IN_THIS_HOST_PREFLIGHT',performance=None),dict(id='PMFS-O24-PORT-GMRF',status='PREPARED_SOURCE_PARAMETERS_FROZEN_ROS_BUILD_AND_RESULTS_PENDING',source=lock['commit'],formula='linear_Omega',D=.2,threshold_m2=1.5,wind='GMRF/local available observations',USE_GADEN=False,parameters=o,executable='NOT_BUILT_NOT_A_P24_ELF',performance=None),dict(id='PMFS-O24-ORACLE-WIND',status='IDENTITY_SPEC_ONLY_NO_BINARY_NO_RESULTS',source=lock['commit'],formula='linear_Omega',D=.2,threshold_m2=1.5,wind='Actual bound true-wind service required',USE_GADEN=True,executable=None,performance=None),dict(id='PMFS-P24-PAPER-FIRST',status='FROZEN_EXISTING_FOUR_REAL_RUNS_NOT_OUR_O24_RESULTS',source=lock['commit'],formula='squared_Omega',D=1.,threshold_m2=1.,wind='GMRF',USE_GADEN=False,existing_binary_sha256=json.loads((AUD/'BUILD_RESULT.json').read_text(encoding='utf-8'))['binary_sha256'],results_sha256=sha(AUD/'analysis/EPISODES.csv')),dict(id='PMFS-A-PRIME',status='NOT_IMPLEMENTED_NO_RESULTS',parent='PMFS-O24-PORT-GMRF',formula=None,D=None,threshold_m2=None,wind='Must share evaluation information protocol',executable=None,performance=None)]
put(R/'BASELINE_IDENTITIES.json',dict(identities=identities,prohibit_ambiguous_PMFS_original_label=True))
put(R/'O24_PARAMETER_MANIFEST.json',dict(status='FROZEN_INTENDED_VALUES_NOT_RUNTIME_RESOLVED_PARAMETERS',values=o,confidence_formula='alpha=1-exp(-Omega/sigmaOmega^2)',score_formula='product_over_free_cells(1-D*alpha*abs(measured-predicted))',readout='Native Top5 weighted position',age_event='Pinned code centre-cell simultaneous any-hit; no age-radius law invented',compiler_flags=dict(USE_GADEN=False,USE_GUI=False,USE_TRACY=False,Release=True,OMP_THREADS=4),runtime_parameter_service_gate_required=True))
profiles=R/'prepared_profiles';profiles.mkdir()
for case,role in [('A2','EA18_A2_R01'),('B2','EA18_B2_R01')]:
 before=(AUD/'cases'/role/'N1_launch.py').read_text(encoding='utf-8');s=before
 s=s.replace('{"sourceDiscriminationPower": 1.0}','{"sourceDiscriminationPower": 0.2}').replace('{"convergence_thr": 1.0}','{"convergence_thr": 1.5}')
 s=s.replace('/home/zyc/ros2_ws/pmfs_early_declaration_20261018/gsl_actionserver_node','/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018/NOT_BUILT/gsl_actionserver_node')
 s=s.replace('/mnt/hgfs/workspace/PMFS_EARLY_DECLARATION_AUDIT_20261018/cases/'+role+'/runtime/','/mnt/hgfs/workspace/PMFS_O24_PHASE1_PENDING_APPROVAL/'+case+'/')
 # This is a template only; no runner, no shell script, no scheduled execution.
 s='# NOT EXECUTABLE QUALIFICATION: requires user-approved ROS build and newly frozen case IDs.\n'+s
 ast.parse(s);(profiles/(case+'_O24_launch_TEMPLATE.py')).write_text(s,encoding='utf-8',newline='\n')
 (profiles/(case+'_P24_to_O24.patch')).write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='P24_actual/'+case,tofile='O24_PREPARED_ONLY/'+case)),encoding='utf-8')
# Preserve P24 results and the authoritative original-C++ readout; never relabel
# them as O24 observations or O24 online performance.
reference=R/'p24_fixed_history_reference';reference.mkdir()
for name in ['EPISODES.csv','SOURCE_UPDATES.csv','FORMULA_CONTROLS_NATIVE_CPP_READOUT.csv','EXACT_NATIVE_REPLAY_PARITY.csv','OFFICIAL_SOURCE_MAP_AUDIT.json','CLOCK_ALIGNMENT_AUDIT.json','FINAL_NATIVE_READOUT_PARITY.json','INHERITED_METADATA_ERRATA.json']:
 shutil.copyfile(AUD/'analysis'/name,reference/name)
shutil.copytree(OLD/'world_provenance',R/'world_provenance')
shutil.copytree(OLD/'dependency_provenance',R/'dependency_provenance')
shutil.copytree(OLD/'dependencies',R/'dependencies')
put(R/'INPUT_ARCHIVE_IDENTITY.json',dict(path=r'C:\Users\50176\Downloads\PMFS_提前错误声明_时钟与B2核清_四回合原始证据_20261018_最终验收版.zip',sha256='84087b1ddd39b1edcc5be33c88263585e7f1a8dd66694f8569a019250bee2100',contract_sha256=sha(DOC),P24_immutable=True))
shutil.copyfile(P/'prepare.py',R/'prepare.py')
put(P/'PREPARED_LOCATION.json',dict(path=str(R),branch='codex/pmfs-o24-baseline-freeze-20261018',new_VM_calls=0,new_ROS=0,new_worlds=0,AIMMD=0))
print(json.dumps(dict(status='O24_SOURCE_AND_IDENTITIES_PREPARED_NO_ROS_BUILD_OR_RUN',path=str(R),official_files=len(verified),patches=len(changes))))
