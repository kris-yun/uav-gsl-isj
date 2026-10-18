from pathlib import Path
import ast,csv,datetime,hashlib,json,math,re,shutil,subprocess,zipfile
P=Path(__file__).resolve().parent;R=Path(json.loads((P/'PREPARED_LOCATION.json').read_text(encoding='utf-8'))['path']);A=R/'validation';OLD=Path(r'D:\ZYC\A-gas\workspace\PMFS_PAPER_FIRST_ROS_QUAL_20261017');AUD=OLD.parent/'PMFS_EARLY_DECLARATION_AUDIT_20261018'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(p):return list(csv.DictReader(p.open(encoding='utf-8')))
# Inventory every keyed parameter expression in the locked launch (including
# inactive optional algorithms) and every core default at its source line.
launch=R/'upstream_readonly/Environment_config/PMFS/launch/main_simbot_launch.py';text=launch.read_text(encoding='utf-8');tree=ast.parse(text);inventory=[]
for node in ast.walk(tree):
 if isinstance(node,ast.Dict):
  for k,v in zip(node.keys,node.values):
   if isinstance(k,ast.Constant)and isinstance(k.value,str):inventory.append(dict(line=k.lineno,key=k.value,expression=ast.get_source_segment(text,v)))
defaults=[]
for rel in ['src/gsl_server/algorithms/PMFS/PMFS.cpp','src/gsl_server/algorithms/PMFS/PMFSLib.cpp','src/gsl_server/algorithms/Common/Algorithm.cpp','src/gsl_server/algorithms/Common/StopAndMeasureState.cpp']:
 t=(R/'upstream_readonly/gsl_server'/rel).read_text(encoding='utf-8')
 for i,line in enumerate(t.splitlines(),1):
  if 'getParam<'in line:defaults.append(dict(path=rel,line=i,text=line.strip()))
put(R/'OFFICIAL_PARAMETER_SOURCE_INVENTORY.json',dict(launch_entries=inventory,core_getParam_lines=defaults,not_a_runtime_parameter_snapshot=True))
param=json.loads((R/'O24_PARAMETER_MANIFEST.json').read_text(encoding='utf-8'));param['values'].update(th_gas_present=.1,th_wind_present=.02,robot_location_topic='ground_truth',enose_topic='PID/Sensor_reading',anemometer_topic='/native20/wind_to',anemometer_frame='PioneerP3DX_anemometer_frame',openMoveSetExpasion=5,explorationProbability=.05,initialExplorationMoves=2,localEstimationWindowSize=2,convergence_steps=5,markers_height=.2,distanceThreshold=.5,headless=True)
param['convergence_steps_is_unused_by_native_stop']=True
param['input_permission_and_visual_differences_from_official_launch']=['useWindGroundTruth True->False; paired with USE_GADEN OFF, intentional deployment information restriction','anemometer_topic routes saved upwind-to-downwind adapter; GMRF consumes original local upwind message','headless False->True and GUI build OFF; avoids graphical startup but not assumed identical runtime timing']
param['per_case']={case:dict(source_xyz=json.loads((OLD/'cases'/rid/'CASE_META.json').read_text(encoding='utf-8'))['source_xyz'],start_xyz=json.loads((OLD/'cases'/rid/'CASE_META.json').read_text(encoding='utf-8'))['robot_start_xyz'])for case,rid in [('A2','PF24_A2_T02'),('B2','PF24_B2_Q01')]}
put(R/'O24_PARAMETER_MANIFEST.json',param)
extra=[]
for case,rid in [('A2','PF24_A2_T02'),('B2','PF24_B2_Q01')]:
 m=json.loads((OLD/'cases'/rid/'CASE_META.json').read_text(encoding='utf-8'));root=Path(m['shared_case_path'].replace('/mnt/hgfs/workspace/',r'D:\ZYC\A-gas\workspace'+'\\'));occ=Path(m['player']['occupancyFile'].replace('/mnt/hgfs/workspace/',r'D:\ZYC\A-gas\workspace'+'\\'))
 for p in [*sorted((root/'one_realization/wind').glob('*')),occ]:
  if p.is_file():extra.append(dict(case=case,path=str(p),size_bytes=p.stat().st_size,sha256=sha(p)))
