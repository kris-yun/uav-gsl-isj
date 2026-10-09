# 对另一个窗口原生适配指南的复核

**总体方向正确，不能原样作为GMRF接入实施规范。** 它正确区分直接调用PMFS核与完整ROS/GADEN导航，指出PID浓度单位、TF高度、二维推断和AGL桥接的边界，也没有把未运行链路标成通过。官方C/C1启动命令是合法示例入口，但必须先有确切匹配资产与依赖。

需要修订以下内容（原指南文件保持不变）：

1. **PMFS与GMRF风消息接口不同。** 固定PMFS commit `4e141e1` 的 `Algorithm::windCallback` 接收TO，做TF旋转，不加π。固定GMRF commit `2ec7a5d` 的 `sensorCallback` 把输入当FROM，做TF后加3.14159。指南建议map/TO对PMFS可以成立，但不能将同一消息直接发给这种GMRF；否则输出方向会反转。必须分别冻结两个consumer的约定、话题和实际安装版本。
2. **GMRF还有观测位置问题。** 同一GMRF回调通过 `lookupTransform(target map, msg.frame_id, msg.stamp)` 取得x/y。若消息frame_id就是map，TF为map→map、平移为0，观测会被放到(0,0)，而不是无人机位置。TO/FROM正确还不够。保留实际传感器frame+TF、分开转换话题，或明确采用接受map下TO角和显式x/y的服务接口；后一种是新的工程桥接，不声称作者原生模块。表格推导只审静态源码，尚未执行四方向端到端ROS验收。
3. **5次/停留不是通用协议。** 它是当前官方示例的maxUpdatesPerStop。StopAndMeasure测量窗口、source update调度与每场景有效参数必须完整解析；不能与10条raw读数或一次CSV更新混为一谈。
4. **C*阈值换算限定S2旧协议。** 0.1×0.00015630356234114871=0.000015630356234114872，在该映射成立时能保留旧检测谓词。它不是作者B1/C1论文ppm阈值；更不能把规范化示踪剂假定为已标定真实气体。S2 demo实际读取布尔事件，单位/阈值发生在上游，仍需上游抽取脚本与数据合同证明。
5. **2026 humble锚点及静态环境检查不是2024论文复现。** 示例入口正确，但C1 YAML覆盖记录步数300、最大预热800、初始探索5；要使用解析后的值。包索引存在或缺失是该次source环境的记录，不表示所有安装都不存在，也不证明当前链路可运行。

证据：`source/guide_official/.../Common/Algorithm.cpp`，`source/gmrf/gmrf_node.cpp`，`source/gaden/simulated_anemometer/src/fake_anemometer.cpp`及原指南的预检JSON。GMRF静态四方向表见 `WIND_INTERFACE_STATIC_TRUTH_TABLE.csv`。这些源码接口发现不能直接升级为H02历史进程已证实的工程根因，因为实际加载模块哈希仍缺。

官方可核对链接：[PMFS回调](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/gsl_server/src/gsl_server/algorithms/Common/Algorithm.cpp)、[GMRF回调](https://github.com/MAPIRlab/GMRF-wind/blob/2ec7a5db7bf5f2597e9d62ba662d3efcfc788d71/gmrf_wind_mapping/src/gmrf_node.cpp)。
