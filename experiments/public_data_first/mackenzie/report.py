from pathlib import Path
import json,sys,hashlib,shutil
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'evidence/public_data_first_20261003/mackenzie'
ROOT=Path(r'C:\work\MACKENZIE_CHANNEL_SEEP2_REAL_DATA_20261003')
sys.path.insert(0,str(Path(__file__).parent))
from audit import inverse_inputs,kernel,CONFIG,TRANSFORM

def main():
    frames={p.stem.split('_')[0]:pd.read_csv(p) for p in OUT.glob('*_processed.csv')}
    rows=pd.read_csv(OUT/'WIND_REPRESENTATION_INVERSION.csv')
    sensitivity=pd.read_csv(OUT/'sensitivity_broader_dispersion/WIND_REPRESENTATION_INVERSION.csv')
    # Descriptive source-relative author curtain plots, separate from inverse inputs.
    se,sn=TRANSFORM.transform(-135.477520,69.319583);a=np.deg2rad(188.54163351823857)
    fig,axes=plt.subplots(2,2,figsize=(11,8))
    for ax,(name,d) in zip(axes.flat,frames.items()):
        y=np.cos(a)*(d.e-se)-np.sin(a)*(d.n-sn)
        m=ax.scatter(y,d.z,c=np.maximum(d.ch4-CONFIG['primary_background_ppm'][name[:2]],0),s=4,cmap='turbo')
        ax.set_title(name+' source-relative author frame');ax.set_xlabel('crosswind / m');ax.set_ylabel('height / m');fig.colorbar(m,ax=ax,label='CH4 enhancement / ppm')
    fig.tight_layout();fig.savefig(OUT/'AUTHOR_CURTAIN_COORDINATE_REPRODUCTION.png',dpi=140);plt.close(fig)
    consistency=[];centerlines=[];windprofiles=[]
    for arm in CONFIG['arms']:
        r=rows[(rows.wind_arm==arm)&(rows.background=='author_code')]
        for platform in ['CP','OP']:
            one=r[r['case']==platform+'1'].iloc[0];two=r[r['case']==platform+'2'].iloc[0]
            consistency.append(dict(platform=platform,wind_arm=arm,near_far_source_estimate_separation_m=float(np.hypot(one.source_easting_MAP_m-two.source_easting_MAP_m,one.source_northing_MAP_m-two.source_northing_MAP_m)),single_curtain_distance_identifiability='NOT_ESTABLISHED',wind_only_causality='NOT_ESTABLISHED'))
        for name,d in frames.items():
            row=r[r['case']==name].iloc[0];s=np.array([row.source_easting_MAP_m,row.source_northing_MAP_m]);v=d[['u','v']].mean().to_numpy();v/=np.linalg.norm(v)
            # Mean-wind straight centerline intersection with mean receptor plane.
            midpoint=d[['e','n']].mean().to_numpy();q=s+((midpoint-s)@v)*v
            centerlines.append(dict(flight=name,wind_arm=arm,inferred_source_easting_m=s[0],inferred_source_northing_m=s[1],predicted_mean_plane_centerline_easting_m=q[0],predicted_mean_plane_centerline_northing_m=q[1],meaning='straight mean-advection centerline only; instantaneous wind does not reconstruct a propagation streamline'))
    pd.DataFrame(consistency).to_csv(OUT/'NEAR_FAR_CONSISTENCY.csv',index=False)
    pd.DataFrame(centerlines).to_csv(OUT/'INFERRED_PLUME_CENTERLINES.csv',index=False)
    for name,d in frames.items():
        for level,g in d.groupby(np.floor(d.z/2)*2):
            u,v=g[['u','v']].mean();windprofiles.append(dict(flight=name,height_bin_lower_m=level,n=len(g),mean_u_east_m_s=u,mean_v_north_m_s=v,mean_vector_speed_m_s=np.hypot(u,v),direction_from_deg=np.rad2deg(np.arctan2(-u,-v))%360,mean_CH4_ppm=g.ch4.mean()))
    pd.DataFrame(windprofiles).to_csv(OUT/'HEIGHT_WIND_PROFILES.csv',index=False)
    # Numerical and design QA before any final claims.
    d,sources,_,_=inverse_inputs(frames,['CP1','CP2'])
    shifted={k:v.assign(e=v.e+1234,n=v.n-5678) for k,v in frames.items()}
    dd,ss,_,_=inverse_inputs(shifted,['CP1','CP2'])
    translation=float(np.max(np.abs(ss-sources-np.array([1234,-5678]))))
    assert translation<1e-7
    k=kernel(np.array([[100.,-100.]]),np.zeros((1,2)),np.zeros((1,2)),np.ones((1,2))*5,np.zeros((1,2)),.1,.1)
    assert k[0,0]>0 and k[0,1]==0
    qa=dict(inverse_domain_translation_max_error_m=translation,upwind_zero_check=True,source_truth_only_fixed_source_reproduction_and_postfit_evaluation=True,source_grid_spacing_alongwind_m=13.,source_truth_survey_uncertainty='not independently specified; reference center of finite seep',ground_arm_not_fabricated=True)
    (OUT/'QA.json').write_text(json.dumps(qa,indent=2),encoding='utf8')
    qual=dict(dataset='Mackenzie Channel Seep 2',doi='10.5281/zenodo.20019779',source_truth='published WGS84 reference point 69.319583,-135.477520; finite seep footprint; survey uncertainty not specified',source_type='natural geological methane seep',scene='river channel/wetland/water Arctic',flight_count='4: CP1/CP2/OP1/OP2, one site/day; two platforms',gas='CP Aeris dry CH4 2Hz; OP laser nominal100Hz but published CSV approx10Hz; raw CH4 and CH4_dry choices differ by method',wind='corrected horizontal 2D on both UAVs; CP wind north offset +19deg in author notebooks; not shared 3D wind data',wind_correction='published motion-corrected columns; author paper method and CP north offset; raw processing not fully reconstructible from curtain-only ZIP',synchronization='published matched observation rows usable for spatial fixed-path fit; no fully reconstructible sensor lag; CP2 clock only mm:ss, CP1 unzoned; OP Excel serial TIME_UTC; no cross-platform lag claim',route='source-informed manual CP and planned OP curtains; not unknown-source search',repeats='4 same-day source-informed curtains: near approximately80m and far approximately150m; not four independent real datasets',ground_background_wind='paper GS1 1.5m and GS2 2.7m; neither time series in full 10-file archive; ground-only arm unavailable',localization_metric='reference horizontal point error computable for truth-blind fixed-route inference, subject to finite source truth and model identifiability; no autonomous search claim',plume_metric='measured curtain concentration support/centerline and near-far consistency; no whole-volume plume truth',public_code='DMB, CKMB notebooks, GPI known-source flux model; hardcoded private filenames require adapters; original GPI is NOT source-position inverse',license='CC-BY-4.0 Zenodo',decision='REAL_MACKENZIE_GO_FIXED_PATH_DATA_HOLD_ROBUST_WIND_INVERSION',data_root=str(ROOT),raw_archive_bytes=29554312,raw_archive_sha256='4c0bdd1adebe8f794f2ee533761ea9e064c3a59011793651378851544883ff49')
    qual['decision']='MACKENZIE_HOLD_SOURCE_INVERSION_NOT_ROBUST'
    qual['protocol_GO_gate']='MACKENZIE_GO_REAL_POINT_SOURCE_NOT_ACHIEVED'
    (OUT/'QUALIFICATION.json').write_text(json.dumps(qual,ensure_ascii=False,indent=2),encoding='utf8')
    text='''# Mackenzie Channel Seep 2：公开数据资格及条件风反演审计

数据具备资格：四条有已知源参考坐标的真实固定 curtain 路径足以建立点源反演输入与水平误差评分。正式判定MACKENZIE_HOLD_SOURCE_INVERSION_NOT_ROBUST：本轮没有证明“平均风失效、局地风稳定修复”，也未达到协议要求跨架次/平台稳定的MACKENZIE_GO_REAL_POINT_SOURCE门。

## 原始包、场景和采样资格

[官方数据 DOI](https://zenodo.org/records/20019779) 的唯一29,554,312-byte ZIP已完整下载，MD5与发布方一致，SHA256为4c0bdd1adebe8f794f2ee533761ea9e064c3a59011793651378851544883ff49。10个文件全部解压并逐文件记录SHA；原始CSV及notebook未改。

[作者论文](https://amt.copernicus.org/articles/19/3983/2026/)及四个CSV确认2025-08-01的CP1/CP2/OP1/OP2，天然点状逸散源参考位置69.319583N,-135.477520E。CP为手动航线，OP为已编程航线；两者均事先知道源并安排下风curtain，不能用于未知源自主搜索结论。论文近/远下风距约CP87/163m、OP77/149m。坐标旋转后的样本中位距离不一定等于论文航线标称距离。

CP实际CSV2125/2250行，2Hz，CH4单位ppb转ppm；WS_corr采用m/s，WD_corr依据作者notebook和DMB的+19°北向修正。OP实际10306/6373行，约10Hz；不能把100Hz传感器名义率称作公开CSV率。论文两套平台均为二维水平风传感器。CP有VertWind辅助列，不足以把整个包宣传为两套运动修正3D风。

原论文有GS1 1.5m、GS2 2.7m地面风，但完整公开包没有它们的时间序列；不能拿图或UAV均值冒充ground-only输入。ground-only arm明确NOT_RUN_DATA_UNAVAILABLE。

## 作者方法复核与明确偏差

EPSG32608投影、Prep_Curtains两段旋转的等价直接旋转、CH4转换、P(z)=101987−12.26z Pa、T=292.4627K、methane质量密度、背景扣除与GPI镜像高斯核均复核。AST提取作者forward函数与适配函数数值完全一致。固定已知源的GPI拟合使用scipy least_squares代替lmfit及1s数据约简，见AUTHOR_FIXED_SOURCE_GPI_REPRODUCTION.csv；这是可移植的作者方法重跑，不宣称逐位复现其论文表格或所有原始传感器修正。

作者GPI/main.py使用CP背景2.031797、OP背景2.064857ppm；CKMB/DMB与论文OP背景约2.0291ppm，且CKMB/DMB用CH4_dry，GPI读CH4。这里保留GPI输入选择，单独测试论文背景；没有把不同处理链的输出混为同一方法。上游完整lag、raw sonic motion correction并不在4个curtain CSV中。

CP1日期时间未带时区，CP2 DateTime截为mm:ss且跨小时；OP TIME_UTC实际是Excel serial day而非秒，TimeStamp为整数Unix秒并重复。不借这些字段猜跨平台对齐或sensor lag。空间模型采用发布方同一CSV行，不作传播时滞结论。

## 固定路径未知源比较

真源只用于作者固定源通量复现及所有未知源拟合完成后的评分；未知源输入只取接收位置、气体、矢量风、高度。原文件中的source-relative x_prime/y_prime不用于未知源拟合。候选域由观测GPS包络与观测平均风确定，向上风延伸10–400m；等权源网格31×31，沿风13m步长，source height=0。均匀/局地/每架次线性高度风三个arm使用同一气体、源域、非负释放率和扩散网格。

current-local只把接收时刻本地风代入稳态高斯核，不知道传播路径的历史风；height-dependent只拟合本条轨迹的风—高度关系，不是独立三维气象场。两者均不等同于已经恢复了真实source–receptor propagation state。

'''
    for label,table in [('冻结主配置',rows[rows['case'].str.contains('\\+')&(rows.background=='author_code')]),('扩散支持范围敏感性',sensitivity)]:
        text+='\n### '+label+'\n\n|航线|风表征|条件定位误差m|源网格边界|\n|---|---|---:|---|\n'
        for _,r in table.iterrows():text+=f'|{r["case"]}|{r.wind_arm}|{r.conditional_localization_error_m:.2f}|{r.source_on_grid_boundary}|\n'
    text+='''
主配置的CP联合mean误差5.08m，扩大扩散参数支持后变成55.52m且贴源域边界。OP联合mean16.71→44.21m；local56.73m且贴边。背景切换对本网格MAP不改，但扩散支持改变风排序。不能择取最有利配置声称某风表征优越，不能把边界最优点当稳健定位。

单curtain中sigma_y=tau_y*x、sigma_z=tau_z*x；自由source distance与tau可以互相补偿，释放率进一步参与。近远联合强加同Q和扩散参数后可给条件点估计，但两架次稳态一致性的假设并未由数据保证。主配置RSS相对最小值+5%支持域只作可辨识性诊断：不是Bayesian posterior，也不是95%可信区间。CP均风联合支持域northing span约155m，不能把5m点误差误读成5m确定度。

NEAR_FAR_CONSISTENCY.csv报告各风arm单独近远源估计分离，INFERRED_PLUME_CENTERLINES.csv给出均风直线中心线交点，HEIGHT_WIND_PROFILES.csv给出真实高度分箱风。全空间plume truth、持续停滞区、岸线传播滞后和真实未知源搜索均不能由此证明。

## 结论

可以合法评分固定轨迹源参考点误差；当前高斯反演的源距离与扩散可辨识性、时变传播及传感器处理仍限制该评分的解释。缺失地面日志阻断ground-only比较。Mackenzie不构成Svalbard中“local wind修复mean wind”的独立正向复现。本轮保持MACKENZIE_HOLD_SOURCE_INVERSION_NOT_ROBUST，不生成CFD/GADEN。
'''
    (OUT/'REPORT_zh.md').write_text(text,encoding='utf8')
    (OUT/'ANALYSIS_COMPLETED.json').write_text(json.dumps(dict(decision=qual['decision'],ground_arm='NOT_RUN_DATA_UNAVAILABLE',primary_wind_ranking='NOT_ROBUST_TO_DISPERSION_SUPPORT',source_inversion_error='conditional only',posterior='NOT_CLAIMED_RSS_SUPPORT_ONLY',temporal_transport='NOT_RUN_CLOCK_CONTRACT_INCOMPLETE'),indent=2),encoding='utf8')
    for folder in [ROOT/'reports',ROOT/'derived']:
        folder.mkdir(exist_ok=True)
    shutil.copy2(OUT/'REPORT_zh.md',ROOT/'reports/REPORT_zh.md')
    for p in OUT.glob('*.csv'):shutil.copy2(p,ROOT/'derived'/p.name)

if __name__=='__main__':main()
