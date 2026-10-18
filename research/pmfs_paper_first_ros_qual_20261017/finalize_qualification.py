from pathlib import Path
import csv,hashlib,json,math,shutil,subprocess
import numpy as np
R=Path(__file__).resolve().parent;O=R/'analysis';PROJECT=R.parents[1]
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,rs):
 with p.open('w',newline='',encoding='utf-8')as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
contexts=json.loads((O/'CONTEXTS.json').read_text());readout=rows(O/'NATIVE_READOUT.csv');assert len(readout)==len(contexts)
parity=[]
for c,r in zip(contexts,readout):
 truth=np.array(c['truth']);native_mean=np.array([float(r['mean_x']),float(r['mean_y'])]);native_top=np.array([float(r['top5_x']),float(r['top5_y'])]);variance=float(r['variance_m2'])
 assert abs(variance-c['info']['full_variance_m2'])<2e-6
 parity.append(dict(role=c['role'],update=c['update'],native_mean_error_m=float(np.linalg.norm(native_mean-truth)),native_top5_error_m=float(np.linalg.norm(native_top-truth)),native_variance_m2=variance,native_python_variance_abs_error=abs(variance-c['info']['full_variance_m2'])))
episodes=rows(O/'EPISODES.csv');support=[];clocks=[]
for e in episodes:
 role=e['role'];d=R/'cases'/role;runtime=d/'runtime';meta=json.loads((d/'CASE_META.json').read_text());nav=json.loads((runtime/'NAVIGATION_MAP_METADATA.json').read_text());truth=meta['source_xyz']
 final=[p for p in parity if p['role']==role][-1]
 assert abs(final['native_top5_error_m']-float(e['declared_top5_error_m']))<1e-5
 assert abs(final['native_variance_m2']-float(e['variance_m2']))<1e-5
 grid=np.fromfile(runtime/'navigation_map.s8','i1').reshape(nav['height'],nav['width']);scale=25;cellsize=float(np.float32(nav['resolution']*scale))
 fx=int((truth[0]-nav['origin_x'])/nav['resolution']);fy=int((truth[1]-nav['origin_y'])/nav['resolution'])
 cx=int(np.float32(np.float32(truth[0])-np.float32(nav['origin_x']))/np.float32(cellsize));cy=int(np.float32(np.float32(truth[1])-np.float32(nav['origin_y']))/np.float32(cellsize))
 block=grid[cy*scale:(cy+1)*scale,cx*scale:(cx+1)*scale];count=int(np.sum(block!=0))
 support.append(dict(role=role,case=e['case'],source_x=truth[0],source_y=truth[1],source_z=truth[2],fine_source_col=fx,fine_source_row=fy,fine_source_occupancy=int(grid[fy,fx]),coarse_source_col=cx,coarse_source_row=cy,coarse_source_pixel_count=block.size,coarse_source_nonfree_pixels=count,passes_author_all_pixels_free_rule=count==0,actual_source_supported=e['truth_supported'],source_or_map_changed=False))
 trace=rows(runtime/'physical_clock_trace.csv');timeline=rows(R/'world_provenance'/e['case']/'PHYSICAL_FRAME_TIME.csv')
 timeline_byframe={int(t['frame']):t for t in timeline};loops=[t for t in trace if t['reason']=='loop']
 nominal=[int(t['frame'])for t in loops];clock=json.loads((runtime/'CLOCK_SENSOR_RATE_PREFLIGHT.json').read_text())
 clocks.append(dict(role=role,PMFS_use_sim_time=False,robot_clock_factor=clock['real_time_factor'],PID_wall_rate_Hz=clock['gas_samples_per_wall_second'],anemometer_wall_rate_Hz=clock['wind_samples_per_wall_second'],player_use_sim_time=meta['player']['use_sim_time'],nominal_player_wall_Hz=meta['player']['player_freq'],actual_loaded_frames=nominal,official_loop=meta['official_playback_loop'],frame_decreases=sum(b<a for a,b in zip(nominal,nominal[1:])),first_original_gas_snapshot_time_s=float(timeline_byframe[nominal[0]].get('physical_snapshot_time_s',timeline_byframe[nominal[0]].get('frame_time_s',0))) if nominal else None,source='Exact public-launch clock profile and disclosed player adapter; original author trial clock unavailable',native_cutoff_seconds=300,cutoff_source='GitHub default, not claimed a universal paper limit'))
