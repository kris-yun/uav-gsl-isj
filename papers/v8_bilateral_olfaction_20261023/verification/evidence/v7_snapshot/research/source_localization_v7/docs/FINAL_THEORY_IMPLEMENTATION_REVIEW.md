# V7封包前理论与实现终审

审查日期：2026-10-23；审查者：radar / information-theory代理。范围为`THREE_INNOVATIONS_AND_THEORY.md`、当前三模块与新增raw-joint、qualified block、2D map、JSONL bridge、TRAIN-only RBF geometry接口。只核对正确性与可主张范围，没有新增物理实验，没有改写冻结静态或156 episode结果。

## 1. 理论主线与代码的一致性

未发现需要撤回的核心条件定理。

|对象|终审判断|交付时必须保留的边界|
|---|---|---|
|M1反对称、固定总平滑的边缘一致性、JS覆盖单调性|与代码一致；嵌套分区条件充分|单调不等于次模/贪心最优；训练距离不是总体辨识证书|
|M1数据处理与静态EO可逆性|证明正确，与冻结静态数值等价相符|不能声称确定性特征增加同一原始块的信息|
|M2方向管、Taylor余项、梯度差方向|与公式/几何接口一致|Hessian/三阶导界未实测；非零梯度差才可归一化，零梯度各方向并列|
|M3单位成本LP与抽样频率|变换正确，资源份额与频率区分正确|估计KL不是实际KL下界；fallback不继承完整LP最优性|
|M3付费覆盖|固定合法动作域的访问概率下界正确|预算尾段域变化、不可辨源及零先验不在必恢复保证内|
|M3新后缀fixed-R审计|似然比超鞅支配、可预测备择、同一实际过去的条件证明正确|E本身不必为超鞅；估计通道只有模型相对保证；不得回乘posterior|

命题7的零梯度退化条件已由bio在原文中补齐并完成复读。该修正是定义域完整性，不影响已执行结果。M3没有未说明的五步恢复、真实plume错误率或渐近最优性声明。

## 2. 新增接口核查

**raw-joint。**实际是同原始完整窗口经`log1p`预处理后的无监督向量量化，默认18符号，再估计一个联合条件表。名称“强同窗口参照”可用；它仍是压缩与有限样本拟合，不是原始连续数据的理想Bayes上限。

**2D map。**导出的是离散候选概率质量，同XY的候选质量相加，其余笛卡尔网格格点标记为非候选。它不插值，也不是连续面积密度；`legal_source_mask`表达已提供的候选支持，不能单凭该数组证明native占据体素合法。

**split隔离。**qualified loader先筛选允许split，才访问观察文件；封存final文件不会为了训练被打开。replay另拒绝已出现在M1训练实现集合中的世界。物理资格仍来自外部已固定的review，布尔字段和字节校验本身不创造物理证据。

**TRAIN geometry。**RBF均值与解析梯度只使用TRAIN块。现版本还固定M1原manifest的SHA和统一观测高度。该A′适配没有声称原生梯度已校准；其协方差池化、局部common-mode近似、短基线与RBF外推限制必须保留。

**live桥接。**已有收据为`CONTROLLED_LEVEL1`、6步、57 s；它证明真实子进程JSONL执行链运行，不证明ROS/GADEN或物理飞行接入完成。主进程不接收真源标签；新块先准备audit、再读出/编码/单次后验更新，raw ledger拒绝重复ID与重叠窗口。成本上界、返回物理时间、动作端点与世界ID均有执行检查。

当前bridge采用非阻塞完整行读取。构造服务器先输出半行再延迟0.25 s，客户端timeout=0.05 s时，实测约0.052 s抛出TimeoutError，未被`readline`卡到后续半行。这只验证协议边界，不升级物理资格。

## 3. 本轮发现的合同缺口与最小修正

构造性复现保存在`results/final_review/PRE_FIX_BOUNDARY_CHECKS.json`。没有使用任何物理数据，也没有为发现问题打开封存观察文件。

|编号|修复前真实复现|为何影响正确性|最小修正|
|---|---|---|---|
|F01|同一episode_id内换nuisance_id，或换realization_id，仍回放完成|前者破坏声明的固定R；后者可把多个世界误记成一条轨迹/一个实验单元|逐episode在更新前检查唯一source、nuisance、realization；需要重置时显式另起episode|
|F02|训练ppm，开发块声明ppb，仍直接进入同编码和似然|同数值不同单位不是同一观测模型|冻结units与必要的有序传感器合同，calibration/replay/live一致验证或显式转换|
|F03|RBF文件保存joint_covariance，bridge却从describe取另一个矩阵|不能将未使用的TRAIN协方差说成live几何已冻结|使用冻结文件协方差；旧L1模型缺字段时只接受明确标注的构造矩阵并记录来源|

**三项均已修复并复核。**root完成源码修改后，本代理对同一构造样本重放：合法基线正常完成；切换nuisance、切换realization、ppm改ppb、交换传感器次序四种违反合同的输入均抛出`QualificationError`。F03经代码复读确认优先加载冻结NPZ协方差；只有显式`CONTROLLED_LEVEL1`可用构造性fallback，原生缺失即拒绝，逐步日志记录`covariance_source`。指定的两项集成回归测试亦为2 passed、13 deselected；未扩大为新一轮性能实验。

最终状态为`PASS_CONDITIONAL_RESEARCH_DELIVERY`，详见[最终收据](../results/final_review/FINAL_REVIEW_RECEIPT.json)与其中的源码SHA。本表保留修复前事实。修复不改变已经冻结的L1终点，也不等同外部物理资格审查。审查代理没有修改源码，封包应从最终src重建分发包，不能混入旧build/lib。

## 4. 可诚实交付的结论

可交付为：具有可检查机制、完整概率/审计职责分离、强联合参照、可运行受控桥接和明确原生接口门的研究包。新增软件功能不会提高原证据等级。静态M1未胜出，156个L1 episode中强基线及主要消融饱和，full七次audit challenger触发并未证明独立收益。

仍须写清：dwell-only工作概率与M2 travel侧信息；均匀phase吸收源平移的对称性；finite候选/finite nuisance；真实源体素、连续窗口、局地风和传感器资格HOLD。代码与数学性质通过不能代替独立物理增益。

另有一项文献勘误：bio在FUSION作者稿v2 §IV脚注4发现代码DOI，本代理随后核对原文，确认[10.3217/kcn0n-03509](https://doi.org/10.3217/kcn0n-03509)。会议文档已更新；独立冻结稿未修改。本轮未下载或运行该代码，不能把发现入口等同复现。

证据：`results/final_review/`；`results/bridge_demo/BRIDGE_RESULT.json`；`results/control_matrix_v7_frozen/CONTROL_MATRIX_RESULT.json`；`results/ocb_static_v1/STATIC_PILOT_RESULT.json`；本目录三模块理论与科学问题文档。
