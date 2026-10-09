# PMFS R3：时间戳接口闭合 → 单次概率更新 → 科学归因（2026-10-09）

## 基于 R2 的事实冻结
- 本地上传 `PMFS_WIND_ONE_UPDATE_R2_20261009_SMALL.zip` 独立复核验证脚本PASS；全部文件SHA清单复核PASS。
- 真实 ROS/TF fixture 14 cases：N1新鲜恒定姿态10/10 PASS（非零四方向×两位置8，零速2）；另有 map frame、共享FROM、混用时钟三个负对照；延迟+90°姿态变化1次导致 PMFS/GMRF ≈1.5707989367 rad 分叉。
- 根因到“原生回调运行行为”层：PMFS `Algorithm::windCallback` 只设置 `PoseStamped.header.frame_id=msg.header.frame_id`，省略 `header.stamp`，TF最新；GMRF按 `msg.header.stamp` 查历史TF。原生 `gsl_server` 这处修复属于工程接口适配，不得充当论文主创新。
- P0保持PASS；`P1a_FULL_MOVING_DELAYED_HOLD`；`P1b_NOT_RUN`；P2/P3未合格；GMRF估计场尚未通过收敛资格；历史H02依然`UNRESOLVED_CONTRACT_HOLD`。
- 适用范围：R2 PMFS harness 是固定源码的受控共同 `Algorithm` 回调子类，不是 full ROS GSL actionserver；混合时钟负对照TF“能成功”不等于合同合格。

## R3 不等待原生完全泛化；分成互不偷换的两条轨迹
**T0 / N0：`UPSTREAM_UNMODIFIED`**：固定 upstream `4e141e162551e674f2f30ddb8859136c72139aac`，不改任何程序。前置验收规定有效输入必须：**同一时钟域、时间戳可追溯、消息年龄小于运行前冻结上限、从msg采样stamp到PMFS实际TF lookup这段期间传感器frame相对map的平移/航向变化足够小**；用真实TF记录证实每条事件。对超出门限的延迟移动用例标 `UNSUPPORTED_OR_FAIL`，保留既有R2 90°反例。为论文级动态场景不可声称原生PMFS全面合法。

**T1 / N1：`STAMP_CORRECTED_ENG_VARIANT`**：对固定PMFS源码仅施加独立可追踪的最小补丁（diff文件）：
```diff
- anemometer_downWind_pose.header.frame_id = msg->header.frame_id;
+ anemometer_downWind_pose.header = msg->header;
```
这将令 PMFS tfBuffer.transform 使用消息发生时刻。验证对纯fresh/恒姿态数据不改变风读数，对延迟+90°数据恢复物理正确的t1方向，与GMRF同时间基准。**同样必须有可用TF历史，正确时钟域，消息年龄合同**；超出TF buffer保留时段不能自动重写stamp掩盖。该变体保留原PMFS概率建图、源模拟、后验及运动逻辑，仅是版本化工程修复，不标为原论文原样基线。

**目标**：让 `P1a_STATIONARY_SCOPED_PASS` 与 `P1a_DYNAMIC_CORRECTED_PASS` 各有独立证据；前者不需要所有移动延迟ケース通过，后者不是上游原样重现。