write(O/'INDEPENDENT_NATIVE_READOUT_PARITY.csv',parity);write(O/'SOURCE_SUPPORT_CHAIN.csv',support);put(O/'CLOCK_DOMAINS.json',clocks)
wind=json.loads((O/'WIND_SEMANTICS_AUDIT.json').read_text());assert all(r['GMRF_callbacks_above_0p2rad']==0 for r in wind['rows'])
# Preserve original dependency implementation and all existing adaptation provenance.
old=PROJECT/'workspace/PMFS_OFFICIAL_REPRO_AUDIT_20261016';dep=R/'dependency_provenance';dep.mkdir(exist_ok=False)
shutil.copytree(old/'paper_baseline_2024/gmrf_original',dep/'gmrf_original_2024')
for name in ['GMRF_2024_BUILD_RECEIPT.json','GMRF_STARTUP_TF_VALIDITY_ONLY.patch','GMRF_TFQUALIFIED_BUILD_RECEIPT.json','PUBLIC_CLOCK_PLAYER_BUILD_RECEIPT.json','PUBLIC_CLOCK_PLAYER_LOOP_ADAPTER.patch']:
 shutil.copyfile(old/'paper_baseline_2024'/name,dep/name)
shutil.copyfile(old/'PINNED_PLAYER_IDENTITY.json',dep/'PINNED_PLAYER_IDENTITY.json')
put(O/'FINAL_VERDICT.json',dict(status='PASS_COMPLETE_ROS_BUILD_AND_A2_B2_IMPLEMENTATION_INPUT_READOUT_CHECKS_PAPER_RESULT_MATCH_NOT_ESTABLISHED',primary_completed=2,technical_trials_retained=2,native_goals_total=3,native_variance_declarations=2,successful_localization_by_small_distance_not_claimed=True,new_gas_worlds=0,AIMMD_runs=0,strict_2024_author_experiment_reproduction=False,age_radius_fallback_disclosed=True,full_source_parameters_local_wind_and_public_clock_validated=True,known_boundaries=['One completed episode per case, not 30 independent author trials','Paper-first reconstruction changes Eq6 and paper-specific parameters, with all engineering adapters listed','Age-dependent coverage law remains absent; retained pinned centre-cell event','B2 true source excluded by pinned conservative source support; no source/map alteration','Native full forward candidate maps and per-thread random states were not captured in these qualification episodes; posterior/Omega/windows/raw sensor traffic are retained','TF wind check establishes consistency with observed history; exact internal TF-owner snapshot not captured','No statistically supported claim about published PMFS limitations or AIMMD effectiveness']))
report=f'''# 论文优先PMFS：完整ROS构建与A2/B2小规模验收

**完整PMFS ROS节点、公共模块编译及两场景实现/输入/读出核验完成；尚未复现论文统计表现。AIMMD未运行。** 原生程序两次都因方差小于1m²触发声明，但实际位置误差较大，不能把程序返回true称为准确找到了源。

|配置|声明Top-5%误差m|搜索时间s|完整方差m²|源更新|有效消费窗口|
|---|---:|---:|---:|---:|---:|
|A2|4.85474|33.5465|0.665675|2|35|
|B2|4.36641|14.4709|0.328695|1|20|

正式论文每配置30次，本轮每配置1次、使用已生成的气体世界。此前图示近似读数A2约0.6m/87s、B2约2.3m/110.5s，只列为背景，不能用一回合对30次平均作统计复现裁决。本轮表现没有达到这些均值，保留结果，不按误差调参数或重跑挑选。

## 本次实际运行的身份

固定作者提交a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533，185个原作者源码/配置文件逐Git blob与SHA校验，完整gsl_server/gsl_actions提交文件已恢复；DDA固定e852a1870bcc5a9285244ffc1111d65e7e6e776a，StateMachine固定3805501e55a272bf917cf5b1eb50b31d7146daed。构建PMFS与必需公共模块、完整ActionServer和辅助程序；作者支持按开关关闭的其他定位算法没有编入，不是只编译公式片段。

首轮全新构建约131.7秒，矩形修正后增量重编约10.1秒。最终实跑二进制SHA256：`78ca758e1b79a8e2f9ebe0480cdbad6211baba512523ef664160c015aa1a5dec`。所有对象来自新构建目录，没有混用July旧PMFS对象。已有GMRF和气体player作为明确锁定的运行依赖复用，其实际二进制SHA在新运行前再次验证，不能称它们也在本轮重编译。

按用户规则：论文明确的Eq6平方、Eq8评分系数1、声明方差门槛1m²优先；论文没有给出的实现细节沿用上述固定GitHub。年龄覆盖无可执行增长律，保留中心占格事件并登记差异，没有补造r(age)。本版本叫“论文优先重建基线”，不是已找回作者当年的实验程序。

## 必要适配单独保留

1. `PAPER_EQ6`：置信度指数仅加Omega平方，属于论文公式对齐。
2. `BUILD_ONLY`：Release、无GUI/Profiler、禁止主程序获取完整真风，选择Common/PMFS，补系统magic_enum包含路径。
3. `INPUT_VALIDITY_AND_PASSIVE_TRACE`：无观测时等待，不制造一次气体未检出；记录实际窗口，保留原0.4秒测量时长。
4. `MAP_STARTUP_GUARD`：地图回调之前不读未初始化的地图派生数组。
5. `PASSIVE_SOURCE_OMEGA_TRACE`：记录源后验、接触log-odds、Omega、confidence及估计风，不改源评分。
6. `RECTANGULAR_READOUT`：作者两处y遍历上界误写为width。本次只改成height。3×5均匀概率控制中原方差0.8、完整域正确值2.6666667；5×3与方形控制也通过。没有开放源格、改地图或移动真源。
7. GMRF保留历史估计器，只复用既有缺TF拒收和被动记录变体；player复用已记录的旧循环/壁钟节律适配。原始源码、补丁、参数和依赖身份分别保存。

这些均不计为创新收益。完整运行与此前614张固定图的离线公式对照不是同一实验，不合并成一张提升表。

## 已核对的运行条件

- 两场实际节点参数均从ROS服务读取并逐项比较：D=1、方差1、局地风、0.4秒窗口、源网格scale25、原噪声/记录/预热等。
- A2、B2实际Nav2地图与固定提交的PGM逐像素完全一致；既有3606个气体帧全部SHA核验，无新气体世界。
- A2/B2消费窗口均非空，最少分别3/4次浓度、7/8次风；没有空窗口被当成未检出。
- 每次源更新概率有限、非负且总质量为1，实际Omega/confidence满足论文Eq6；独立C++重算Top-5%、均值和全概率方差，复现程序输出误差与声明条件。
- 主程序编译时没有GADEN真风查询支持，实际使用GMRF；物理真风查询均为单受体传感器请求。风不是零数组：A2传感器真风幅值约0.377–0.819m/s，B2约0.031–0.217m/s。
- 原始风消息到downwind接口共1632对，π转换最大误差小于1.2e-7rad；GMRF非零风159个接受回调均能在存档TF时序中得到一致方向。B2两次零速按原代码取direction0，不拿零向量角度判错。两场各有一个重复header时间戳，审计保留多条消息、以速度共同匹配，未覆盖丢失。TF检查不冒称恢复了每次内部TF的唯一owner。
- 保留GitHub公开时钟配置：机器人ROS约5×壁钟、PMFS用壁钟、PID约10Hz壁钟、风约20Hz壁钟、气体player按壁钟文件节律加载；另保存原气体物理帧时间和循环。该加速耦合是本重建的明确身份，不是已证明等同作者原实验时间。300秒上限来自固定GitHub启动文件，不写成所有PMFS实验的论文统一上限。

## 源域和技术失败

源域逐像素链在`analysis/SOURCE_SUPPORT_CHAIN.csv`。B2真源不在448个合法候选格内，必须先区分粗网格保守过滤与实际气体源位置，不能用本轮B2评价“是否把真源概率救回”。地图与真源都保持原样。本轮没有把它直接归结为正式论文PMFS的缺陷。

保留两次A2技术记录：首次核验过早遇到参数延迟声明（发过1个goal、尚无源更新）；第二次同DDS域重启时Nav2生命周期通信超时（未发goal）。最终A2域227、B2域228，各自只发1个goal，合计3个实际goal。没有因为误差较大增加算法重复或挑选种子。

## 结束裁决

**实现与输入核验通过；论文统计复现仍未成立。** 已排除本轮的公式未应用、错用旧PMFS二进制、参数未生效、地图文件错配、空观测、整片零风及简单180°风方向接反。尚不能把剩余误差唯一归因，也不能称论文方法已经被完整复现或AIMMD具有增益。

下阶段若继续，应围绕公开代码版本、纸面年龄覆盖缺口、源支持和明确时钟条件规划比较；本轮到此完成小规模验收，不自动启动AIMMD或30次统计批次。包内不包含全部物理世界文件或可移植ROS安装；原世界路径与逐帧哈希、所有本轮原始ROS记录、源代码与编译记录均给出。
'''
(R/'验收结论_zh.md').write_text(report,encoding='utf-8')
put(R/'DELIVERY_STATE.json',dict(status=json.loads((O/'FINAL_VERDICT.json').read_text())['status'],episodes=episodes,binary_sha256='78ca758e1b79a8e2f9ebe0480cdbad6211baba512523ef664160c015aa1a5dec',new_worlds=0,AIMMD=0,source_support_chain=support,full_paper_reproduction=False,main_task_small_run_implementation_qualification_complete=True))
print(json.dumps(dict(status='POSTFLIGHT_PASS',episodes=len(episodes),source_support=support),ensure_ascii=False))
