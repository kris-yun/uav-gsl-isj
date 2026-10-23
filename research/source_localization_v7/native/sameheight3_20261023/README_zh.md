# 同高三源有界试验

先读项目根目录 `SAME_HEIGHT_THREE_SOURCE_REPORT_zh.md`。本轮8个新物理世界已完成，当前M1没有独立DEV增益，不得继续按成绩补数据或调阈值。

在解压项目根目录，使用Python3.12及 `requirements-tested.txt` 的固定依赖执行：

```powershell
python native/sameheight3_20261023/verify.py
python native/sameheight3_20261023/degeneracy.py
```

它们只读取包内派生数组、已冻结模型和已编译C++组件，复算分数及退化关系，不需要VM、ROS或新气体生成，会在解压副本内更新QA收据。先检查ZIP的 `MANIFEST_SHA256.json`，再运行核验。

`audit_costs.py` 进一步读取包内8个原始tar、对应stdout与清单，检查14,424个帧SHA、参数和CPU成本。tar省去重复风副本；完整共享风束和占据图位于 `results/same_height_three_source_20261023/shared_inputs/`，每个原世界的对应风SHA写在RUN_MANIFEST。原A四个大世界不重复打包，其原始路径/SHA、所用TRAIN全探针响应和唯一DEV窗口均已保存。

`run_guest.py` 是原ELF的有界运行封装，要求精确SHA与原dirty补丁；不编译替代生成器。`run_and_collect.py`、`extract.py`、`analysis.py` 分别执行新世界、原生读出、普通三源对照，并拒绝悄悄覆盖冻结阶段。不要为了“复算”再次调用物理执行入口。

`mirror_shadow.py` 是用户追加的同数据镜像诊断：沿用旧coarse bank及0.04，对照普通均值、全时序、同核线性延迟、静态和去序镜像。旧高速0.2秒母算子不具备本机约0.6秒档案的资格；此处是理想数值读出，不是硬件PID校准。

`train_motion_diagnostic.py` 是主结果之后的TRAIN探索。候选300/700秒未查询额外DEV，不可将其6/6写成独立验证。`NEXT_SINGLE_MIRROR_PROPOSAL.json` 只是未执行提案，没有本轮额外打开DEV或开展M2/M3的授权。
