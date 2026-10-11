"""Final descriptive delivery from frozen results. No fit or prediction calls."""
from common_b import *
import csv, shutil

def rows(p):
    with Path(p).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def table(rr, fields):
    return '\n'.join(['| '+' | '.join(fields)+' |', '| '+' | '.join(['---']*len(fields))+' |'] +
                     ['| '+' | '.join(str(r[k]) for k in fields)+' |' for r in rr])

def main():
    a=rows(CORE/'reference_transfer_error_attribution.csv')
    bad=[r for r in a if r['M']=='2' and r['method']=='L' and
         r['reference_role']=='extra_reference' and r['F_zero_model_positive']=='True']
    assert len(bad)==11
    for r in bad:
        assert float(r['F_ppm'])==0 and float(r['physical_F_fallback_ppm'])==0
        assert abs(float(r['physical_conditional_prior_transfer_ppm']))<1e-12
        assert abs(float(r['known_decoder_ppm_from_zero_training_prior_states'])-float(r['frozen_prediction_ppm']))<1e-12
        assert abs(float(r['fit_coefficient_adjustment_ppm'])-float(r['frozen_prediction_ppm']))<1e-12
    assert sum(int(r['cutoff_eligible_particles'])==0 for r in bad)==5
    assert all(int(r['cutoff_eligible_particles'])==int(r['cutoff_eligible_LOS_blocked']) for r in bad)
    compact=[dict(job=r['job_id'],block=r['block'],pose=r['pose'],F_ppm=r['F_ppm'],L_ppm=r['frozen_prediction_ppm'],
                  fit_added_ppm=r['fit_coefficient_adjustment_ppm'],eligible=r['cutoff_eligible_particles'],
                  LOS_blocked=r['cutoff_eligible_LOS_blocked'],unknown=r['unknown_particles']) for r in bad]
    appendix='''# 响应读出跨实现失效组成因素：已冻结数据的算术定位

这次不仅保留FAIL/HOLD标签，也找到了代码与数值相互对应的具体组成因素：**在11个额外参考查询中，原生物理读出严格为零，L仍预测超过0.1ppm；全部正值来自训练拟合对零物理先验状态赋予的正系数。** 独立脚本从原始快照、几何、phi和模型数组重建3600个查询及全部分项，不导入生产模型模块。

该结论针对M2的冻结L原型及预先登记的额外参考实现，不是原始PMFS的科学缺陷，也不是对所有20个阈值翻转的统一解释。额外参考对未进入M2原B源判别库，因此不能用此诊断解释主门NLL略微退化的全部原因。

## 1. 先区分训练内保真和实现间迁移

| 固定模型与数据 | U翻转/300 | S翻转/300 | L翻转/300 | L的ppm均方误差 |
| --- | --- | --- | --- | --- |
| M2，原2参考，参与拟合 | 1 | 0 | 0 | 0.000001089918 |
| M2，额外2参考，未参与拟合 | 26 | 30 | 20 | 0.174499320525 |

两种数据均是既定参考读取诊断，不是新试验或新增源推断。M4将两对参考都用于拟合后，L在600个查询上不翻转，平均MSE为0.000004630032；这是训练集合扩展后的插值成绩，不能作为新的独立读出泛化证据。额外实现的L未知状态比例均值仅0.283%，高状态覆盖不保证正确解码。

## 2. 严格为零的物理响应被谁改成了正值

原生单粒子响应必须同时满足距离小于3σ和占据地图视线无遮挡。以下5个查询没有任何距离合格粒子；另6个虽有合格粒子，但全部被遮挡。原生F=0不是浮点下溢或阈值附近模糊结果。11个查询的物理条件先验传递项和回退项都为0，正预测完全来自已知状态的拟合系数。

'''+table(compact,['job','block','pose','F_ppm','L_ppm','fit_added_ppm','eligible','LOS_blocked','unknown'])+'''

保存每个查询的逐项分解：

`L−F = Σ_known n(h−prior) + [Σ_known n·prior−Σ_known φ] + fallback_rounding + native_sum_rounding`。

这11个查询中第一项等于L本身。所有产生正值的状态，在该受体的训练物理先验都是0。它们无须依赖未知状态回退，便可生成约0.10–0.50ppm的伪正响应。

## 3. 对应代码与机制边界

[common_fit](source/rk2b_models.py)第55–80行使用非负ridge，先验进入正则项，未约束`prior=0 ⇒ h=0`。每个受体仅30条拟合行，同时存在大量状态系数；非负系数满足优化和KKT不保证每个单粒子状态的物理零支持不变。

[compress](source/rk2b_models.py)第193–210行，已知状态直接计算`counts @ h[:, pose]`；距离和视线的原生物理检查只对未知状态回退执行。因此，拟合得到的正系数在新的粒子计数组合中可以产生本应为零的响应。这里的归因是**拟合系数创造了物理零响应之外的支持**；本组11例的条件先验本身已经为零，不能误写成“先验没有保留物理零”。

本轮没有重新拟合受约束模型、追加源推断或将原先验替换方案记作性能收益。仍需区分训练目标的欠约束、状态压缩和新实现计数组合变化；当前证据只足以确认这一具体算术失效组成因素。

## 4. 为什么不能直接说“把h换成prior就修好了”

M2额外参考L误差的均方分解为：拟合调整平方0.0620636112，物理条件先验传递平方0.2320904828，两者交叉项−0.1196548046，总误差约0.1744993205。训练原参考的两项平方均约0.108，而交叉项约−0.21558，几乎抵消。

因此，训练内极小总误差可能包含分项抵消；去掉拟合调整并不保证整体误差下降。该分解也不是将总误差按百分比独立分摊的因果结论。完整3600行含浮点串行求和尾项，独立核验误差恒等式。

## 5. 与本轮研究决策的关系

原B（正式6份、M2、H0）仍FAIL：L与S/F二值预测完全相同，六份均Top1正确，但未实现对U/S的10%NLL增益。跨实现伪正读出是另一个应保留的反例，不能用它事后更换主端点。

建议PRO优先判断：响应保真方法的目标是否应直接约束物理零支持及条件响应，而非只拟合聚合浓度；该约束是否有超越普通物理特征回归的贡献；在有限参考噪声与当前已饱和二值判别条件下，是否还有值得推进的独立源定位增量。本轮不自动展开新模型。

复核入口：`source/verify_raw_support_b.py CORE目录 RAW目录`。证据：`reference_transfer_error_attribution.csv`、`reference_transfer_summary.csv`、`INDEPENDENT_TRANSFER_ATTRIBUTION_QA.stdout`。
'''
    (CORE/'READOUT_TRANSFER_FAILURE_COMPONENT_zh.md').write_text(appendix,encoding='utf-8')
    executive='''本轮24份预登记物理实现和全部有效分支已完成，结果没有停在HOLD。

原B主门：FAIL_ORIGINAL_B_ENDPOINT。正式6份、M2、H0中，L相对U的NLL增益为−0.6935%，相对S为0，未达到分别≥10%的要求。F/U/S/L均6/6 Top1正确；L/S/F的本档二值预测相同。H1和M4全部保留，不能替换原门。

另找到一个具体失效组成因素：M2的L在额外参考对有20/300个阈值事件翻转，其中11个是原生F严格为0却预测>0.1ppm。5例没有3σ内粒子，6例合格粒子全部被视线遮挡；全部正值由零物理先验状态的拟合正系数产生，物理先验传递和回退贡献均为0。独立原字节/几何/模型重建通过。这个结论属于冻结读出原型，不能指认为原始PMFS缺陷；也不能解释主门小幅退化，因为该额外参考对未进入M2主源判别。

先读：READOUT_TRANSFER_FAILURE_COMPONENT_zh.md，再读RK2B_CONTINUOUS_RESEARCH_REPORT_zh.md。本包保存全部24份记录、两档/两头、逐实现成绩、前缀与未来预测、参考更换、状态覆盖、完整成本和隔离证据，没有只保留有利分支。

给PRO优先判断三个问题：
1. 训练内聚合浓度保真通过分项抵消取得，而新实现出现明确物理零支持破坏；应否改变方法约束目标，还是将L保留为辅助对照并结束当前主创新路线？
2. L已有物理条件先验，却由拟合创造伪正响应。物理支持约束能否形成必要、可被否证且超越常规回归的贡献？不能只增加树深度。
3. 二值F/S/L已无本样本内增量，有限参考F也非Bayes最优；H1与M4没有翻案。参考噪声、阈值化信息损失、当前采样设计中，哪一项值得下一轮单独验证？

物理数据是可追溯受控仿真，静态风10，三预置候选、六正式实现；不是完整PMFS导航或跨场景统计复现。全部原始粒子仍保全。现在停止，不自动追加seed、源、导航或新模型。
'''
    (CORE/'EXECUTIVE_DECISION_zh.md').write_text(executive,encoding='utf-8')
    (CORE/'SEND_TO_PRO_zh.txt').write_text(executive,encoding='utf-8')
    report=CORE/'RK2B_CONTINUOUS_RESEARCH_REPORT_zh.md'
    marker='## 7. 补充：读出跨实现失效的算术组成因素'
    t=report.read_text(encoding='utf-8')
    if marker not in t:
        report.write_text(t+'\n'+marker+'\n\n完整证据见[READOUT_TRANSFER_FAILURE_COMPONENT_zh.md](READOUT_TRANSFER_FAILURE_COMPONENT_zh.md)。M2额外参考L出现20/300个事件翻转，其中11个F严格为0但L超过阈值，正值全部来自零训练物理先验状态的拟合正系数。这是独立重建确认的原型读出失效组成因素，不用于替换原B判决或证明原始PMFS缺陷。参考数量变更的H0置信变化还包括Jeffreys先验稀释，分项见registered_H0_information_and_smoothing.csv。\n',encoding='utf-8')
    readme='''# RK2-B/B+审核包读取说明

这是一次已结束的24份固定物理实现连续验证。原B主门FAIL，全部登记分支均完成。详细机制组成因素已有算术证据；原始PMFS物理缺陷尚未由本轮证明。

推荐阅读顺序：

1. `SEND_TO_PRO_zh.txt`：可直接发送PRO的说明和三个决策问题。
2. `READOUT_TRANSFER_FAILURE_COMPONENT_zh.md`：11例物理零支持破坏的代码与分项证据。
3. `RK2B_CONTINUOUS_RESEARCH_REPORT_zh.md`：全部分支、物理合同、成本及反例。
4. `ORIGINAL_B_GATE_FINAL.json`、`SUMMARY_METRICS.csv`、`reference_transfer_error_attribution.csv`：精确数值。
5. `authorization`与`PREPHYSICAL_SOURCE_SHA256.json`：运行前合同与冻结源；`technical_repairs`保留技术错误及修复。

两个ZIP解压到不同目录。需要Python 3、NumPy、SciPy（原始环境版本写在PREFLIGHT.json）；独立复核不启动ROS、GADEN，不生成物理数据或拟合模型：

```
python CORE/source/verify_b.py CORE
python CORE/source/verify_raw_support_b.py CORE RAW
```

CORE含全部预测、标量观测、模型、原始参数与时间索引。RAW含1200份主查询原字节快照、600份参考phi缓存、24份原生查询/时间/RNG日志、3D占据和风场。完整43272帧银行留在FULL_BANK_PRESERVATION.json指定目录；本任务不删除未装包数据。

每包MANIFEST_SHA256.json纳入除自身之外全部文件，CSV复算采用数值容差；ZIP另有SHA256与解压验证结果。已有父RK2-A、RK1和历史STOP/HOLD不被覆盖。

本包生产脚本为环境绑定的完整运行血统，不是鼓励重复执行科学试验的一键入口。已冻结生产模块的SHA保持不变；最终报告/打包与独立复核脚本在运行后完善，未更改模型或端点。受控仿真的物理生成资格与主门统计成绩分别判定。
'''
    (CORE/'README_zh.md').write_text(readme,encoding='utf-8')
    (CORE/'.gitattributes').write_text('* -text\n',encoding='utf-8')
    logs=['FINAL_PREPHYSICAL_FREEZE_REPAIRED.stderr','FINAL_PREPHYSICAL_FREEZE_REPAIRED.stdout',
          'FINAL_PREPHYSICAL_FREEZE_REPAIRED2.stderr','FINAL_PREPHYSICAL_FREEZE_REPAIRED2.stdout',
          'FINAL_PREPHYSICAL_FREEZE.stderr','FINAL_PREPHYSICAL_FREEZE.stdout','FREEZE_LAYOUT_DIAGNOSIS.stdout']
    for n in logs:
        if (WORK/n).exists() and not (CORE/'technical_repairs'/n).exists():
            shutil.copyfile(WORK/n,CORE/'technical_repairs'/n)
    shutil.copyfile(Path(__file__),CORE/'source'/Path(__file__).name)
    frozen=load(CORE/'PREPHYSICAL_SOURCE_SHA256.json')
    assert all(sha(WORK/n)==s and sha(CORE/'source'/n)==s for n,s in frozen.items())
    dump(CORE/'FINAL_FROZEN_SOURCE_AUDIT.json',dict(status='PASS',prephysical_frozen_files=len(frozen),all_work_and_core_bytes_unchanged=True,
        final_description_does_not_change_models_or_predictions=True))
    print(json.dumps(dict(status='FINAL_DESCRIPTIVE_MATERIAL_COMPLETE',zero_response_cases=len(bad))))

if __name__=='__main__':main()