## Task R3-A：最小时间戳真实ROS对照（无需新气体数据）
- 使用已存在VM中的隔离构建目录；绝不在原生checkout直接打补丁或覆盖旧HARNESS。校验源 SHA/ELF/commit。
- 比较N0原版与N1最小补丁，在3个必要输入下检验：（i）新鲜固定姿态0°/90°；（ii）带消息旧stamp且之后旋转90°的动态TF；（iii）新鲜但位置非原点、yaw不为零。保留R2共享FROM、map frame与混合时钟负对照，不重复全部14条可复用样本；只补时间戳差异所需用例。
- 对两消费通道输入必须仍区分PMFS TO与GMRF FROM，保持真实sensor frame、tf、同一物理风矢量。采集收到的真实ROS消息时戳、PMFS实际transform时间、GMRF存储xy与TO方向、时钟域。拒绝非法时间戳，不通过修改ROS端本地接收时间冒充测量时刻。
- 在消息采样时刻和PMFS消费时刻分别读取tf `map←sensor_frame`，导出 `pose_drift_xy_m`、`pose_drift_yaw_rad`；明确追踪 `LookupTransform` 对 `stamp=0` 的选择。接受门：预声明角误差 <1e-4rad、位置误差<0.01m、时钟同域且 age<2s，并在固定TF测试保持姿态不变。运动延迟case N0预计 FAIL、N1预计 PASS，必须如实测量，不能硬编码期望为结果。
- 若补丁编译失败、t1时刻TF无历史或GMRF仍未插入，报告原因；不额外修改算法其他逻辑。产出 `UPSTREAM_VS_STAMP_PATCH.csv`、`TF_STAMP_TRACE.csv`、`R3A_GO_NOGO.md`。

## Task R3-B：尽早启动P1b的**受限**单次在线-离线核心校验
门控：若 R3-A 原版固定姿态/同钟合同 PASS，则可以在 **固定停留、合法风向、合法数据、两端物理时刻一致** 的限定范围下运行一次 source update。不必等原生任意移动消息全部PASS。该单更新不能代表原生闭环导航。
- 优先使用旧合法20事件/87叶恢复资产，但须确认事件/风/候选支持（不合格就HOLD）；同一时钟TF与生效参数固定。
- 由实际 native PMFS source update 捕捉测量地图logOdds/confidence、每次quadtree叶、原生候选叶内采样位置/RNG、模拟hitMap、raw logscore、归一化后验及最终叶排序。用同样输入在离线回放器逐层比较；候选叶和随机点分布不能从truth猜测。
- 若无合法源模拟输入，允许**只读查找**已存在87叶模拟图，不许拼接新工况冒充官方；缺任何关键状态时明确`P1b_HOLD_MISSING_STATE`，列单条路径或函数钩子，不能用score-only PASS顶替online core parity。
- 具体对应 `PMFS_CORE_PARITY_TO_SCIENCE_CODEX_CHARTER_20261009.md` 的单次update捕捉合同。执行完成前不启动P2原生完整导航，也不训练新网络。

## 关键区分与决策
1. N0 原版动态时戳缺陷 → **工程局限**；N1 修复后改善只是 `ENGINEERING_FIX`。
2. N0 固定停留数据通过，且单次source update parity通过 → **合法方法级基线**，但不等于300s导航基线。
3. 时间/风场/地图已合法，却仍出现真实源和候选源传播预测证据冲突 → **科学假设线索**，仍需后续独立源/realization验证，而不是今天就立主创新。
4. P1b没有真实在线候选图/随机采样状态不得PASS。GMRF收敛仍HOLD，应优先使用有可核验的`USE_GADEN+useWindGroundTruth`原生前向风场或明确区分measured-wind / simulated-wind。

## 冻结约束
- 本轮只 R3-A＋一次可能的 R3-B；不新增CFD/GADEN、下载数据、训练网络、调整结果阈值、额外seed/House；不修改冻结开题报告。
- 输出：中文审核 `PMFS_TIMESTAMP_R3_REPORT_zh.md`，两个variant单次ROS记录，已定门的数值验收，`R3_SINGLE_UPDATE_PARITY.csv`（确实完成时才存在），SHA256和小ZIP。结论用 `STAMP_PATCH_PASS/HOLD`、`SCOPED_P1b_PASS/HOLD`、`PHYSICAL_MECHANISM_NOT_YET_QUALIFIED`。
- 如单更新仍缺资产，请停止工程循环，开题报告继续使用“源—受体传播历史一致性”作为待验证问题，不得因为截止时间强求实证。
