# V46 三轮代码与理论接口交叉审查记录

审查人员说明：本记录来自实际 AI 任务分工与交叉反馈，不代表人类专家评审或期刊通过。第一轮只读记录见 `R1_CODE_CHAIN_AUDIT.md`；以下是实际实施及其后的独立复核。

## R1：保留正确内核，定位真实范围缺口

V45A `m1_decoders.py` 的 T/R、固定 mask 前置、非饱和历史与阴性控制正确。该文件原样保留，字节一致。旧 `propose` 明确只是候选接口，未实现候选全链、安全、后验与原生执行；因此新增闭环实现是补齐范围，不是“推翻原来的 M1 等变证明”。ReLU 控制编码不进入 raw Fisher 的求导对象。

## R2：实施并逐项绑定计算关系

新增 `core.py`：物理 ID 带标定和历史的规范存储；mask 改变重启窗口；T/R 进入共有 63 候选；统一限速与连续段安全先于昂贵预测；固定 K 子集和语义决胜；四资格独立三值状态；原始 sample/block 双账本；真实有限 bank Gaussian 后验与 XY 边缘；实际 Green/ZOH 新观测和可中断轨迹。

这一后端是指定的离散传感/输运模型。源高和源强作为 bank 支持，风/κ/释放时刻/传感参数已知；它没有实现任意未知传播或任意隐路径模型。其 raw 加性高斯似然不冒充附录对数噪声 Fisher 子模型。默认连续域确认关闭。

## R3：独立挑错、修复与回归

| ID | 发现方 | 实质问题 | 实际修复 | 证据 |
|---|---|---|---|---|
| R3-C01 | root 独立代码复核 | 普通风向/梯度基线未共享失格控制 mask，会让 M1 排脏值而基线吃脏值 | 两基线使用同一 mask/calibration；梯度秩不足显式回退合格逆风 | 失格 raw/wind 改到 1e100，两个基线 anchor 输出差均0 |
| R3-C02 | theory 独立代码复核 | 新确认逻辑最初只看最后帧 PASS，可能追认历史 UNKNOWN | 要求全部已计证历史 time/model 均PASS、无pending raw、固定模型；旧资格未修复不重新确认 | UNKNOWN→PASS 不确认；PASS→UNKNOWN→PASS 仍REVOKED，12帧raw保留 |
| R3-C03 | code/root 范围复核 | 若更换模型而继续相乘旧后验会混计证 | 似然参数签名检查；变更必须fresh posterior+raw replay | 变更κ后决策/更新均拒绝，新raw先归档，旧ledger不变 |
| R3-C04 | code 自审 | 普通基线不需要T/R，却可能被收取其运算成本 | 普通提案只计算其实际所需量；M1才调用encode/decode | 正常模式保持同K计数，full-catalog阴性不变 |
| R3-C05 | code与theory交叉 | “控制资格失格”和raw饱和故障不能混为删除测量 | 控制mask与raw_status分开；合法raw仍更新，缺故障似然只归档并明确OPEN | mask改变仍8帧ledger，SATURATED不伪造似然而保留received archive |
| R3-C06 | code审图 / root | 旧新图草稿把M2预测放在安全缩放之前 | 图作者将合法候选/共同缩放与安全移到M2之前 | 图稿顺序与代码先safe再predict一致 |
| R3-C07 | code审理论附录 | 安全成本写K，实际检查全库J；历史距离成本遗漏Ho | 附录与正文改O(JN²)、O(KP²N(Ho+Hp))；不隐去候选/干扰增长 | README及模块计数对应 |
| R3-C08 | theory/root 概率复核 | 固定设计Green Fisher不能直接当自适应闭环Fisher | 代码只称finite-bank固定已实现设计评分；合同加入由更早history冻结动作后采新验证对 | 不把raw加性Gaussian证书替代lognoise理论 |
| R3-C09 | code审算法1 | 覆盖/补测实际不做M2评分，旧短伪代码可能写成全分支评分K次 | 主文Select辅助逻辑区分；源码fallback的scored_count=0 | bounded remeasure/covers实际执行安全，无多计证 |

这些是 V46 新增全链实现/表述的具体修复；不能据此声称 V45A 既有 T/R 公式本身错误。

## 已实际执行的证书

`tests/test_chain.py` 退出0，结果在 `results/chain_certificates.json`：六种输入存储次序携带不同增益/时延/历史，端到端误差0；七种方法全库同评分得到相同动作；同一 raw 换块名/换行序重复计证均拒绝且无状态改变；错配标定的反例T差约0.07847；负raw似然复核差0；连续安全拒绝端点检查漏掉的碰撞；计划2s实际执行1s按真实路径更新；2机与4机均可运行；同XY仅高度信息的XY EIG约-1.13e-17（数值0），真正分离XY的诊断约0.67687。

`run_reference.py` 退出0，20s软件参考运行包含9次实际决策和40个唯一原始帧。其有限世界、时间和概率输出只用于检查完整运算；**不是**合同要求的VGR 300s定位实验。

`preflight_native.py` 对未冻结模板按设计退出4，状态为 `UNRESOLVED_DATA_OR_INTERFACE`，22项缺少冻结/原生文件。它没有偷偷改用Green，`method_failed=false`、`native_performance_evaluated=false`。原生阶段交给本合同明确的Codex工作。

本轮另已真实下载并审计 Orebro3DSEN 官方固定版本的10个CSV；134427行、337196个有限负浓度值、时间单调。报告见 `results/OREBRO_AUDIT_ZH.md`。这只支持字段与资格边界，不是M1运动或定位增益。

## 剩余原生证据

GADEN/VGR多机公共时钟；局地风及传感动态校准；真实地图与加速度/飞控段；共享普通源前向与模型覆盖；完整300s等预算闭环；强原生PMFS/EIG对照和独立留出住宅。缺失项目保留OPEN，详见执行合同。没有独立标定时，代码不生成形态/相干的误拒误放率。
