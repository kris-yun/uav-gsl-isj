"""Summarize the feature audit, preserve STOP decisions and package exact raw inputs."""
import pathlib,json,hashlib,zipfile,shutil
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent;EXP=ROOT/'experiments/lakeshore_observability'
OUT=ROOT/'evidence/wiscodisco_real_scene_feature_audit_20261003';BASE=pathlib.Path('C:/work/LAKESHORE_GSL_DATA_20261002')
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def js(name,value):(OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')
thermal=pd.read_csv(OUT/'M210_all_flight_thermal_features.csv');strict=thermal[thermal.policy=='strict_flag0'];usable=strict[strict.max_inversion10_100_C.notna()];strong=usable[usable.max_inversion10_100_C>=1]
ground=pd.read_csv(OUT/'RAAVEN_ground_reference_QA.csv');rw=pd.read_csv(OUT/'RAAVEN_300s_height_wind_thermo_table.csv');rp=rw[(rw.height_policy=='two_anchor_primary')&(rw.speed_screen==.5)];lid=pd.read_csv(OUT/'LIDAR_daily_direction_statistics.csv');ld=lid[lid.speed_screen==.5];cad=pd.read_csv(OUT/'LIDAR_native_cadence.csv');daily=pd.read_csv(OUT/'M210_daily_thermal_statistics.csv')
primary_shear=rp[rp.max_requested_direction_diff_deg>=30];points=pd.read_csv(OUT/'M210_QC_profile_points.csv');marker=rp[rp.utc.str.startswith('2021-05-24 17:40:00')].iloc[0]
feature=[{'candidate':'A_shallow_layer_height','observed':'6/16 usable profiles have>=1C sequential10..100m inversion proxy over3dates; strongest7.179C','task_time':'PARTIAL:90s means;only2of6 strongest pairs<=300s; no fixed-height persistence established','altitude_magnitude':'THERMAL_PROXY_PRESENT;true lake-breeze/TIBL top NOT_IDENTIFIED','replication':'YES_for_thermal_proxy_not_same_identified_lake_state','UAV_observable_state':'T/RH/P observable;air-mass/layer-top classifier NOT_VALIDATED','specific_GSL_failure':'NOT_TESTED','allow_GADEN':False},
 {'candidate':'B_near_source_vs_UAV_direction','observed':'5/13 two-height300s RAAVEN windows have>=30deg at60/100 target bins, one primary date;10/30m no primary coverage','task_time':'SEQUENTIAL_MOBILE_SAMPLES;not persistent simultaneous vertical shear','altitude_magnitude':'60..100m contrast yes;near-source10..30m unknown','replication':'PRIMARY_ONE_DATE;May22 post-anchor sensitivity only','UAV_observable_state':'own-height wind yes;near-source wind unavailable to UAV','specific_GSL_failure':'NOT_TESTED','allow_GADEN':False},
 {'candidate':'C_convergence_stagnation_hotspot','observed':'single-column lidar low speeds and M210 ozone context;no simultaneous horizontal vector map or source truth','task_time':'NOT_IDENTIFIED','altitude_magnitude':'CONVERGENCE_NOT_MEASURED','replication':'NOT_ESTABLISHED','UAV_observable_state':'single-point low speed/O3 do not determine convergence or source','specific_GSL_failure':'HOTSPOT_NOT_SOURCE_NOT_TESTABLE_WITH_THESE_RECORDS','allow_GADEN':False},
 {'candidate':'D_temperature_humidity_marker','observed':f"May24 17:40 primary window60/100 targets:T difference{marker.T_100m_C-marker.T_60m_C:.3f}C,RH difference{marker.RH_100m_percent-marker.RH_60m_percent:.3f}pp,wind difference{marker.max_requested_direction_diff_deg:.3f}deg",'task_time':'mean height sampling time gap31.09s;no simultaneous independent state labels','altitude_magnitude':'STRONG_JOINT_OBSERVABLE_PROXY','replication':'thermal/RH contrasts recur;joint marker-state classification not independently validated','UAV_observable_state':'YES_variables;NO_validated_lake_air_land_air_labels','specific_GSL_failure':'NOT_TESTED','allow_GADEN':False}]
js('FEATURE_GATE_AUDIT.json',feature)
decision={'decision':'REAL_SCENE_FEATURE_GATE_NOT_ESTABLISHED','current_parametric_front_mainline':'STOP','R1':'R1_HOLD_WEAK_OR_UNSTABLE','R1A':'R1A_RESIDENCE_SUFFICIENT_STOP_UPLIFT_ATTRIBUTION','R1B':'R1B_HOLD_MISMATCH_NOT_FRONT_LOCKED','new_GADEN_realizations':0,'new_CFD_runs':0,'Word_changes':0,'allowed_next_GADEN':False,'strongest_observed_feature':'low-altitude temperature structure and occasional joint60/100m thermo/wind contrast;not confirmed persistent near-source/UAV air-mass decoupling','strategic_disposition':'lake shore remains real application/validation;first-paper innovation should return to task-sufficient robust source inference/active sensing rather than claiming established lake-specific physics','observation_scope':{'raw_files':42,'RAAVEN':12,'M210':24,'lidar_daily':6,'usable_strict_M210':len(usable),'strong_M210_ge1C':len(strong),'strong_M210_dates':strong.date.nunique(),'RAAVEN_two_anchor_flights':int(ground.two_anchor_primary_accepted.sum()),'RAAVEN_post_anchor_flights':int(ground.post_anchor_sensitivity_accepted.sum()),'primary_joint_shear_windows':len(primary_shear),'primary_joint_shear_dates':primary_shear.date.nunique()},'interpretation':'NOT_ESTABLISHED is evidence insufficiency,not a proof that real lake features are absent;no new numerical gate added to old experiments'}
js('FINAL_DECISION.json',decision)
fig,axs=plt.subplots(1,3,figsize=(14,4),layout='constrained')
for date,q in usable.groupby('date'):axs[0].scatter([date]*len(q),q.max_inversion10_100_C,label=date)
axs[0].set_ylabel('10..100 m sequential positive T contrast (C)');axs[0].tick_params(axis='x',rotation=45);axs[0].grid(alpha=.2)
axs[1].plot(ld.date,ld.median_diff76_93,'o-',label='median');axs[1].plot(ld.date,ld.p90_diff76_93,'o-',label='90th percentile');axs[1].set_ylabel('Lidar76/93 m direction difference (deg)');axs[1].tick_params(axis='x',rotation=45);axs[1].legend();axs[1].grid(alpha=.2)
axs[2].scatter(range(len(rp)),rp.max_requested_direction_diff_deg);axs[2].axhline(30,ls='--',color='grey');axs[2].set_xlabel('RAAVEN primary300s window index');axs[2].set_ylabel('Available requested-height contrast (deg)');axs[2].grid(alpha=.2)
fig.suptitle('Real-scene audit: observed proxies; sequential sampling and coverage matter');fig.savefig(OUT/'real_scene_feature_overview.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(12,5),layout='constrained')
for name in ['WiscoDisco21_M210_20210522_F4.txt','WiscoDisco21_M210_20210522_F6.txt','WiscoDisco21_M210_20210524_F3.txt']:
 q=points[points.file==name];label=name.split('_')[-2]+'_'+name.split('_')[-1].split('.')[0]
 axs[0].plot(q.temperature_C,q.height_m,'o-',label=label);axs[1].plot(q.RH_percent,q.height_m,'o-',label=label);axs[2].plot(q.specific_humidity_g_kg,q.height_m,'o-',label=label)
for ax,label in zip(axs,['Temperature (C)','Relative humidity (%)','Specific humidity (g/kg)']):ax.set_xlabel(label);ax.set_ylabel('Published height AGL (m)');ax.set_ylim(0,130);ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.suptitle('Selected descriptive profiles,90s sequential means: not confirmed air-mass tops');fig.savefig(OUT/'thermal_and_humidity_examples.png',dpi=150);plt.close(fig)
allwind=rw[(rw.speed_screen==.5)&(rw.height_policy=='two_anchor_primary')];keycols=['file','utc','max_requested_direction_diff_deg','direction_60m_deg','direction_100m_deg','actual_height_60m','actual_height_100m','mean_height_sampling_time_gap_s','direction_resultant_R_60m','direction_resultant_R_100m']
sources=[{'id':'WISCO_ESSD2022','url':'https://essd.copernicus.org/articles/14/2129/2022/','type':'primary observation/data paper','supports':'sampling/QC;May22 published marine-layer height250m at21UTC and100m at22UTC;single documented evolution,not2independent events'}, {'id':'JGR2025','url':'https://collaborate.princeton.edu/en/publications/unsteady-land-sea-breeze-circulations-in-the-presence-of-a-synopt/','doi':'10.1029/2023JD040708','type':'primary author institution and existing author manuscript','supports':'idealized unsteady land-sea LES regimes and flow history;not empirical Wisco10..100m persistent layer statistics'}, {'id':'FASTEDDY2024','url':'https://impacts.ucar.edu/en/publications/application-of-the-ncar-fasteddysupsup-microscale-model-to-a-lake/','doi':'10.3390/atmos15070809','type':'primary NCAR institution publication record','supports':'independent Great Salt Lake June3_2022 case at5m horizontal LES;qualitative humidity/wind marker relevance;not quantitative validation of Wisco GSL or recurrence'}, {'id':'BOLTON_CALCULATION','url':'https://www.ncl.ucar.edu/Document/Functions/Contributed/satvpr_water_bolton.shtml','type':'official NCAR formula documentation','supports':'vapor pressure formula6.112exp(17.67T/(T+243.5));specific humidity computed using observed RH/P,kept derived and flagged'}]
js('LITERATURE_EVIDENCE.json',sources)
report=f'''# WiscoDISCO Real-Scene Feature Audit

## 决策

`REAL_SCENE_FEATURE_GATE_NOT_ESTABLISHED`：不授权新GADEN或CFD。旧R1/R1A/R1B判定原封不动；当前参数化锋面主创新路线STOP。这里的“未建立”不等于湖岸没有强结构：温度结构及个别联合风/温湿度对比很强，但尚不能识别源附近层与UAV层之间持久、湖岸特有的状态边界。

## 最强的实际观测

42个公开原始文件全部审计：12RAAVEN、24M210、6天lidar wind_profiles。M210严格iMetFlag0下，16个剖面可计算10..100m正温差；其中6个在3个日期出现>=1C（本数值只作描述，不作为事后GSL门槛）。最大7.179C，其他强剖面1.678..4.057C。这些是真实逐层观测中的温度对比，不是同一时刻的垂直场。6个强剖面里仅2个最大温差端点间隔<=300s，另4个相隔360..450s。

{strong[['file','max_inversion10_100_C','inversion_bottom_m','inversion_top_m','inversion_pair_elapsed_s','thermal_transition_proxy_m']].to_markdown(index=False,floatfmt='.3f')}

5月22日F4的7.179C来自完整飞行18:27:55/11.14m到18:33:55/59.63m，跨越6分钟且23.06m的温度stdev约3.00C。因此不能排除湖风入侵随时间变化，不能把这个数直接当作稳定层结。原R0冻结18:30..19:00窗口仍为1.271C，没有改旧窗口或判定。thermal_transition_proxy只是最大相邻正温度梯度的位置，层高标准差常有4..10m，且未把位温稳定区、局地逆温或该代理量认定为湖风层/TIBL顶。真层高各行保留空值。

## 风向解耦

RAAVEN原生alt是MSL。12个文件仅2个起飞前/着陆后30s地面参考满足IQR<=2m、差<=5m；二者均在5月24日。另{int(ground.post_anchor_sensitivity_accepted.sum())}个文件有稳定着陆参考，全部只作post-anchor敏感性。多数起飞前记录比着陆参考低约140m；这是记录/基准一致性问题，本审计不猜其故障来源。派生高度是相对起落地点的AGL估计，仍不含沿轨迹地形高度修正。两个参考一致也不是测量精度的独立认证。

主分析28个300s窗口，其中13个至少覆盖两个请求高度，有5个>=30deg。主分析无合格10/30m风观测，无任何完整四高度窗口。风向取逐样本方向的圆均值；同时报告风矢量均速和圆集中度R，避免把低风速/宽角分布当作可靠确定风向。

{primary_shear[keycols].to_markdown(index=False,floatfmt='.3f')}

最大102.425deg窗口在100m带只有8.7s观测、平均矢量风速0.895m/s、R0.560；应低置信解读。其他31..65deg样例亦来自移动、先后或多次穿层取样，300s分组只是任务预算窗口，不能写成维持300s的同时垂直风差。5月22日单着陆基准敏感性可见强差异，但不能与主分析等权堆成独立确认。

额外QA发现，作者wind_direction与由u/v计算的方向中位差为0，但每文件约0.36..1.15%的wind_flag0、速度>=0.5m/s样本差>1deg，少数差很大。产生原因未确认，不假装独立一致性验证全部通过。主分析自始使用u/v计算方向，没有据此回改结果；逐文件诊断在RAAVEN_UV_vs_published_direction_QA.csv，可用direction_qa.py复现。该质量边界也是谨慎解读偶发最大值的原因。

lidar原生低门为42/59/76/93m；10/30m无覆盖。42/59m的速度通常极低，近场质量没有作者给出的可直接应用SNR阈值，因此59m按近60m诊断列保留，主比较仅76/93m。该主比较日中位数1.87..3.12deg，偶有大差；其17m高度间距不能推论20..80m风向差很弱或很强。

{ld[['date','n_profiles','n_valid_76_93','median_diff76_93','p90_diff76_93','fraction_ge30','max_diff76_93']].to_markdown(index=False,floatfmt='.3f')}

原生中位采样间隔309..319s。5月23日有4个连续采样点跨约957s均>=30deg，5月24日有相邻点跨319s；只证明这些离散时刻的差异，不能宣称间隔期间连续存在或满足5..300s准稳态。stare日期/高度契约仍未解决，本轮排除。

## 温湿度标记与低风速积聚

5月24日17:40UTC主分析窗口，实际均高60.59/95.98m，方向差64.51deg，矢量风速8.23/5.21m/s，T为18.84/23.75C，RH为78.92/65.21%，两高度平均采样时间差31.09s。它是本轮值得保留的联合可观测对比，但低高度约12s、高高度约26s风样本、传感器不同变量QC，以及水平位置变化均限制解释。

RH下降可能只是升温造成，不能作为独立湿空气边界证据。本审计另计算比湿q和位温theta，严格遵守各自温湿压质量标志；例如M210强温差剖面的上下比湿变化跨正负，不能把RH单调变化硬解释为统一湖面空气标签。没有独立水面/陆面气团真值标签或留事件外分类验证，不报告“温湿度已能识别湖风气团”。

单柱低风速、M210臭氧值没有同时二维水平矢量图，无法求真实辐合；臭氧也不是受控泄漏源的示踪真值。因此“持久岸线辐合积聚”和“浓度热点不等于源”在这些文件中均不可确认。

## 四候选门审计

{pd.DataFrame(feature)[['candidate','task_time','altitude_magnitude','replication','UAV_observable_state','allow_GADEN']].to_markdown(index=False)}

A/D是可观测变量层面最值得保留的线索，B有个别大幅度但近源风/跨日期主证据缺失，C目前不具所需观测几何。没有把普通逆温、任意风切变当作湖岸独有，也没有因为变量大就推断GSL失效。

## 文献独立支持及缺口

正式Wisco论文明确报告5月22日海洋层由约250m/21UTC下降到约100m/22UTC；属于一个事件的两个时刻，不是层顶经常落30..80m的频率证据。[ESSD原文](https://essd.copernicus.org/articles/14/2129/2022/)

2025JGR研究支持非定常陆海热力循环及流动历史效应，但不能补齐本次近源风和任务内持续时间。[作者机构记录](https://collaborate.princeton.edu/en/publications/unsteady-land-sea-breeze-circulations-in-the-presence-of-a-synopt/)

FastEddy湖风锋论文是2024年Atmosphere文章，独立Salt Lake事件与5m水平LES提供情景支持，未用于给Wisco填造低空层顶、持久辐合或GSL误差。[NCAR机构记录](https://impacts.ucar.edu/en/publications/application-of-the-ncar-fasteddysupsup-microscale-model-to-a-lake/)

LMOS原始事件数据本轮不在输入集，没有假装完成其数值复核。现有JGR公开结果为统计X-Z切片，不用它构造新气体模拟；原数据审计对维度/时间重构的限制保持。独立论文不能替代本任务中缺测的场量。比湿为派生诊断，Bolton饱和水汽压公式来源[NCAR说明](https://www.ncl.ucar.edu/Document/Functions/Contributed/satvpr_water_bolton.shtml)。

## 输出与研究处置

EVENT_UAV10_100_FEATURE_TABLE.csv给出每个M210事件及最近lidar（<=180s）匹配；10/30m风向、确认逆温层高度及湖风层顶缺测处为空，不插值。平台空间分离显式标注。另有全日期lidar表、RAAVEN300s表、日统计、地面基准QA、质量门统计、热力原始均值/SD、臭氧背景、JSON门审计和PNG。

没有新的机制通过真实数据门。本任务完成后，湖岸保留应用/验证场景，第一篇主创新回到task-sufficient source/plume world model、robust source inference与active sensing的方法问题。这里不设计或运行新算法。若后续要重新论证一个气象特征，所缺的是同步近源与空中风、边界身份/高度及重复任务尺度证据；不会通过继续调这套参数化锋面补门。

开题Word未改动。建议措辞保持：“针对湖岸水陆热力差异可能形成的低空分层、局地辐合及空间非均匀风场，研究其对有限移动观测源判别信息的影响。”不写机制已证明。

复现：解压新目录后python experiments/lakeshore_observability/real_scene_audit/audit.py；默认原数据目录为C:/work/LAKESHORE_GSL_DATA_20261002，可按压缩包README指引指定raw输入目录。pandas/numpy/xarray/scipy/h5py用于读原始数据；matplotlib/tabulate用于报告。全部输入SHA在INPUT_MANIFEST中，旧R1/R1A/R1B清单验证写入DELIVERY_VALIDATION。分析契约在结果计算前记录，但本工作是探索审计，不声称一个预注册的、新数值PASS标准。
'''
(OUT/'REPORT_zh.md').write_text(report,encoding='utf-8')
(OUT/'.gitattributes').write_text('* -text -whitespace\n')
shutil.copyfile(EXP/'R1B_POSTMORTEM_STOP_AND_NEXT_HYPOTHESES_20261003.md',OUT/'STOP_PROTOCOL.md')
checks={}
for name in ['lakeshore_observability_r0_r2','lakeshore_r1a_deconfound_20261003','lakeshore_r1b_front_mismatch_20261003']:
 m=pd.read_csv(ROOT/'evidence'/name/'MANIFEST.csv')
 for q in m.itertuples():assert sha(ROOT/q.path)==q.sha256,q.path
 checks[name+'_manifest_members_unchanged']=len(m)
im=pd.read_csv(OUT/'INPUT_MANIFEST.csv')
for q in im.itertuples():assert sha(q.path)==q.sha256
freeze=json.loads((OUT/'PRE_ANALYSIS_FREEZE.json').read_text());assert sha(HERE/'audit.py')==freeze['script_sha256'];assert sha(OUT/'ANALYSIS_CONTRACT.json')==freeze['contract_sha256']
checks.update(raw_inputs_unchanged=42,analysis_contract_and_script_match=True,new_GADEN_runs=0,Word_edits=0)
js('DELIVERY_VALIDATION.json',checks)
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['MANIFEST.csv','SHA256SUMS'])+sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
members=[(p,p.relative_to(ROOT).as_posix()) for p in files]+[(pathlib.Path(q.path),q.archive_path) for q in im.itertuples()]
manifest=[dict(path=arc,bytes=p.stat().st_size,sha256=sha(p)) for p,arc in members];pd.DataFrame(manifest).to_csv(OUT/'MANIFEST.csv',index=False)
(OUT/'SHA256SUMS').write_text(''.join(q['sha256']+'  '+q['path']+'\n' for q in manifest))
archive=pathlib.Path('C:/work/WISCODISCO_REAL_SCENE_FEATURE_AUDIT_20261003.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p,name in members:z.write(p,name)
 for p in [OUT/'MANIFEST.csv',OUT/'SHA256SUMS']:z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for q in manifest:assert hashlib.sha256(z.read(q['path'])).hexdigest()==q['sha256']
digest=sha(archive);archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
print(json.dumps({'decision':decision['decision'],'ZIP':str(archive),'bytes':archive.stat().st_size,'members':len(manifest)+2,'SHA256':digest},indent=2))
