# 唯一候选：物理候选条件化双向循环门控

## 母理论与改造边界

母理论为上下行递归注意与特征绑定，具体采用2026 BRG的有界乘性门控思想。原论文的高层任务线索来自视觉任务。本项目改成 **对所有候选一视同仁的物理预测线索**，不是喂真实 source 标签作 top-down prompt。

二次创新候选是“候选假设驱动的证据绑定”：同一测量对于不同候选可以有不同解释；每个候选的预测与过去相容状态调制当前证据，同时全部候选共用参数。这是一个可实现、待证的归纳偏置，不是新的可辨识性定理。条件循环模型、attention、GRU、softmax本身均不认领创新。

## 数学与代码一一对应

观测特征 o_t 包含浓度的两个单调幅度通道和hit状态。候选线索 v_{s,t} 包括当前位置下的 p_s、rawu_s 和相对位置。没有 source ID embedding、环境标签、未来观测、真实 source cue。

- a_t = tanh(LN(W_o phi(y_t)))
- v_{s,t} = tanh(LN(W_v psi(p_s,rawu_s,x_t-s)))
- h^(0)_{s,t} = h_{s,t-1}
- g^(k)_{s,t} = 1 + 0.5 tanh(W_g [h^(k)_{s,t},v_{s,t}])
- z^(k) = tanh(LN(W_f [a_t*g^(k), v, a_t-v, a_t*v]))
- h^(k+1) = GRUCell(z^(k),h^(k))，k=0,1,2
- ell_{s,t} = w^T h^(3)_{s,t}
- q_t(s) = softmax_s(ell_{s,t} + log pi_s)

这里“双向”不是未来到过去的时序模型：只有同一观测上的bottom-up/top-down内部迭代。三次内部迭代不是三条独立证据。h已概括过去，因此 **q_t替换旧概率图，不乘回q_{t-1}**。

源先验只加一次。训练样本各source等权，使用logits级cross entropy，所有前缀参与训练；不对已经softmax的概率再次作CrossEntropy。LayerNorm无运行期BatchNorm累积统计。所有正常零值保留零，不加会破坏自由gain等价关系的per-entry floor。

rawu仍为计数代理，不是ppm。因此分别无量纲化，不能直接把c-rawu当物理残差。本实现使用log1p(c/c0)、c/(c+c0)，保留幅度信息而不是按每条path归一化。

## 观测条件

训练默认只有固定0.2m高度、0.2m方形footprint、10个顺序快照。第一版不使用delta-t作学习特征，只利用顺序；时间戳用于防重与审计。不据此宣称学到了连续时间动态、first passage、真实burst。超过10次观测会记录history_extrapolated；可用实际OPEN日志训练更长history，不伪造高频独立样本。

风信息通过预先生成且有版本号的PMFS候选预测进入。本版没有在线识别全场风。银行在一个episode内固定，变更必须终止/重建该episode推断合同，不能悄悄换bank后续乘概率。未来若更新bank，应重放已观察前缀而非增加新证据。

## 闭环接口为何必须改两处

native planner实际读取 source分布加权的hit-map方差。只替换画出来的sourceProbability，保留旧variance缓存，不一定会改变动作。

本包返回：

- full source map: q_s放回对应原格，质量守恒；
- mu_i = sum_s q_s p_{s,i}；
- variance_i = sum_s q_s p_{s,i}^2 - mu_i^2。

这是原planner已有的“候选预测分歧”量，只更换其belief权重，不引入另一套EIG或新planner。公开humble版本的calculateMutualInformationGas是另一个debug计算，实际informationValue用varianceOfHitProb。若用户fork已改为真正使用MI，必须接上相应belief缓存，不能机械套本补丁。

## 这条路线必须经受的检验（在同一闭环比较内完成）

1. 相同输入、相同事件预算下胜原生PMFS，是实际效用要求。
2. 同模型银行的候选GRU是必要强对照；已有B2排序可作离线辅助，不把未校准SSE伪装成后验；不能把更丰富forward预算的收益全给网络。
3. 移除feedback的同结构版本检验top-down是否必要。若GRU/ungated解释全部改善，不能认领BRG二次创新。
4. 最终输出必须改变合法的导航决策链，并改善最终源误差/成功，而不只是offline NLL或rank。
5. 地图、PMFS预测、单一未知泄漏的观测合法；目标多源GADEN测试bank不可作在线context。

没有提供“新架构必然改善”的保证。BRG论文也并未以击败所有AI架构为目标。研究假设是：物理候选反馈约束使有限数据的局部证据整合更有效；这需由闭环和同输入消融证明。
