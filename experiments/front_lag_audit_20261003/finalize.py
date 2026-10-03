"""Assemble audit evidence, verification and Chinese report. No simulation."""
from pathlib import Path
import json, hashlib, zipfile, subprocess, sys
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'evidence/front_lag_audit_20261003'
LOCAL=Path('C:/work/FRONT_LAG_AUDIT_20261003');SOURCES=LOCAL/'sources'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def table(df):return df.to_markdown(index=False,floatfmt='.2f')

d=pd.read_csv(OUT/'DISTANCE_SUMMARY.csv');f=pd.read_csv(OUT/'TIMESCALE_SUMMARY.csv');r=pd.read_csv(OUT/'RETARDED_BACKTRACE.csv');a=pd.read_csv(OUT/'ADVECTIVE_TIMESCALES.csv');m=pd.read_csv(OUT/'MEASUREMENT_FLOOR.csv')
assert sorted(d.distance_m.unique().tolist())==[50,100,200,300,500,750,1000]
assert not r[(r.platform=='lidar')&r.height_or_bin.isin([42,59])].shape[0]
assert not r[(r.platform=='lidar')&(r.distance_m<=300)].temporally_resolved.any()
supported=r[r.history_supported]
assert np.allclose(supported.normalized_endpoint_mismatch,supported.endpoint_mismatch_m/supported.distance_m)
assert np.allclose(supported.endpoint_mismatch_m,np.hypot(supported.inst_east_m-supported.ret_east_m,supported.inst_north_m-supported.ret_north_m))
assert np.allclose(supported.tau_adv_s,supported.distance_m/supported.speed_m_s)
check=pd.read_csv(OUT/'FRONT_TIMESCALES.csv');assert not check[(check.platform=='lidar')&(check.window_s<300)].resolved.any()

# Audit requested speed screening separately; raw coverage sensitivity is not a new gate.
import h5py
import xarray as xr
rows=[]
manifest=pd.read_csv(OUT/'INPUT_MANIFEST.csv')
identity=[]
records={folder:json.loads((SOURCES/f'zenodo_{rid}.json').read_text(encoding='utf-8')) for folder,rid in [('B_WiscoDISCO21_Lidar',5213039),('B_WiscoDISCO21_RAAVEN',5142491),('B_WiscoDISCO21_M210',5160346)]}
for item in manifest.to_dict('records'):
 p=Path(item['path']);expected=next(x for x in records[p.parent.parent.name]['files'] if x['key']==p.name)
 actual='md5:'+hashlib.md5(p.read_bytes()).hexdigest()
 assert actual==expected['checksum'] and p.stat().st_size==expected['size']
 identity.append({'file':p.name,'official_checksum':expected['checksum'],'actual_checksum':actual,'size_match':True,'checksum_match':True})
pd.DataFrame(identity).to_csv(OUT/'OFFICIAL_INPUT_IDENTITY_QA.csv',index=False)
coordinate_rows=[{'platform':'lidar','coordinate_status':'No coordinates in raw profile file; paper deployment site only','latitude':None,'longitude':None,'source':'ESSD2022 section3'}]
for file,q in pd.read_csv(OUT/'M210_TEMPERATURE.csv').groupby('file'):
 coordinate_rows.append({'platform':'M210','file':file,'coordinate_status':'author published raw table','latitude':float(q.lat.median()),'longitude':float(q.lon.median())})
for file,q in pd.read_csv(OUT/'RAAVEN_10s_vectors.csv').groupby('file'):
 coordinate_rows.append({'platform':'RAAVEN','file':file,'coordinate_status':'author raw position summarized over accepted10s bins; NOT fixed site','latitude':float(q.lat_approx.median()),'longitude':float(q.lon_approx.median()),'min_lat':float(q.lat_approx.min()),'max_lat':float(q.lat_approx.max()),'min_lon':float(q.lon_approx.min()),'max_lon':float(q.lon_approx.max())})
