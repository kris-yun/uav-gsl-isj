# ROS/PMFS接入合同

## 已编译与未编译

C++17 `NeuralEvidenceClient.hpp`已在本容器编译并与Python sidecar真实通信。完整ROS2 workspace未在本环境编译，VM runner未执行；不能称为已完成部署。

补丁参考2026-09-27读取的公开MAPIRlab/GasSourceLocalization humble版本，用户frozen fork未包含完整orchestrator源码。`apply_humble_patch.py`使用精确锚点，拒绝模糊修改。Native mode默认`brg_enabled=false`，不调用sidecar，不改变旧科学标签。

## 操作

```bash
python integration/apply_humble_patch.py --pmfs-dir /your/worktree/gsl_server/src/gsl_server/algorithms/PMFS --dry-run
# 显式核对后，去掉--dry-run；先新worktree，不向旧确认分支push。
```

在VM构建原项目。配置参数：

- brg_enabled: true
- brg_port: 17831
- brg_candidates: 完整native合法source数
- brg_bank_sha256: sidecar TemplateBank fingerprint（不是npz文件SHA，两者分别记录）
- brg_run_id: 每个独立case唯一、不含空格
- brg_sensor_offset_z_m: 真实标定的sensor相对robot pose垂直偏移；**不是为了凑模板高度的可调参数**。

补丁通过robot pose z + sensor offset与bank高度核对。存在旋转/非共轴外参时，应由现有TF传感器pose替换这一步，保存实际frame，不用常量伪造高度。

## 事件顺序

每次`processGasAndWindMeasurements`收到一个已经完成的观测block，在线服务消费一次。示例接收时钟为`node->now()`；它是receipt/sim clock而不是精准采样瞬间，需沿用现有writer/window日志。神经输入v0不把这个值用作预测特征。

在原`timeToSimulate`更新时刻，执行原forward bookkeeping后，把两张返回数组提交：

```
sourceProbability = result.sourceMap;
simulations.varianceOfHitProb = result.hitVariance;
movingState->chooseGoalAndMove();
```

这是同一原生更新节奏，不在神经版本偷加导航轮数。posterior不是重复乘积。内部三轮feedback不会三次写回map。

**重启/reset分开**：每个case新run，清空隐藏状态；相同event重发返回同结果；同event改内容报错。网络/通信失效不偷偷切回native，应取消新动作、记录错误并按已有安全/模拟框架处置。不要把异常运行从比较中静默删掉。

## 完整候选支持

6候选训练示例只用于训练/服务冒烟，不可对比全屋native。补丁默认要求candidate_count等于native free-cell数量、坐标网格一致，而且概率不能落在障碍格。若项目用合法pruned支持，两侧必须事先统一该支持并改验证器，不能仅让神经模型看到真源子集。

## 代价与公平性

Sidecar用缓存的全候选p/rawu图，不会每次查询GADEN。它仍然依赖PMFS模型生成，预计算/更新费用单列。第一轮必须包含同银行GRU/ungated，避免把“比classic多用了全银行”的好处全部解释成网络结构。

此版不覆盖风场在线变化后重新生成银行、任意高度、任意MOX响应或真实飞行安全。它足以接入现有固定场景PMFS闭环器作开发比较；不是完整sim-to-real承诺。
