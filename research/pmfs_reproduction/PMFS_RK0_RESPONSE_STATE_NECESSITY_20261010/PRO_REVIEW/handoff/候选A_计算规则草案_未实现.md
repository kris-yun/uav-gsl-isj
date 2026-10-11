# 响应保持的克隆状态：计算规则草案

状态：未实现、未训练、未验证适配；不能用本文件替代下一关的必要性检验。启发来自Sun等2025 Nature的正交化状态机/CSCG，但以下气体模型及约束是本项目需要独立设计和验证的迁移，不是原论文成果。

## 输入与内部状态

输入：气体物理几何G_g、导航/安全几何G_a（两者分开），风条件，已知释放高度和统一候选源集合，实际受体位姿/时间和气体记录，独立物理reference。

内部状态：每个粗XY格最多K个物理状态类，以及这些类上的随机羽团数量/质量分布N_t；不是把无人机的位置当气体位置，也不是只有一个移动气团。

类内可以共享一个粗标签，但不同类应对应不同的未来受体响应或合法转移。未知高度、羽团尺度和驻留历史只是候选解释，不能预先全部硬加入。

## 离线规则

1. 从每XY一个类开始。先验证粒子数量、核加和、正确几何和正确传感器读出。
2. 仅在reference上计算同粗类的受体响应差异。使用事先固定的受体集合/预测时距，不使用真/错源标签、B4事后评分带或最终排名。
3. 只分裂“同粗类但具有不同预测响应”的状态；分裂数有硬上限。比较相同数量的固定物理分箱，避免把多参数收益当脑启发收益。
4. 拟合或构造物理允许的转移。若有合格身份轨迹，受约束计数/EM可更新：

   T_ij = (E[n_ij] + alpha_ij) / sum_{k in legal(i)}(E[n_ik]+alpha_ik).

   非法边的alpha和T严格为0。需要出口/损失吸收状态以保持完整概率。没有合格轨迹，不得把快照行号当ID。
5. 状态间响应核由物理观测模型给出或用独立标定估计。源位置只能改变释放注入，不能为每个源自由学习一个“万能纠偏核”。
6. 冻结分裂、转移与响应参数。以未用于拟合的实现确认预测收益。

## 在线规则（人口/集合滤波骨架）

```
for candidate s in frozen_source_grid:
    initialize an ensemble of population states N[s] from common prior

for each actual observation block t:
    for s:
        propagate N[s] using legal gas transitions + injection at candidate s
        evaluate the actual receiver response for each ensemble member
        apply actual aggregation/threshold/sensor observation likelihood
        update joint weights of source s and hidden population state
    normalize the joint distribution (not a new multiply of old cumulative maps)
    output pi_t[s] = sum_hidden joint_weight[s, hidden]
    forecast receptor/field observables by propagating the same joint ensemble
```

该骨架中的滤波本身不是新发明。原创价值只能来自可解释的状态构造和可验证的响应保持性质。

## 不可省略的随机性

一般情况下，P(C>tau)不等于1[E(C)>tau]。保留均值人口向量、用线性核输出均值浓度，不足以得到检出概率。需要数量分布、波动模型或集合，并对其有限样本误差检验。

## 可证明的条件与不能冒领的结论

对完整Markov状态X，若压缩R使转移核在类内相同，且每个受体的条件观测分布只依赖RX，且初态/源注入相容，则粗模型保留相应观测序列分布。这个结论来自经典聚合，不是2025才有。

若每候选每一步的条件预测log误差不超过eps_t，同先验下任意两个候选的后验log-odds误差不超过2 sum eps_t。它由三角不等式得到，不能声称为新定理；难点是如何在有限reference上得到可信eps，而不是写出不等式。

本方法不能承诺恢复观测中不存在的信息；不能借所有候选自由残差把每个源都拟合得好；不能把一个2源4留出成功说成跨数据集稳定提升。

## 终止标准

若统一核已解决问题；若固定分箱与克隆效果相同；若收益只是完整三维oracle额外信息；若状态更多却仅改善场MSE；若对独立源/风况不能保持，则停止作为主创新。保留物理支撑与响应修正为基线，不伪装成成功的新算法。
