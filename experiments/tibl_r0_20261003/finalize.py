"""Finalize frozen gates; do not execute source stages after geometry failure."""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evidence/tibl_r0_20261003'


def main():
    cfg=json.loads((OUT/'R0_TIBL_CONFIG.json').read_text())
    stages=json.loads((OUT/'STAGE_GATE_RESULTS.json').read_text())
    rows=[]
    for c in stages['conditions']:
        for i,case in enumerate(['Z_MEAN','K_MEAN']):
            values=c['geometry_JSDs'][i*6:(i+1)*6]
            rows.append(dict(closure=c['closure'],flux=c['flux'],control=case,
                             minimum_JSD=min(values),mean_JSD=float(np.mean(values)),maximum_JSD=max(values),
                             gate_minimum=cfg['gates']['geometry_JSD_min'],
                             numerical_max_JSD=stages['numerical_max_JSD'],
                             all_source_path_geometry_pass=bool(min(values)>=cfg['gates']['geometry_JSD_min'] and
                                    min(values)>cfg['gates']['effect_over_numerical_error_min']*stages['numerical_max_JSD'])))
    pd.DataFrame(rows).to_csv(OUT/'GEOMETRY_GATE_BY_CONTROL.csv',index=False)
    numeric=all(c['numerical_max_relative_L2']<=cfg['gates']['numerical_profile_relL2_max'] for c in stages['conditions'])
    geometry=all(r['all_source_path_geometry_pass'] for r in rows)
    assert numeric and not geometry and stages['localization_rows']==0
    decision=dict(decision='R0_TIBL_STOP_NOT_LOCALIZATION_RELEVANT',
                  reason='FROZEN_GEOMETRY_GATE_FAILED_SOURCE_MAPPING_NOT_EXECUTED',
                  numerical_gate_pass=numeric,geometry_gate_pass=geometry,
                  geometry_threshold_origin='operational engineering choice frozen before scoring, not a literature threshold or user-specified number',
                  partial_geometry_changes_above_numerical_error=True,
                  all_geometry_abs_threshold_pass=False,
                  source_mapping_status='NOT_EXECUTED_GEOMETRY_GATE',
                  matched_detection_status='NOT_EXECUTED_GEOMETRY_GATE',
                  continuous_localization_status='NOT_EXECUTED_GEOMETRY_GATE',
                  independent_height_laws_tested=1,local_K_shapes_tested=2,
                  scientific_scope='prescribed local gradient-diffusion family; not all physical TIBL mechanisms',
                  three_dimensional_execution='NOT_EXECUTED',OpenFOAM_installed=False,GADEN_generated=False,
                  invalid_initial_run='quarantined; downstream metrics excluded; same config replayed after safe JSD correction',
                  geometry_comparisons=rows)
    (OUT/'R0_TIBL_DECISION.json').write_text(json.dumps(decision,indent=2,allow_nan=False),encoding='utf-8')
    # Explicit schema-only files mean not executed, never a fabricated zero result.
    for name,columns in [
        ('MATCHED_DETECTION.csv',['closure','flux','path','source_x','common_hits','same_positions','same_count','expected_SNR_ratio_max','selection']),
        ('SOURCE_PROFILE_LIKELIHOOD.csv',['closure','flux','path','source_x','seed','mode','inverse','candidate_x','profile_chi2','Q_hat','background_hat']),
        ('MODEL_MISMATCH_LOCALIZATION.csv',['closure','flux','path','source_x','seed','mode','inverse','xhat','Qhat','background_hat','bias','error','interval_low','interval_high','coverage'])]:
        pd.DataFrame(columns=columns).to_csv(OUT/name,index=False)
    shutil.copy2(ROOT/'experiments/tibl_r0_20261003/FROZEN_PARAMETER_SOURCES.md',OUT/'FROZEN_PARAMETER_SOURCES.md')
    n=pd.read_csv(OUT/'NUMERICAL_CONVERGENCE.csv');budget=pd.read_csv(OUT/'MATCHED_MIXING_CONTROLS.csv')
    groups=budget.groupby(['closure','flux']).integral_Kz
    match=float(((groups.max()-groups.min())/groups.mean()).max())
    assert match<1e-12
    text='''# R0-TIBL 受限证伪结果

正式判定：**R0_TIBL_STOP_NOT_LOCALIZATION_RELEVANT**。

这是按本轮冻结几何 gate 停止，**没有得到“源坐标不受 TIBL 影响”的结论**。源映射、匹配检测和连续反演均因前置门失败而未执行。三个相关 CSV 只有字段表头，不能把空文件读成零误差或零效应。旧 R1/R1A/R1B/R3 不变，不进三维、不装 OpenFOAM、不生成 GADEN。

## 实际执行范围

域为 0–1000 m × 0–150 m，u=2 m/s、w=0、Kx=.5 m²/s，源高度 3 m，三个连续 source-x truth 为 73.4/161.7/287.3 m。两条固定受体路径、三个匹配场 TIBL_X/Z_MEAN/K_MEAN、热通量 .06/.04 K m/s。

第一局地闭合是用户给定简化 K-profile，第二是 Siebesma et al. 2007 eq.20 的 Holtslag ED 形式在自由对流极限下的局地部分。它们有不同垂向形状，但共享同一个 EPA 高度律；没有伪造第二种 h(x) 模型，也没有把只改强度的压力测试称为第二完整物理闭合。没有实现非局地质量通量或夹卷。

EPA 高度律和 Allouche 热通量已核实原文。参考温度 300 K、源宽度、噪声和路径是冻结的研究设置，并非真实观测反演值。所有来源、公式、假设和操作化阈值见 FROZEN_PARAMETER_SOURCES.md。

## 数值验证

采用保守有限体积二维平流—扩散。比较 10×2.5、5×1.25、2.5×.625 m 网格；用 20/10 s 隐式时间步推进到同样的 1500 s，独立核对稳态正演。完成非负性、质量平衡、更高顶边界、更远出流边界、吸收顶边界和单独的吸收地面压力测试。

'''
    text+=f"- 细网格受体剖面最大相对 L2 差：{n[n.check=='fine'].relative_L2.max():.6%}。\n"
    text+=f"- 粗网格最大相对差：{n[n.check=='coarse'].relative_L2.max():.6%}。\n"
    text+=f"- 固定时长/时间步最大相对差：{n[n.check.str.startswith('dt_')].relative_L2.max():.3e}。\n"
    text+=f"- 质量平衡最大相对误差：{n[n.check=='steady_mass_balance'].relative_L2.max():.3e}。\n"
    text+=f"- 三个场全域 Kz 积分预算的最大相对不一致：{match:.3e}。\n"
    text+=f"- 最大数值 JSD 包络：{stages['numerical_max_JSD']:.6g}。\n"
    text+='''
吸收地面明显改变浓度，是物理边界敏感性而非舍入误差，不应隐去。主模型是无沉降被动标量；本轮不借主模型结果推断真实甲烷地表交换条件。

## 几何门结果

门槛在求解前写入 JSON：所有预设源/路径相对两个匹配对照的 JSD>=.01，且大于五倍数值包络。这一绝对门槛是本轮实现时选择的工程判据，**不是用户原文指定值或文献给出的物理临界值**。它要求所有预设源和路径通过，严格于仅证明某处存在几何变化；因此不能把失败推广成真实 TIBL 没有作用。

| 局地闭合 | 热通量 | Z_MEAN 最小 JSD | K_MEAN 最小 JSD |
|---|---:|---:|---:|
'''
    for closure in cfg['closures']:
        for flux in cfg['heat_fluxes']:
            a=[r for r in rows if r['closure']==closure and r['flux']==flux]
            text+=f"| {closure} | {flux} | {a[0]['minimum_JSD']:.6f} | {a[1]['minimum_JSD']:.6f} |\n"
    text+='''
有些几何差异明显大于数值误差；不是“两个场完全一样”。但两种闭合、两档热通量的预设组合都未全部达到 .01 绝对门，特别是 Z_MEAN 这一更严格的匹配垂向结构对照。按冻结顺序不继续源评分，不事后删除弱源/路径，也不调门槛。

## 首轮实现问题与重跑

首轮 JSD 在两边均为零的概率项上遇到 0/0，NaN 未被比较语句拦住，导致不应执行的下游评分。发现后将首轮归为无效运行，单独归档。修正零质量项的计算、增加有限值检查和禁止 JSON NaN；冻结参数与门槛完全不变，完整确定性重跑。首轮任何定位误差、bias、覆盖率均不进入正式报告或正式决定。QA_INITIAL_RUN_REJECTED.json 保存归档路径及哈希。

## 可成立的结论与不能成立的结论

可以成立：提出的匹配闭合机制试验可实现；局地扩散率的岸距发展产生可测的合成剖面差异，但本轮没有通过预设的全组合几何门。

不能成立：真实湖岸 TIBL 必然导致源定位失败；TIBL 没有定位意义；二维已恢复完整水平源坐标；两种完整热力模型或两种独立高度律已经交叉验证。严格局地 K-profile 在层顶以外设零混合，还遗漏真实稳定层湍流/夹卷，任何停止都局限于本试验合同。

本轮正式工作已结束。后续若改变阈值、观测路径、闭合或源配置，必须作为新的协议，明确披露已经看过本轮结果，不能重标本轮 PASS。
'''
    (OUT/'REPORT_R0_TIBL_zh.md').write_text(text,encoding='utf-8')
    print(json.dumps({'decision':decision['decision'],'mixing_budget_relative_error':match,'numerical_max_JSD':stages['numerical_max_JSD']}))


if __name__=='__main__':main()
