# 官方代码与权重审计

## 证据与复现范围

官方仓库：https://github.com/CHTiansweet/Topography-aware-Gas-Source-Localization

冻结 commit：`ca0c387be9f27716a422588ac2299e2d816c3e2a`。

四本 notebook 完整导出至 `*.cells.txt`，原文件 SHA256 见 `NOTEBOOK_HASHES.json`。论文 `GSL_preprint.pdf` 来自作者 README 所链接的文件，保留全文与提取文本。论文与代码有差异时，本轮说明差异，不悄悄替换算法。

`OFFICIAL_REPRODUCTION_PASS` 仅指 **官方软件 smoke**。未复跑论文全数据的完整训练和精度表，不声称已复现全部论文性能。

## 1. 网络

`GSL_train.ipynb` cell 2 和 `GSLInference.ipynb` cell 2 中的 UNet 定义经 AST 比较一致。标准 2D U-Net，双 3×3 conv（bias=False）+ BatchNorm + ReLU，通道 64/128/256/512/1024，四级 max-pool，下采样 skip 与转置卷积上采样，最后 1×1 conv + sigmoid。

三通道版本参数数为 **31,037,633**；两通道版本为 31,037,057。本轮未减小网络或加入时间编码。

## 2. 三个输入通道

`np.stack([map_origin, wind, encounter], axis=0)`：

| 通道 | 代码实际含义 |
|---|---|
| occupancy | 原始二维地图：unknown=-1、free=0、占据值至100 |
| wind | 每次 encounter 的机器人局部风方向对应全图 ±1 halfplane；截至 prefix 累加 |
| encounter | `map_proceeded==233` 的二值已遭遇位置图 |

wind **不是完整 CFD/vector wind map**。它只使用 encounter 时机器人本地的方向、位置与姿态。风速不作为连续数值场进入网络，`0,0` 是无风特殊标识。原函数将 clockwise angle 取整数后加负号，通过 quaternion 转成世界方向，再在 row/column 网格上划分 halfplanes。

不能给未访问位置填 GADEN concentration，也不能用全场 oracle wind 替代局部风日志。

## 3. 尺寸、padding 和归一化

固定 `3×279×279` float32。仅在右侧和底部 pad，不插值改尺寸，不将占据值除100，不归一化累积 wind channel。

**上游存在差异**：训练 dataset 的地图 padding 为 **−1**，inference notebook 为 **0**。Wrapper 保留这两种各自语义；初次探测误用训练 padding 的小结果保留于 `initial_smoke_training_padding/`，最终预训练 smoke 已改为官方 inference padding=0。此修正未涉及 OCB target 或性能选择。

若新地图超过279格，不允许静默裁切/缩放。Map resolution、物理覆盖范围和坐标轴转换必须先签署；当前未做 OCB transfer 推理。

## 4. Label

第 N 次 encounter：`D_N = 3 exp(-0.3(N-1)) + 1` m。

Grid 坐标为 `origin + index×resolution`，不加半格。距离超过 D_N 或 unknown=-1 的点为0；其余为：

`((D_N - distance)/D_N) × ((100 - occupancy)/100)`。

写盘保留两位小数。真实 source 仅用于生成训练 label 和事后评价，不能进输入。原标签构造器在官方 epoch1..4 的首条 label 上重算，数值完全相同，见 `LABEL_CONSTRUCTOR_PARITY.json`。

## 5. Output map

每 cell 独立 sigmoid，0..1，**不要求全图 sum=1**。不能直接解释成已校准的 PMFS source posterior；本轮不额外 softmax。

## 6. Loss 与训练

代码 `CustomLoss(positive_weight=5)`：逐 cell BCE；soft target 非0时权重为 `5×target^0.2`，target=0 则普通 BCE；最后 mean。输出和 target clamp0..1。

Adam lr=1e−5；**代码 weight_decay=0.1，论文写0.01**，本轮遵循代码0.1并记录冲突。上游训练100epochs，batch8，ReduceLROnPlateau factor0.5/patience5。

本轮 fresh 初始化，固定 seed2026093007，完成2个真实 Adam 优化 step 和一个 validation step。未用 OCB 数据训练，未声称收敛。

## 7. Train/validation split

`GroupShuffleSplit(test_size=0.2, random_state=42)`，group 为整次 physical trial。每 trial 的全部 encounter prefixes 和四种 rotation 都保持同组。官方训练代码使用 normalcondition epoch1..60；仓库现存 normalcondition64 trials。

本轮为软件 smoke 只用官方 epoch1..4，共100个增强样本，train64/validation36。Split 在训练前写盘并 hash，见 `OFFICIAL_SMOKE_SPLIT.tsv` 与 `OFFICIAL_PRE_RUN_FREEZE.json`。

## 8. Encounter 样本

每次 encounter 对应一个 prefix：累积截至此 encounter 的 encounter 图与 wind halfplanes；同一 trial 有多个 prefix。每 prefix 再做0/90/180/270度旋转，三个输入通道和 label 一起旋转。增强样本不是新增独立 plume。

## 9. 四个权重

见 `results/LFS_AUDIT.json`，实际大小和 SHA256 全部符合用户冻结清单，`git lfs fsck` PASS。

| 文件 | 输入通道 | 严格加载 |
|---|---:|---|
| unet_model_final.pth | 2 | PASS |
| unet_model_final_1.pth | 3 | PASS |
| unet_model_final_2.pth | 3 | PASS |
| unet_model_final_3.pth | 3 | PASS |

上游 README/commit/notebooks **没有逐文件明确标注实验变体**。不能根据文件编号杜撰对应方法或按 OCB 成绩挑权重。本轮预先固定 `_1` 做三通道推理 smoke；训练 notebook 的保存文件名也带 `_1`，但这不能证明其完整训练 provenance。

## 10. Source location 与 inference notebook 限制

论文p6描述 **概率加权 centroid**。本轮主输出为原始地图范围内的加权 centroid，按原 grid origin+index×resolution 换坐标；argmax 只作诊断。

Inference cell4包含 `nowind` 实验分支，满足其条件时置零风图，只在特定 save 条件下推理。不能将该 cell 当作普适三通道推理规则。本 wrapper 重用原网络与官方通道函数，不启用此 ablation；差异已明确记录。

## 本轮结果与界限

四权重 strict-load；GPU 推理输出279×279、有限、0..1；两次同输入推理逐字节一致；实际 GPU 训练梯度非零，loss/validation有限。可视化见 `OFFICIAL_LIKELIHOOD_VISUALIZATION.png`。

这确认软件可运行，不确认 House transfer 能力、校准、收敛或源定位优于 PMFS。