put(R/'WORLD_WIND_AND_3D_OCCUPANCY_MANIFEST.json',dict(status='HOST_READONLY_HASHED_EXISTING_INPUTS',files=extra,new_worlds=0))
deps=json.loads((OLD/'LIVE_BINARY_AND_DEPENDENCY_IDENTITY.json').read_text(encoding='utf-8'));put(R/'DEPENDENCY_EXPECTATIONS_NOT_LIVE_RECHECK.json',dict(source='Prior executed dependency identities, not live VM verification during this host-only phase',dependencies=deps['dependencies'],P24_binary_not_O24=deps['baseline'],O24_ROS_ELF=None,live_VM_recheck_required_before_run=True))
rngsrc=R/'o24_port_gmrf_source/src/gsl_server/algorithms/Common/Utils/Math.cpp';simsrc=R/'o24_port_gmrf_source/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp';rg=rngsrc.read_text(encoding='utf-8');sg=simsrc.read_text(encoding='utf-8')
assert 'std::chrono::high_resolution_clock::now().time_since_epoch().count()'in rg and 'schedule(dynamic)'in sg
put(R/'RNG_AND_PASSIVE_IO_AUDIT.json',dict(status='NATIVE_RNG_SOURCE_UNCHANGED_EXACT_STREAM_FREEZE_HOLD',Math_cpp_sha256=sha(rngsrc),native_facts=['thread_local minstd_rand0 is default constructed, no exposed runtime seeding API','uniformRandom uses thread-local high_resolution_clock seed and xxHash32 state','PrecalculatedGaussian uses a uniform-random initial table phase and2500 normal values','OpenMP dynamic scheduling assigns candidates to thread-local streams'],passive_capture='No extra direct uniformRandom/randomFromGaussian/nextValue calls. Critical file I/O, timing and thread scheduling are not guaranteed inert. This is an explicitly disclosed instrumentation adaptation.',externally_freezable_seed_parameter=None,preselected_seed_values=None,pending='Before strict seeded phase1, audit/approve a separate native-state capture/replay protocol; do not invent four seed numbers or silently force new RNG behavior. No such RNG adapter was added here.'))
pair=[]
for case,role in [('A2','EA18_A2_R01'),('B2','EA18_B2_R01')]:
 rows=read(AUD/'cases'/role/'runtime/native_posterior_updates.csv');u=max(int(x['update'])for x in rows);rows=[x for x in rows if int(x['update'])==u];truth=param['per_case'][case]['source_xyz'];nearest=min(rows,key=lambda x:(math.hypot(float(x['x_m'])-truth[0],float(x['y_m'])-truth[1]),int(x['row']),int(x['col'])));competitor=max(rows,key=lambda x:(float(x['source_probability']),-int(x['row']),-int(x['col'])))
 if case=='A2':near=next(x for x in rows if int(x['col'])==7 and int(x['row'])==34)
 else:near=nearest
 pair.append(dict(case=case,diagnostic_only_never_online_input=True,true_source_xy=truth[:2],near_source_cell=dict(col=int(near['col']),row=int(near['row']),x=float(near['x_m']),y=float(near['y_m'])),competitor_cell=dict(col=int(competitor['col']),row=int(competitor['row']),x=float(competitor['x_m']),y=float(competitor['y_m'])),selection='Competitor fixed from first existing P24 development episode before any O24 outcome; B2 uses nearest legal coarse cell, not nonexistent true cell',margin_definition='log posterior probability at fixed near-source cell minus log probability at fixed competitor, at each full source update. No epsilon floor; zero reported as -inf/undefined when bothzero.'))
