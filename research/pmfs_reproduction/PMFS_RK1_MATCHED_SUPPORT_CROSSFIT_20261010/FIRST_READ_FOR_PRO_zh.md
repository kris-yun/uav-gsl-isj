# 给PRO：本次响应核/状态必要性实验，先读此页

**已经完成一次新的U/S/F必要性门，不是只复述M2/M3。**同上限非物理R对照也按预注册规则执行。没有新气体、CFD、候选输运、ROS、VM、导航或训练；计算约60.35秒、峰值72.18MiB。八份旧银行仍是探索数据，当前不存在新独立任务。

## 核心发现与反例

1. 同3D参考同原生评分：中心占用margin−0.258862，实际PID读出+4.008207；共同blur后仍−0.508909对+3.303355。独立再算通过，读出定义本身改变源排序。M3气体/导航支撑干预保持有效，ALLXY旧分母clamp弱翻转的解释已纠正。
2. 共享核U已经保持F的O0和四份旧留出二源决定；S仍4/4，无新增分类成绩。S在四份任务同时增强log/Brier判别margin，固定非物理四组R则与U源事件相同。S只是普通高度×尺度固定四类，未实现CSCG。
3. 正确源绝对proper预测并非四份都改善：C7两份不变，margin收益来自排斥错误K2；K2两份正确源预测确有改善。源评分与受体压缩是不同评价对象。
4. pooled核总体均值守恒达约1e−13ppm，却可掩盖约±1.5ppm的源条件偏差；S部分恢复但不充分。这定位到条件组成混合，而没有唯一分离高度、尺度、格内位置或LOS。
5. S完整点仅62/200，U144/200。共同支持MSE只在C7两份降低，K2_2升高、K2_3无完整点。全200事件错误界S16–33、U27–34重叠；K2_2局部稳健改善，C7_3局部稳健退化。未知h不填零、未用留出真值补核。

因此保留`S_ADDITIONAL_DIAGNOSTIC_VALUE_WITH_KERNEL_COVERAGE_LIMIT`，同时明确：U已足够当前源决定，CSCG必要性、全量响应保真、新定位收益与唯一物理根因都未建立。请不要把数值PASS与主创新有效混为一项，也不必回到笼统“无证据HOLD”。

## 建议审核顺序

- `RK0_NEW/RK0_RESPONSE_STATE_NECESSITY_REPORT_zh.md`：完整新实验、数学定义、源码路径、效应、反例及下一门。
- `RK0_NEW/independent_scientific_review/RK0_SCIENTIFIC_DECISION_REVIEW_zh.md`：独立评分与科学边界审查，拆开正确源/错误源loss。
- `RK0_NEW/independent_rk0_complete_audit/RK0_INDEPENDENT_REVIEW_zh.md`：独立全链核、粒子分母、缺失、native锚点与评分复算。
- `RK0_NEW/RK0_PAIRED_RESPONSE_DIAGNOSTIC.png`及caption：实际配对数据图。
- `PRO_REVIEW/PRO_INDEPENDENT_RECOMPUTATION_zh.md`：本地独立复算您新增的同bank同scorer与分母诊断；原PRO ZIP和脚本全部保留。
- `RK0_NEW/NEXT_RESPONSE_PRESERVATION_GATE_zh.md`：先覆盖/正确普通基线/新任务，后讨论clone的可否证路线。

`PARENT_M2M3_FROZEN/`是旧联合审核包完整逐字副本；包含392个选择快照、原始查询/时间/哈希/源码，不是八份完整1803帧大银行；完整银行仍留在原环境，但本审核不依赖VM或联网。原始判决不改，补充解释单独存放。

## 本地只读验证

需要Python3与NumPy；PRO读出可选深核另需OpenCV。版本差异是元数据，整数/count/SHA严格一致，科学量使用保留的窄容差；旧OpenCV字面版本和浮点CSV字节检查不作为本包跨平台科学验收标准。

在包根运行（输出必须是包外新JSON文件）：

```text
python -B verify_review_bundle.py --package . --deep --out ../rk0_fresh_verification.json
```

主验证器不调用producer、native physics或ROS，不改包内文件。先验全包与明确scope的nested hashes，然后按缓存和原快照重算kernel、预测、缺失、全部源任务。带包外新--out时另在包外scratch重算PRO整数/scalar读出及分母对照；所有派生表只写包外。详见delivery_verifier_qa/REVIEW_BUNDLE_VERIFIER_REVIEW_zh.md和实际JSON。旧父验证器仍保留，其历史运行日志也保留。原始原生锚点204项精确一致，不以环境字符串替代数值锚点。

## 请本次集中决策

①S的有限响应组成收益是否足以进入一个有限原型，还是先补参考覆盖？②如何让普通共享响应在新状态上可用，又不借源标签/留出真值补核？③下一新任务怎样要求候选超过正确常规响应和固定分箱？

本轮未批准或执行24份新realization，未增加分箱/seed，未训练clone。所有原R7/D0/D1/E3/B4/STOP判决保留。本包足够独立复算本轮数值，不需要再让我重新整理旧证据。
