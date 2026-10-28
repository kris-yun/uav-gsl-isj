# Codex V41｜先复核完整算法源码，再做 S2 原生实验

**研究分支**：`research/v41-executable-flowolf-20261028`；继承V40理论分支。你不必再帮忙发明算法；请先运行并审计现有V41代码，在原生证据下判定是否可晋级。

## 第1步：代码合格性

```bash
git fetch origin
git switch research/v41-executable-flowolf-20261028
cd research/v41_flowolf
python -m pip install -r requirements-v41.txt
python -m pytest tests/test_v41.py -q
python demo_v41.py --steps 20 --seed 9001 --out V41_SYNTHETIC_20.json
```

本地已通过27项单元断言和20步高斯同模型闭环；它不等于 S2 或真实定位证明。固定合成案例BIO=0m、普通8候选EIG=8m、普通投影=4m、BIO-noidentity也为0m。另行固定的3个合成源×2噪声种子（16步）结果：BIO均值4.11m，普通全候选EIG=5.44m，普通全候选投影=4.11m，BIO-noidentity=2.77m，BIO-nogap=4.11m。**身份保持主模块尚无独立实证收益，甚至部分消融更好**；这些是开发样本而非独立统计，不许挑单个0m声称晋级。

## 第2步：完整原生数据与接口对齐

先找到并校验唯一原始 `FSR_S2_120m_CH4_DATA_ONLY_V1_20261026.zip`，预期SHA256=`210771b27161b74d73c5e4d8c620a85f1652f402c80b81a68c12d41a03fceffe`。需要5×60s、每世界601帧、共3005帧，以及原生 AgentSession、查询、障碍、风、传感器延迟和一阶记忆。V34只含静态子集，绝对不等于完整原生数据。使用公共的候选源支持文件，**不能**从labels/sources.csv读真实源后作为在线候选域或策略输入。

以下命令的路径是占位符，必须用你本机真实校验的文件路径替换，不得报告虚构成功：

```bash
python run_v41_s2.py --root <完整S2原始解压目录> --world W001 \
 --sources-npy <已冻结公开候选源支持_Sx3.npy> \
 --start-json <已冻结三机合法ENU起点.json> \
 --mode bio --seconds 5 --seed 9001 --out <证据目录>/V41_W001_5s.json
```

首先验证多AgentSession每0.1s顺序步进与单机标准AgentSession的同世界同种子前缀完全同步，核实每机独立噪声、1Hz读出、2s延时/1s时间常数、背景1.93457ppm、正检出门0.06ppm，检查避障/机间距。控制器只获得 Reading+公共地形，不得传入世界对象、完整真值风、未来气团或标签。未经明确同步/查询对齐，标 `NATIVE_MULTI_SESSION_PARITY_UNKNOWN`。

## 第3步：正式的 E0 → E1 → E2，不允许跳级

- **E0 原生接触**：执行V38固定三机路线、普通同预算横风/多高度覆盖、V41 BIO/消融的真实气体观测，W001/W002正常案例harm和W003/W004/W005旧零检出世界救援分开记；新路线到达真源近处不等于成功检出。
- **E1 源条件前向资格**：共享普通V34前向在正检出窗，使用合法未知q/h/m是否能解释真实观测及真源附近响应（真实源仅事后归因）；如果前向仍预测真源为0却实测有气，就标 MODEL_COVERAGE_FAIL，禁止继续宣称M3源消歧成功。
- **E2 二维概率定位**：仅当前向合格且有独立误差界后，对相同源支持、同预算的普通全候选EIG/GLR/E-opt/覆盖做MAP、Top5%、rank、Brier/NLL、false-declare、正常组harm、CPU/前向预算比。`ordinary_eig`是最多8候选的快速近似；`ordinary_eig_full`含同动作库全部候选，计算资源不同，需要画效益-调用/时间曲线。BIO-noidentity、BIO-noflow、BIO-nogap均必须同样做。

## 已实现与尚欠缺

- **M1 已代码化**：身份保持风嗅×历史相对运动欠采样方向→合法平移/重构候选；并非来源论文直接给出的无人机轨迹公式。
- **M2 已代码化**：普通源×公共q后验、二维源概率输出和无二次计证；**尚未**实现任意q(t)与完整多模式风误差后验。
- **M3 已代码化**：未知q及局部源高的投影Fisher、源对有界q轮廓距离、同模型EIG与可信误差门；**尚未**实现有严格下界证明的所有传播模式/时变q/风场联合不确定性。
- **原生部分尚未验证**：S2完整气团接口的三机同步、候选源真实响应覆盖、误差界校准，以及独立的定位收益；最终JCR二区主创新现在仍为HOLD。

## 交付与停止条件

保存 `evidence/v41_native_implementation/`：实际argv、源码SHA、原始数据SHA、测试及CPU日志、每机1Hz浓度/风/轨迹、每tick合法动作、源后验、TRUE_EVAL_ONLY标签、S2 E0真实检出、E1源附近模型误差、E2合格后的普通强对照与消融、机器可读PASS/FAIL/UNKNOWN。只能先修复实际接口/安全bug，方法参数须冻结，不得按标签调W005。缺候选源有效前向时仍完成E0，E1/E2如实UNKNOWN，不得报告成功。