pd.DataFrame(coordinate_rows).to_csv(OUT/'PLATFORM_COORDINATES.csv',index=False)
for item in manifest.to_dict('records'):
 p=Path(item['path'])
 if 'wind_profiles' in p.name:
  with h5py.File(p) as ds:
   time=ds['time'][:];s=ds['windSpeed'][:];direc=ds['windDir'][:];z=ds['height'][:]*1000
  for h in [76,93]:
   k=np.argmin(abs(z-h));valid=np.isfinite(s[:,k])&np.isfinite(direc[:,k])&(s[:,k]<100)&(direc[:,k]>=0)&(direc[:,k]<=360)&(time>=13)&(time<23)
   for cut in [.1,.5,1.]:rows.append({'file':p.name,'height':h,'speed_screen':cut,'valid_points':int((valid&(s[:,k]>=cut)).sum()),'scope':'raw coverage only; .1 not reintegrated'})

# Descriptive, explicitly post-QC decomposition; never used to choose events or gates.
from scipy.integrate import trapezoid
decomp=[]
for item in manifest.to_dict('records'):
 p=Path(item['path'])
 if 'wind_profiles' not in p.name:continue
 with h5py.File(p) as ds:time=ds['time'][:]*3600;s=ds['windSpeed'][:];di=ds['windDir'][:];z=ds['height'][:]*1000;date=int(ds['date'][()])
 for h in [76,93]:
  k=np.argmin(abs(z-h));valid=np.isfinite(s[:,k])&np.isfinite(di[:,k])&(s[:,k]>=.5)&(s[:,k]<100)&(di[:,k]>=0)&(di[:,k]<=360)
  tt=time[valid];uu=-np.sin(np.radians(di[valid,k]));vv=-np.cos(np.radians(di[valid,k]))
  for row in r[(r.date==date)&(r.platform=='lidar')&(r.height_or_bin==h)&r.history_supported].itertuples():
   b=(pd.Timestamp(row.utc)-pd.Timestamp(str(date),tz='UTC')).total_seconds();start=b-row.tau_adv_s
   knots=np.unique(np.r_[np.linspace(start,b,int(np.ceil(row.tau_adv_s/5))+1),tt[(tt>start)&(tt<b)]])
   # Unit direction is interpolated, then renormalized so this integral's speed stays current speed.
   uk=np.interp(knots,tt,uu);vk=np.interp(knots,tt,vv);norm=np.hypot(uk,vk)
   if np.any(norm<1e-8):continue
   ddir=-row.speed_m_s*np.array([trapezoid(uk/norm,knots),trapezoid(vk/norm,knots)])
   inst=np.array([row.inst_east_m,row.inst_north_m]);full=np.array([row.ret_east_m,row.ret_north_m])
   decomp.append({'date':date,'height_m':h,'utc':row.utc,'distance_m':row.distance_m,'temporally_resolved':row.temporally_resolved,'angular_mismatch_deg':row.angular_mismatch_deg,'total_endpoint_mismatch_m':row.endpoint_mismatch_m,'constant_speed_direction_change_proxy_m':float(np.linalg.norm(inst-ddir)),'speed_weighting_residual_m':float(np.linalg.norm(ddir-full)),'scope':'post-QC descriptive decomposition; normalized interpolated direction, <=5s integration quadrature is not observed5s wind; terms are vector components, scalar norms not additive; not a gate'})
pd.DataFrame(decomp).to_csv(OUT/'DIRECTION_SPEED_DECOMPOSITION.csv',index=False)
for (date,L),q in r[(r.platform=='lidar')&r.height_or_bin.isin([76,93])].groupby(['date','distance_m']):
 for cut in [.5,1.]:
  s=q[(q.speed_m_s>=cut)&q.history_supported];rs=s[s.temporally_resolved]
  rows.append({'date':int(date),'distance_m':int(L),'speed_screen':cut,'valid_points':len(s),'resolved_points':len(rs),'median_mismatch_m':float(s.endpoint_mismatch_m.median()) if len(s) else None,'resolved_max_mismatch_m':float(rs.endpoint_mismatch_m.max()) if len(rs) else None,'scope':'endpoint-screen sensitivity; historical .5m/s base retained'})
