# 原生恢复增量代码

本目录是2026-10-23新增实现，不覆盖Pro交付的V7负结果或冻结O24。

先读根目录 `NATIVE_EXECUTION_REPORT_zh.md` 与 `results/native_20261023/R2_RESULT.json`。本次R3/R4明确未执行。

## 已执行入口

按顺序执行，输出目录含冻结保护，勿在原结果目录重跑：

1. `recover_assets.py`：仅8个开放世界、14,424帧、地图及参考数组的字节/身份恢复。原始根目录为 `C:/GADEN_OCB_R2_ARCHIVE`，House01在原workspace。没有新生成。
2. `build_native.cmd`：Windows MSVC C++17编译。只读查询与M1/raw-joint推理API在 `native_query.cpp`。Linux可用 `g++ -std=c++17 -O2 -fPIC -shared native/native_query.cpp -o native/native_query.so`；将相应调用方库路径指向该文件，本次没有伪称已在Linux验收。
3. `extract_existing_worlds.py`：1200项历史原生读出回归、33项风分量回归，之后提取冻结50–70 s双点窗口。
4. `fit_native.py`：只打开TRAIN块；粗采样适配明确登记，不能冒充原默认高频机制或真实PID资格。
5. `evaluate_native.py`：冻结模型后只评估DEV；保留普通强基线、平局和失败。
6. `verify_native.py`：冻结哈希、20次C++推理对照、真实原生进程组件和拒绝重复消费检查。

上述绝对原数据位置在恢复脚本和收据中可见。派生块/模型和所有结果已包含；原1803帧×8、原16件参考数组不重复分发。保留取回脚本与原SHA。

## 可调用的原生组件

`python native/gaden_executor/server.py --run ocb_r2_cfg00_r01 --output <新目录>`

stdin/stdout JSONL接口：`{"id":1,"method":"describe"}`，再 `{"id":2,"method":"execute","action":0}`。返回同一物理时刻两探头的浓度和局地风文件；无源标签、无全图风输出。再次消费同一窗口或action不在冻结集合时拒绝。

组件schema是 `gsl-native-fixed-probe-component-1`，有意不同于完整动作桥；没有为绕过资格门填充M2几何、无人机速度/安全或假运动轨迹。它不是完整ROS executor。

## 复核而不重做科研

运行 `python native/verify_delivery.py` 检查已交付模型/块/结果并从冻结参数重新计算20次M1/raw-joint分类；不拟合、不改协议、不生成新世界。

完整原生组件验证需要原始归档；Windows交付DLL可选携带，源码和构建命令永久保留。没有对应平台的动态库时，交付复核仍可执行Python冻结预测复算，但不能声称完成该平台C++验收。