put(R/'PHASE1_DIAGNOSTIC_SOURCE_PAIRS.json',dict(status='FIXED_DIAGNOSTIC_PAIRS_NOT_A_GUIDANCE_POLICY',pairs=pair))
roles=[dict(id=f'O24G_{case}_R{i:02d}',case=case,repeat=i,information='GMRF/local sensor only',start=param['per_case'][case]['start_xyz'],native_cutoff_wall_s=300,seed=None,seed_status='NOT_FREEZABLE_BY_UPSTREAM_API_HOLD')for case in ['A2','B2']for i in [1,2]]
plan=dict(status='DRAFT_FROZEN_SCOPE_NOT_AUTHORIZATION_NOT_READY_TO_LAUNCH',roles=roles,real_ROS_episodes=4,new_worlds=0,AIMMD=0,science_parameter_changes_from_declared_O24=0,variance_threshold_m2=1.5,native_clock='wall',D=.2,confidence='linear_Omega',source_domain='Original all-pixels-free coarse support; B2 exclusion retained',stop_on_scientific_failure='Keep it; no extra rerun to select a favorable result',technical_retry_cap=0,phase0_limits='No VM, ROS, CFD, cloud tasks, other chats; host C++ only',next_phase_requires_direct_user_approval=True,proposed_total_host_budget_s=2400,guest_free_floor_bytes=5*2**30,host_free_floor_bytes=2*2**30,build_storage='Prefer sharedD build to avoid reducingVM free reserve; do not delete/move existing data',required_before_any_goal=['New full O24 ROS build with prepared source and macros; record uniqueELF SHA','Runtime dependencies SHA must be verified live, not assumed from cached expectations','All resolved ROS parameters and local-wind branch observed, map/player/sensor preflight','RNG seed/state protocol audited and frozen; current upstream no external seed knob','Ensure planned per-message/query/frame/window mapping is actually captured, otherwise restrict attribution'],required_outputs=['native declaration bool and stop reason','wall/robot/physical-frame time mapping','nativeTop5/full-mean/MAPerror and whole-posterior variance','truth1m/2mneighborhood probability mass asdiagnostics, not altered success criterion','fixedsource-pair logratio and allcandidateowner/RNG provenance','allraw observations, consumerwindows, navigation and actualparameters','full candidatecalls and CPU/cost includinginstrumentation'],no_stop_shadow_runs_authorized=False)
put(R/'PHASE1_QUALIFICATION_PLAN.json',plan)
checks=[('UPSTREAM_SELECTED_FILE_IDENTITY','PASS'),('O24_LINEAR_OMEGA_AND_NATIVE_SCORING_SOURCE','PASS'),('O24_INTENDED_SCIENCE_PARAMETER_MANIFEST','PASS'),('WIND_INFORMATION_IDENTITIES_SEPARATED','PASS_SPEC_ONLY'),('HOST_CPP_FIXED_HISTORY_SCORING_AND_MOMENTS','PASS'),('RECTANGULAR_REPAIR_DISCLOSED','PASS_WITH_PATCH'),('ALL_EXISTING_GAS_FRAME_BYTES','PASS_HASH_IDENTITY_ONLY'),('PASSIVE_DIRECT_RNG_CALLS_NOT_ADDED','PASS_STATIC'),('PASSIVE_IO_IDENTICAL_RNG_THREAD_TRAJECTORY','HOLD_NOT_PROVABLE'),('PRESELECTED_NATIVE_SEED_OR_STATE_PROTOCOL','HOLD_NOT_EXPOSED'),('FULL_O24_ROS_BINARY_AND_RESOLVED_RUNTIME','NOT_BUILT_NOT_RUN'),('O24_REAL_CLOSED_LOOP_RESULT','NOT_AVAILABLE'),('PAPER_30_RUN_PERFORMANCE_REPRODUCTION','HOLD')]
put(R/'FINAL_GATE_TABLE.json',dict(gates=[dict(gate=k,status=v)for k,v in checks],verdicts=['BASELINE_SOURCE_IDENTITY_FROZEN','O24_PORT_GMRF_ROS_RESULT_NOT_YET_AVAILABLE','PAPER_PERFORMANCE_REPRODUCTION_HOLD','MAIN_INNOVATION_EVALUATION_NOT_YET_LICENSED_BY_DATA_QUALIFICATION'],new_ROS=0,new_VM_calls=0,new_worlds=0,AIMMD=0,new_chat_messages=0))
report='''# PMFS-O24身份冻结与阶段0预检

本轮仅执行用户采用合同第5节的只读预检：读取已有ZIP/源码/物理帧，在独立工作树生成源码副本、差异、manifest与Windows本机C++验证。没有连接或启动VM，没有ROS/CFD/AIMMD，没有生成气体世界，没有打开或联系其他会话，也没有创建后台/云任务。

## 冻结裁决

主公平基线以后命名为 **PMFS-O24-PORT-GMRF**：2024-09-18作者提交`a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533`的核心，D=0.2、线性Ω、方差门1.5m²，GMRF/可获得的局地风输入。原样上游、Oracle真风、P24论文重建和A-prime分别保留身份。A-prime尚未实现，Oracle尚未运行，O24目前没有真实闭环成绩。

之前四次运行全部属于 **PMFS-P24-PAPER-FIRST**（D=1、Ω²、1m²）。它们仍是负证据，没有迁移为O24性能。正式论文30次结果的复现继续HOLD。185份所选官方文件逐一通过SHA与Git blob校验；这证明源码身份，不证明已取得作者论文实际实验提交或所有仓库资产。

## 风输入的纠正

固定官方启动文件确为`useWindGroundTruth=True`。前一轮实际是False，且编译`USE_GADEN=OFF`，使用GMRF。不能再把二者称为全部启动条件一致。关闭GADEN宏时，原生estimateWind没有真风分支；打开宏后也必须实际连接并消费真风服务才算Oracle，不能仅凭布尔值命名。主公平O24主动采用非真值风信息协议，这是一项明确的部署信息限制。

## 准备的源码及补丁

O24源副本已将PMFSLib的Ω平方改回官方线性形式；该文件现在与上游完全相同。评分、气团运动、预热/记录、随机函数和源支持没有新科学改动。相对上游有五个已列明文件差异：构建/依赖与GADEN信息权限；空观测保护与消费导出；地图就绪保护；矩形地图的全域均值/方差遍历修复；被动源更新/候选响应导出。

这些差异不能笼统称为无影响。空观测/TF/播放器会影响有效输入或轨迹，矩形修复会改变错误的原方差读数，被动I/O可能改变耗时与OpenMP线程随机流归属。全部作为可审计适配保留，不包装成创新。源码文件未静默修正气团公式、地图、单位、阈值或年龄覆盖规律。

## 本机C++与输入检验

在Windows MSVC运行从固定官方源码直接提取的评分、logOdds、归一化和读出函数，用原P24保存的1,120张实际候选图做7组离线复算。P24评分对保存值最大相对差约7.2e-16，重建概率图最大绝对差约1.4e-17。矩形3×5示例确认原遍历方差0.8、正确全域方差8/3；未因此改变阈值。

同一P24历史下也按O24公式重算了概率图。这是源函数验证，不是O24ROS运行。MSVC与Linux libstdc++对并列概率std::sort的Top5%边界选择可略有不同，不能把Windows读出冒充Linux线上成绩。权威已有Linux重算表另原样保存，差别明确保留。

原输入ZIP的340个payload全部通过哈希；A2/B2共3606个已有气体帧也重新逐文件通过SHA，另存风文件和三维占据输入SHA。该检验确认文件身份，没有把重新生成的世界升格为作者原始实验数据，也不证明湖岸物理资格。

## 仍不能标PASS的项

1. **O24完整ROS二进制尚未编译，也没有任何O24实际回合。** Windows小型验证EXE有独立SHA，绝不充当ROS ELF；P24 ELF未改名。依赖二进制当前只是已有审计中的期望SHA，尚未通过本轮VM现场核验。
2. **预先固定种子尚未成立。** 上游Gaussian引擎为线程局部默认初始化，uniformRandom以高精度时间初始化xxHash种子，缓存Gaussian相位也依赖该流。它没有外部seed参数；OpenMP动态调度和I/O可以改变候选对应的随机流。没有新增随机调用不等于完整轨迹保持不变。本轮不自造四个种子、不擅自增加重置/新随机协议，Math.cpp逐字节未变。阶段1若要求严格预先锁seed/state，需先审计并冻结原生状态记录/重放接线。
3. **实际运行参数与完整时间映射必须到下一阶段现场验证。** 目前给出的是所有关键预期值与官方参数表达式/默认值清单。模板使用明确的NOT_BUILT路径，未提供可自动启动的ROSrunner。四个拟议回合、源对诊断、停机规则及预算另列，均非运行授权。

B2地图仍保持：二维源粗格被排除、三维释放合法、最近合法中心约0.2483m。不开格、不移动源。混合时钟与A2循环边界沿用已核定语义，不把搜索墙钟乘除5。

## 下一阶段范围与门

拟议仅A2/B2各两回合，D=.2、线性Ω、阈值1.5、原起点/地图/世界/混合时钟/GMRF，最多40分钟宿主预算草案，气体世界新增0，AIMMD0，无no-stop影子运行，无科学失败重跑。先完成真实O24构建、实际参数/依赖/输入预检、RNG协议门，再允许发出任何目标；如不满足，停在构建/资格状态。

**用户采用合同第5节明确要求“只有在用户单独批准真实运行时才进入A2/B2的小规模闭环资格测试”。本轮到阶段0为止。** 不把本机验证、源码血统或固定历史复算当成官方性能复现。

交付中的`FINAL_GATE_TABLE.json`为准；`BASELINE_IDENTITIES.json`固定五类身份；`O24_PARAMETER_MANIFEST.json`与`PHASE1_QUALIFICATION_PLAN.json`为下一阶段审核材料。`upstream_readonly/`、`o24_port_gmrf_source/`与`patches/`让改动可逐文件检查。
'''
(R/'阶段0裁决_zh.md').write_text(report,encoding='utf-8')
for name in ['prepare_cpp.py','run_host_checks.py','finalize.py']:shutil.copyfile(P/name,R/name)
put(R/'ANALYSIS_NOTES.json',dict(issues=[dict(issue='Initial audit extractor expected void moveAlongPath; upstream returns bool',resolution='Corrected extractor signature, no algorithm/source change'),dict(issue='Windows VsDevCmd path needed native CMD quoting',resolution='Corrected host environment invocation; no VM/ROS and no environment secrets printed')],all_physical_results_unchanged=True))
source_manifest=[dict(path=p.relative_to(R/'o24_port_gmrf_source').as_posix(),sha256=sha(p))for p in sorted((R/'o24_port_gmrf_source').rglob('*'))if p.is_file()]
put(R/'O24_PREPARED_SOURCE_SHA256.json',dict(status='SOURCE_PREPARED_NOT_COMPILED_AS_ROS',files=source_manifest))
print(json.dumps(dict(status='STAGE0_COMPLETE_WITH_EXPLICIT_RUNTIME_AND_RNG_HOLDS',report=str(R/'阶段0裁决_zh.md'),new_VM=0,new_ROS=0)))
