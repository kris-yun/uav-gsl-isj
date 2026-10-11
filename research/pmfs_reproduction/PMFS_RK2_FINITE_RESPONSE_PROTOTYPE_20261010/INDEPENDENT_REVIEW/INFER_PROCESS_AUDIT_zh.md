# RK2 独立源盲推断进程审计

结果：`PASS_ISOLATED_SOURCE_BLIND_INFER_PROCESS`。在独立 `python -I -B` 子进程中，用已冻结的4个forecast NPZ与4个标量观察JSON重新计算16组共同评分，所有结果与 `SOURCE_TASK_PREDICTIONS_BLIND.json` 最大数值差为0。候选重命名及置换16例均通过，数据访问只有明确白名单中的8个文件。实际推断阶段非法文件访问为0、被阻止的尝试为0，没有训练、粒子读出或物理查询。

子进程只取得上述8份文件和冻结 `rk2_infer.py` 的隔离复制件，不提供旧父包路径、training/model对象、原始快照、占据地图、测试粒子、φ贡献、生成者映射或评价文件。推断先对每份候选参考响应进行float32严格阈值化，再形成平滑事件频率及固定meanlogscore softmax。全部源概率与实际保存结果逐字段复算。

在正式数据加载前，审计器尝试打开一个专设、确实存在的非法测试文件；Python audit hook在返回任何字节前抛出PermissionError，软件检查通过。此QA尝试单独记录，不混入实际推断的非法读计数。

首次审计启动按严格代码白名单阻止了Anaconda NumPy的 `mkl` 代码依赖，尚未读取任何候选或观察数据。只补充该安装版NumPy明确导入的mkl依赖目录后，在新审计目录运行成功；预测、推断源码、算法与数据白名单未更改。失败stderr留存在 `isolated_infer_process_validation`，成功完整日志在 `isolated_infer_process_validation_v2`。每次审计只启动1个子进程，合计1次依赖初始化失败与1次完整审计，均未调用producer。

证据文件：

- `audit_infer_process.py`：可复算审计器。
- `isolated_infer_process_validation_v2/INFER_PROCESS_AUDIT_RESULT.json`：冻结输入SHA、16例复算与置换、资源和判决。
- `isolated_infer_process_validation_v2/ISOLATED_CHILD_STDOUT.json`：完整open路径轨迹、8文件白名单和所有评分。
- `isolated_infer_process_validation_v2/ISOLATED_CHILD_STDERR.txt`：成功进程无异常。

边界：Python audit hook记录的是安装后可见的Python open、socket、process事件，不能宣称跟踪了所有本机动态库系统调用。该证据支持这份冻结infer接口的源盲输入隔离，不说明前向模型、物理预测或未见任务本身已通过验证。
