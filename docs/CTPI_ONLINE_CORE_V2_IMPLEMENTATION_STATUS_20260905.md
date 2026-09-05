# M1/M2 在线核心 V2：实施与验收状态

状态：`LOCAL_CORE_PASS_RUNTIME_NOT_CONNECTED`。这是准备真实闭环的实现进展，不是闭环有效性 PASS。

## 已实施

- 新增独立 C++17 `CTPIOnlineCoreV2.hpp`，不修改 R4 `CPIR.cpp`、原 field gate 或原算法入口。
- M2：共享面通量的守恒迎风/扩散推进；根据最大流出速率决定子步；检查非负与质量收支；固壁及外域采用显式 no-flux 契约。无状态截零。旧反例新版本得到 2.0（旧版 2.444444），使用两个子步。
- M1 观测接口：候选预测先过 FOPDT，随后接收观测；保留移动期间响应状态；输出不重复的非重叠块均值，拒绝未来风输入、乱序/缺失样本、缺失起始历史、重复消费。
- FOPDT 参数沿用现有配置：tau=1.2 s、delay=0.4 s、初始输入/输出零、线性延迟插值、0–1e6 输出饱和。不是逆滤波，也没有读取真源来更改估计。

## 已验证

Windows MSVC 实际编译通过 `/std:c++17 /W4 /O2`，C++ 自测 PASS：原反例修复、零场、固壁无泄漏、恒风平移、纯扩散时间步收敛、非法数值拒绝、先预测后观测、源强线性比例、块不重复、起始/连续采样契约。

C++ 传感器与本地 `D:/ZYC/A-gas/src/sensor_model.py` 的零输入、阶跃恢复、500 步变采样间隔随机输入逐点完全一致。此为本地源实现 parity，不宣称已比对当前 VM 源文件身份。

对 R4 九组已花费传感器记录做只读回放，最大误差 7.286e-7 ppm，小于两列六位小数舍入的 1e-6 合成误差界。真气体值只进入测试 evaluator，未进入候选源推断。结果：`evidence/ctpi_online_core_v2_20260905/LOCAL_CORE_VERIFICATION.json`。

## 仍未完成，不能省略

1. 尚未定义并验证新 M1 源强/误差模型与后验更新；当前只修好了观测比较接口，不能说 M1 已改好或定位更准。
2. 尚未把 V2 接到 ROS gas/wind/pose 回调、候选源状态及统一控制器，没有启动任何新闭环。旧运行入口仍执行旧公式。
3. 必须解决模拟器起点到 GSL 启动的传感器/输运预历史：不能从晚到的首条观测把候选传感器假装重置为零。V2 当前会显式拒绝缺起始历史。
4. no-flux 是新边界契约，不等价于旧吸收掩膜，不能继承旧场预测 PASS；实际房屋边界/通风口映射须在部署前审计。
5. 运行时在线风快照时间、陈旧风策略、空风起始状态尚须定义并验证；不能把未来 GADEN 风场接作在线输入。

## 真实闭环阻碍（历史记录，连接状态见后续更新）

2026-09-05 当前检查：原 SSH 目标 `zyc@192.168.111.128:22` 连接超时，Windows IPv4 邻居状态 Unreachable，未发现 `vmware-vmx.exe` 进程。备用 WSL Ubuntu-22.04 启动失败，报告其 ext4.vhdx 不存在；未修复或新装环境、未重启 VM、未变更网络。

需要恢复原实验 VM 或提供新的可用 SSH 地址，才能检查实际 ROS/传感器源身份、部署和开始真实闭环验证。不能用本地单测代替该步骤。

后续更新：SSH 已恢复并完成 VM 在线输入源码审计。现在的未完成项是初场/通风模型、风时间语义、启动握手和实际算法接线，不再是 VM 失联。见 `docs/CTPI_V2_VM_INPUT_CONTRACT_AUDIT_20260905.md`。旧失联记录保留，避免改写历史；恢复连接不代表闭环 gate 通过。

## 复现

```text
tools/build_ctpi_online_core_v2_windows.cmd D:\ZYC\A-gas\_staging\CTPI_ONLINE_CORE_V2_20260905
python tools/verify_ctpi_online_core_v2.py --executable <selftest.exe> --sensor-source <sensor_model.py> --spent-r4-root <extracted-R4> --output <new-report.json>
```

所有旧负结果、冻结门槛、受保护 bank 保留。新增代码与报告尚未提交或推送。
