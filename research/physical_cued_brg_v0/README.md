# 直接进入算法开发与闭环对照：物理候选提示的循环门控 PMFS

**这不是新一轮“找信号”的任务书。** 本包给出网络、训练器、已训练的 OPEN 热启动权重、在线服务、C++ 客户端、PMFS 接入补丁、对照与闭环计分代码。

## 一句话方法

保留 PMFS 的候选 occurrence 与 rawu forward，把“实际测量、候选应产生的测量、历史匹配状态”送入一个共享的小型循环门控网络；输出完整候选源概率图，并同步更新原 planner 真正使用的 `varianceOfHitProb`。

母算法是 Salehi 等的 **Bidirectional Recurrent Gating (BRG), Nature Communications, 2026-05-05**，不是旧 dANN。本包是依据公开机制独立编写的候选条件改造，**不是作者视觉 U-Net 的复现，也没有作者预训练的气源权重**。

## 已经实际完成

- 13,120 参数网络及 GRU、feedback-off 对照，PyTorch CPU 可运行。
- 从历史 OPEN H01/H02 三个环境导入 288 条既有轨迹；216 条训练、72 条开发，所有同 run 的路径增强不跨集合。
- 三个版本分别训练 15 epochs，权重、全部训练曲线都在 `checkpoints/`；**没有因验证表现挑换架构**。
- 26 项确定性/梯度/输入语义测试。
- 已编译 C++17 客户端，与 Python 服务真实 TCP 往返成功。
- 使用 House03 **仅模型预测**的完整624源银行做接口规模/耗时测试；没有读取这次的 House03 气体 target。结果在 `results/interface/`。

## 没有完成，不应冒称

**没有 ROS 完整工作区编译、VM 闭环、真实无人机或新 fresh 验证。当前权重没有证明优于普通 GRU，不能宣称主创新已经成立。** 已训练权重是可用的开发热启动，不是已验证的部署模型。三套 warm-start 的 best development NLL 都约 1.0，BRG 并未领先；这只是短时训练管线检查，不是用于宣布方法胜负的实验。

## 先运行

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
export MARKED_REVIEW=/path/to/MARKED_ENCOUNTER_PMFS_D0_REVIEW_20260927.zip
bash tools/start_open.sh
```

上面不是硬性离线 PASS 门：完成软件检查与固定训练后，直接接入现有闭环器比较。`start_open.sh` 的正式开发配方为30 epochs/8路径；本包实际完成的是15 epochs/4路径的训练冒烟，区别在日志中保留。

已有热启动可直接用于**开发调试**，不必等重新训练：

```bash
python tools/serve.py --checkpoint checkpoints/brg/best.pt \
  --bank example_banks/h03_model_only.npz --allow-warmstart \
  --tcp-port 17831 --log runs_brg_events.jsonl
```

禁止用 `example_banks/env_0_bank.npz` 等六候选示例去对比原生全屋PMFS；完整候选支持必须相同。H03示例是已生成的 PMFS 模型银行，不是目标 GADEN ensemble。它的风条件是固定平均风模板，因此首轮是 **cached-model 条件下的开发闭环**。其他环境需要本来就合法可计算的完整候选模型银行；不能拿 GADEN 每个真源的未来浓度补充。

## 最短交付顺序

1. 用包内脚本训练三个同输入模型（或先用热启动作功能联调）。
2. 在新 worktree 执行 `integration/apply_humble_patch.py --dry-run`，核对 frozen fork 的锚点，再编译。
3. 同步替换 sourceProbability 和 varianceOfHitProb；同一次 measurement 只消费一次；保持 planner、controller、测量预算不变。
4. 用既有 OPEN plume 回放做 paired closed-loop：Native PMFS / 同输入GRU / BRG / feedback-off。
5. 交付最终定位成功、距离误差、耗时和失败原因；不再交 rank 信号或一份新母理论清单。

详细执行说明：`CODEX_EXECUTE.txt`。方法推导：`docs/METHOD.md`。实际测量和限制：`STATUS.json`。