pd.DataFrame(rows).to_csv(OUT/'SPEED_SCREEN_SENSITIVITY.csv',index=False)

# Source archive inventories and literature are evidence, distinct from observational inputs.
source_rows=[]
for p in sorted(SOURCES.iterdir()):
 if p.is_file() and p.suffix in ['.json','.pdf','.txt','.html']:
  source_rows.append({'path':str(p),'archive_path':'sources/'+p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
pd.DataFrame(source_rows).to_csv(OUT/'SOURCE_MANIFEST.csv',index=False)
js('PROTOCOL_IMPLEMENTATION_HISTORY.json',{
 'initial_freeze':'Dates/ranges/height exclusions/window rules and engineering sensitivity screen fixed before initial numerical run. Earlier Wisco summaries already seen; not a blind preregistration.',
 'implementation_fixes':['NumPy1.26 lacks np.trapezoid: use scipy.integrate.trapezoid before any integration output.', 'Onset persistence checks now enforce gap<=1.5cadence.', 'After preliminary QC, RAAVEN bin timestamp changed from median time to last accepted sample, so no bin contains data from future relative to its timestamp; keep within-bin full coordinate/height extrema for conservative history checks. All new outputs rerun.'],
 'unchanged':['event dates','distance grid','lidar calculations','old gates','new assumed-bound screen','no simulation authorization'],
 'final_freeze_file':'PRE_ANALYSIS_FREEZE.json identifies final corrected implementation, not a pre-first-look preregistration',
 'remaining_speed_sensitivity_scope':'SPEED_SCREEN_SENSITIVITY.csv: .1/.5/1 raw lidar coverage, .5/1 endpoint filtering of primary integrations; .1 integrations not performed.',
 'post_QC_descriptive_only':'DIRECTION_SPEED_DECOMPOSITION.csv separates fixed-current-speed direction proxy from speed-weighting residual. Not a new gate or test.'})

key=d[['date','distance_m','n_total','n_temporally_resolved','tau_adv_median_s','Lambda_5min_median','Lambda_5min_p95','conditional_all_mismatch_median_m']]
times=f[(f.platform=='lidar')&f.height_or_bin.isin([76,93])&(f.window_s==300)][['date','height_or_bin','n','circular_change_p50_deg','circular_change_p95_deg','tau_met30_median_s']]
mobile=r[r.platform=='RAAVEN_mobile'];strict=int(mobile.mobile_height10m_pos50m_screen.fillna(False).sum());relaxed=int(mobile.mobile_height20m_pos100m_screen.fillna(False).sum())
onset=pd.read_csv(OUT/'ONSET_PROXIES.csv');os=onset[(onset.platform=='lidar')&onset.height_or_bin.isin([76,93])][['date','height_or_bin','onset_proxy_utc','bracket_s']]
text=f'''# WiscoDISCO 湖风转换与有限传播时间：真实气象 R0 审计

正式决定：`R0_FRONT_LAG_HOLD_EVENT_SPECIFIC`。本轮没有建立“湖风转换已造成真实气源定位错误”的证据，也没有证明该机制不存在。该允许的代码名称在本报告中表示合同/解析能力不足的 HOLD，并不表示已证明只有一个日期成立。**不进入 transient puff 或源反演阶段。**

## 授权范围与旧结果

仅处理真实 WiscoDISCO 原始风、位置、温湿度数据及官方元数据。保持 R1/R1A/R1B/R3/TIBL-R0 原决定，TIBL 0.01 门与跳过的 source stage 不变。本轮没有生成 plume/CFD/GADEN，没有运行 PMFS、训练或闭环。用户目标仍为未知源坐标反演；此气象筛查不是定位性能实验。

日期严格冻结为 2021-05-22 与 2021-05-24，分析时段均为 13–23 UTC。May21 未用作替代事件，也未加入补救性实验。所有七个距离使用完整的合格时段，不挑选最高变化窗口。输入 {len(manifest)} 个原始文件，字节和 SHA256 逐项见 INPUT_MANIFEST.csv；参数见 FRONT_EVENT_CONTRACT.json。已有汇总结果先前已知，本轮不能称为盲法预注册。

## 事件证据与引用修正

ESSD 2022 的 Table2 明确 May22 为西风转冷 SSE，May24 为南风/湖风高臭氧事件。section6 支持 May22 18 UTC 后间歇入侵和 18:30–19:00 平台低层温度不一致，描述 21 UTC 约250m、22 UTC 约100m marine layer。[ESSD 原文](https://essd.copernicus.org/articles/14/2129/2022/index.html)

用户所引 sawtooth（三次 May21 推进）、May22 近岸约18:30冷空气/约19:00持续东风、约100→300m 的叙述可在**RSC 2023 后续论文** section3.2/3.3 查到，应改正引用来源。它用4.5m站风由>180°持续转为90–180°、减速/降温并排除其他锋面识别湖风；这些是作者事件证据，不等于已恢复可逐秒计算的站点原始序列。[RSC DOI](https://doi.org/10.1039/D2EA00101B)。两篇论文层顶描述时段与方法不同，不能把文字数值拼接成一个精确层顶时序。

官方三个 Zenodo 档案完整元数据已抓取并逐文件核对：M210 24表、RAAVEN 12文件、lidar 12文件（六个profile与六个stare）。目录没有第四套DNR地面风原始文件。RSC正文确认地面风观测实际存在；本轮未恢复分钟级站风，不能写成“没有地面风”。RSC网页访问403，猜测ESI PDF地址404；不会用论文图像数字化值冒充原始数据。另核查 EPA 小时风档案入口，下载结果见 sources 内日志；小时聚合即便取得也不能支持1/2/5min回溯。[EPA 公开档案说明](https://aqs.epa.gov/aqsweb/airdata/download_files.html)

## 数据质量与同步合同

Lidar 主结果分开使用原生76/93m层，110/127/144m只作高度背景。42/59m不作主结果，不混成“84.5m”。两日全文件中位间隔分别 **313.5s、317.0s**，不是恰好300s；每个方向变化记录其实际时间差。原始文件没有作者逐点QC标志/已审计SNR阈值，有限值与风速筛查不能取代仪器精度合同。Lidar原文件只有date/height/snr/time/windDir/windSpeed，**没有站点坐标字段**；论文提供部署位置背景，不能声称原文件自带精确站坐标。

RAAVEN 用作者东/北风矢量，Flight_Flag=1/wind_flag=0。原始时间按UTC恢复，不采用与矢量不完全一致的published direction。10/30/60s风是过去bin的中位矢量，timestamp为该bin最后接受样本，避免使用未来数据；仍含平滑响应/代表性误差，不能叫逐点瞬时风。沿用此前独立地面高度锚点QA：May22三飞均不能通过双锚点，稳定post锚仅敏感性；May24前两飞可用双锚点，第三飞仍不通过。输出保留MSL与条件AGL，不用假设海拔补齐。

RAAVEN是移动采样。本轮既检查跨bin又检查bin内全高度/坐标极值；在10–100m verified-AGL历史、高度范围≤10m、位置bbox≤50m条件下，仅 **{strict}** 个回溯条目；放宽至20m/100m为 **{relaxed}** 个条目（距离、bin与时刻重复，非独立事件）。不能把移动路径的风变化直接当固定站时间变化。

M210只有温湿度/臭氧，没有风，原表为90s顺序高度支持。iMetFlag0、位置、高度与温度SD均保留在M210_TEMPERATURE.csv。不能把不同高度先后采样的温差当同一点风锋到达时间。

## 时标与运动学结果

方向变化采用最短圆周差，1/2/5/10min都输出。Lidar1/2min标记unresolved；不把插值算作观测。tau_met主定义为30°除以对应真实间隔的方向变化率，60°以及10min端点窗口作敏感性；风速变化时标另列。此定义不捕捉窗口内反转，且不是锋面空间传播时标。所有合格时刻统计如下：

{table(times)}

76m的5min窗口方向差P95，May22约54.53°、May24约26.93°；93m相应53.70°、26.61°。强变化不是每个间隔都存在，背景13–17UTC的方向变化本身也较大，不能当仪器误差或保证稳定背景。MEASUREMENT_FLOOR.csv将实测背景变化、未知仪器精度和假设误差界分开。

tau_adv=L/当前风速，Lambda=tau_adv/tau_met。下表跨两个原生主高度合并，行数是时间×高度条目，**不是独立重复样本**。偏差列是PWL条件计算、包含分辨率不足条目：

{table(key)}

500m的tau_adv中位数为86.04/103.95s；Lambda中位约0.087/0.080，P95约0.931/0.714。这支持部分时段“时标可接近”的可能，但不能把P95或最快个别变化代替典型事件。50–300m没有满足至少两采样间隔/三个实测点的lidar回溯；500m每天仅1条，750m为3/4条，1000m为7/15条。较长距离且低风速才能跨足够采样间隔，解析性和低速选择强耦合。

两个回溯使用相同tau，d_inst=-U(t)tau；d_ret=-积分 U(s)ds，PWL矢量积分并以因果past-hold检验插值敏感性。距离、坐标差、角差、角误差敏感性均在RETARDED_BACKTRACE.csv。**空间均匀时间风场是条件代理，不是严格偏差下界，也没有恢复移动锋面或真实源。**

50–1000m的原始条件偏差随距离增加；500m中位约25.11m/17.76m。但500m可解析个别值分别2070.50m/2701.86m，不能写成“500m源误差几公里”：它们在极低当前风速下用L/U延长tau，历史风更强，积分净位移已明显超过L。最大个例May22：93m、18:20:19UTC、1000m、当前0.566m/s、tau1766.8s、积分净位移5478.9m、两线差6471.7m。May24大例14:16:34UTC早于本算法的下午onset proxy。故大数还包含“当前速度估travel time”和速度变化的影响，不能归因风向相位或湖风过境。

另输出DIRECTION_SPEED_DECOMPOSITION.csv作明确标注的事后描述诊断：将历史矢量方向单位化，在相同tau内保持当前速度积分，比较方向变化代理与历史速度加权残差。两者是矢量分解，范数不能直接相加。这项诊断不选事件、不改判定；其本身仍受次采样间隔插值限制。

假设方向5/10/20°和风速0.1/0.5m/s分别报告。10°/.5m/s的保守三角界为2L sin(10°)+2tau*.5，表示两段估计分别允许误差后的最坏界，**不是经标定置信区间**。PWL与past-hold的差是插值敏感性，不能界定所有未采到的次分钟变化。按预先设定的探索性≥3连续解析点、≥30m且超过假设界+插值差筛查，两个日期均无连续稳定段。该筛查是工程诊断，不能据此宣布物理机制不存在。

## Onset、岸内陆时差与层顶

冻结的“17UTC以后由西侧进入90–180°并维持约15min”仅风标记输出：

{table(os)}

该规则不是论文风+温度+天气排除联合定义。May24窗口边界/早先海风历史尚未从地面序列核清，因此不能把这些时刻称独立锋面精确过境。移动RAAVEN的标记也不能与lidar或M210直接相减求传播速度。岸内陆onset lag、front speed与实测layer-top时序在decision中保持null并说明原因；未以字面18:30与19:00生成伪精确1800s合同。

## 最终判断与源定位主线

本轮发现真实风在分钟尺度可显著改变，并得到条件性回溯差异；但**没有两个独立真实湖风事件的、稳定超过经标定测量/采样误差的源相关偏差证据**。缺失的是分钟级固定近地风、同高度/同位置高频风历史、可核验锋面到达合同及逐样本仪器精度。不能因为这些未解就给PHYSICALLY_RELEVANT，也不能把未解析当STOP物理缺席。

因此保持 `R0_FRONT_LAG_HOLD_EVENT_SPECIFIC`，禁止下一阶段模型。此结果仅能写为“检验非稳态风与有限传播时间对源反演的潜在影响”；不能写成已发现湖岸特有定位盲区或已改进定位。若未来取得高频站风与精度合同，可以在原日期/距离网格复核；在取得前不追加机制模拟。

## 复现、验证与文件

Windows依赖 numpy/pandas/scipy/h5py/xarray/tabulate。运行experiments/front_lag_audit_20261003/run.py，再运行finalize.py。原始inputs默认在C:/work/LAKESHORE_GSL_DATA_20261002/data_external，可用WISCO_DATA_ROOT指定。此审计隔离输出位于C:/work/FRONT_LAG_AUDIT_20261003，原件未改写。

解析积分验证包括常量风、线性风和359→1°圆周差；输出核对tau=L/U、归一化偏差、端点坐标、排除低层及不把短窗当观测。20个输入逐一通过官方Zenodo文件大小和MD5身份核验（OFFICIAL_INPUT_IDENTITY_QA.csv），另附独立SHA256。修正历史见PROTOCOL_IMPLEMENTATION_HISTORY.json。完整ZIP含本轮使用的20个原始文件、来源PDF/元数据、代码及全部CSV/JSON；manifest保存逐文件SHA256。Git提交不重复装入原始百MB数据。

分支：`{subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()}`。本轮开始时base commit：`{json.loads((OUT/'FRONT_EVENT_CONTRACT.json').read_text(encoding='utf-8'))['base_commit']}`。最终commit见交付ZIP根目录MANIFEST.json（避免提交包含自身hash的循环）。输入manifest SHA256：`{sha(OUT/'INPUT_MANIFEST.csv')}`。
'''
(OUT/'REPORT_R0_FRONT_LAG_zh.md').write_text(text,encoding='utf-8')
js('VALIDATION.json',{'analytic_integral_constant_and_linear':'PASS','circular_359_to1':'PASS','output_tau_endpoint_normalization':'PASS','native_low_gates_excluded':'PASS','short_lidar_windows_not_observed':'PASS','mobile_bin_future_leakage_removed':'PASS; implementation reviewed','scientific_contract':'HOLD','source_inversion_executed':False})
(OUT/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n',encoding='ascii')

if '--zip' in sys.argv:
 branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip();commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 entries=[]
 for p in sorted(OUT.iterdir()):
  if p.is_file():entries.append((p,'evidence/'+p.name))
 for p in sorted((ROOT/'experiments/front_lag_audit_20261003').glob('*.py')):entries.append((p,'code/'+p.name))
 for row in manifest.to_dict('records'):entries.append((Path(row['path']),row['archive_path']))
 for row in source_rows:entries.append((Path(row['path']),row['archive_path']))
 zip_path=LOCAL/'R0_FRONT_LAG_EVIDENCE_20261003.zip'
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p,target in entries:z.write(p,target)
  z.writestr('MANIFEST.json',json.dumps({'branch':branch,'commit':commit,'files':[{'path':target,'sha256':sha(p),'bytes':p.stat().st_size} for p,target in entries]},ensure_ascii=False,indent=2))
 with zipfile.ZipFile(zip_path) as z:
  assert z.testzip() is None
  for p,target in entries:assert hashlib.sha256(z.read(target)).hexdigest()==sha(p)
 digest=sha(zip_path);zip_path.with_suffix('.zip.sha256').write_text(digest+'  '+zip_path.name+'\n',encoding='ascii')
 print(json.dumps({'branch':branch,'commit':commit,'zip':str(zip_path),'bytes':zip_path.stat().st_size,'sha256':digest},indent=2))
else:print('Report and validation complete')
