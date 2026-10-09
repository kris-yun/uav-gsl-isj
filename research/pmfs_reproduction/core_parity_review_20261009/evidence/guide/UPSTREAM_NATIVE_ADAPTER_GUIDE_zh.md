# 怎样使用公开PMFS的原生接入流程

**官方已有ROS2/GADEN机器人示例接入，入口包为`pmfs_env`；没有发现即插即用的枫树岭三维AGL无人机适配器。** 当前`s2_pmfs_demo.cpp`直接调用原生核，不能代替完整官方接入。

官方humble提交 `4e141e162551e674f2f30ddb8859136c72139aac`：

- [官方PMFS示例说明](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/Environment_config/PMFS/readme.md)
- [完整示例launch](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/Environment_config/PMFS/launch/main_simbot_launch.py)
- [原生ROS订阅/风向与定位回调](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/gsl_server/src/gsl_server/algorithms/Common/Algorithm.cpp)
- [原生停留测量窗口](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/gsl_server/src/gsl_server/algorithms/Common/States/StopAndMeasureState.cpp)
- [原生PMFS调度](https://github.com/MAPIRlab/GasSourceLocalization/blob/4e141e162551e674f2f30ddb8859136c72139aac/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp)

## 官方示例的用法

在依赖已安装、该官方示例环境已预处理并完成气体计算后，可以用作者提供的命令：

```bash
source /opt/ros/humble/setup.bash
source /path/to/official_ros_workspace/install/setup.bash
ros2 launch pmfs_env main_simbot_launch.py scenario:=C simulation:=C1 method:=PMFS
```

这里的C/C1是作者室内环境，不是本项目S2。本轮没有启动该示例，也没有执行readme中的preproc/sim命令。初次构建使用仓库README依赖说明，包含GADEN、Olfaction msgs、GMRF-wind、导航依赖及git submodules；在独立工作区固定上述提交，保留现有recovery工程基线。

## 原生链路与当前差异

|环节|公开原生方式|S2需要提供|
|---|---|---|
|启动|gsl_actionserver_node，gsl_actionserver_call，DoGSL goal gsl_method=PMFS|避免把CPP demo二进制当官方server|
|定位|PoseWithCovarianceStamped，robot_location_topic|实际ENU xy姿态与时戳；独立map→UAV/传感器TF含真实z|
|气体|olfaction_msgs/GasSensor，经ppmFromGasMsg；默认PID/Sensor_reading|官方模拟PID服务查询真实xyz，输出等效ppm；禁止把C*伪标ppm|
|风|olfaction_msgs/Anemometer，经TF变换；默认Anemometer/WindSensor_reading|明确map中TO角、rad与m/s，含实际传感器高度|
|地图|OccupancyGrid/Nav2 map/costmap，原生GetMapMetadata按scale降采样|S2三维航空自由空间的二维可行性投影；记录降采样占据规则，不能套地面可行地图|
|测量|StopAndMeasure按窗口平均浓度/速度、圆平均方向|日志保存raw采样、时间窗口与native实际输入；保留原生5次/停留协议，不能逐CSV直接替代|
|概率更新|每若干原生移动迭代触发源概率update|记录native真实触发次数与内部风；不是末尾一次调用|
|导航|PMFS MovingState通过二维NavigateToPose规划/执行|UAV的高度跟随和执行动作需桥接，明确这是新工程接口|
|评估|PMFS方差终止；GT用于navigationTime/最终误差日志|封存后独立评估；额外abstain属于项目评价协议|

## S2迁移时必须处理的三个具体接口

**1. 风向。** 原生内核与Algorithm回调按downwind TO解释。当前公开GADEN模拟风速计`use_map_ref_system=false`分支发布传感器FROM；`true`分支直接atan2(v,u)并frame=map。S2接入宜显式true、fixed_frame=map；保留/冻结噪声协议。先用(u,v)=(1,0),(0,1),(-1,0),(0,-1)验证端到端角0,π/2,±π,-π/2，不凭箭头目视猜方向。该选择是接口语义固定，不是为定位成功搜索风向。

**2. 浓度单位。** 官方PID30返回服务浓度之和（use_PID_correction_factors=false时），GasSensor使用UNITS_PPM时原生回调直接读取raw。旧逻辑C*=ppm_equivalent/0.00015630356234114871，阈值C*>0.1。因此等效ppm阈值固定为0.000015630356234114872。使用官方launch默认0.1ppm会改变检测判据，应显式转换。原气体是规范化被动示踪剂，不能因为使用PID消息就声称已验证真实气体传感器物性。

**3. 三维高度。** 官方PMFSLib::InitializeWindEstimations取初始化TF中的anemometer绝对z并把同一z填到所有候选查询；这表示恒绝对高程平面。S2的20m AGL随地形改变，不能把该常z平面称20m AGL。保持干净公开推断代码可选官方GMRF估风，由实际AGL传感器观测生成二维风；也可用明示的新服务桥接把查询xy映射为ground(xy)+20，再调用真实GADEN风。两者都必须预先固定并作为新采集协议，与本轮固定44s真实风基线分开报告。没有官方现成AGL服务桥接；需要写工程代码时不能称作者原生模块。

## 已完成的运行环境预检

当前源环境能找到gsl_server、gsl_actions、pmfs_env、Nav2、gmrf_wind_mapping。当前source链不能找到gaden_player、simulated_gas_sensor、simulated_anemometer；另外旧hcmc_gaden_seed_build_20260922工作区存在gaden_player包索引，尚未验证其版本/格式与S2状态兼容。原生产GADEN使用ocb_r2_seeded_gaden库。不能据此声称完整官方链路已经可运行；应在新工作区确认包与GADEN数据格式。详见NATIVE_ADAPTER_PREFLIGHT.json及audit/RUNTIME_FINAL_INVENTORY.json。

公开GADEN humble源码提交ccb02e959a45a188e4b6c78792e197633fc64f1c已经取回传感器与服务定义；这是接口参考，不是本轮已替换原GADEN引擎。官方launch有示例环境的墙体、Pioneer机器人、传感器偏移、地图与时钟默认，不能直接把scenario字符串改成S2就宣称移植完成。

## 本轮的完成边界

原生接入路径、源码、消息/服务、依赖和S2差异已经查清并交付。A/B/C诊断、确定取风修复与abstain已完成。完整S2原生闭环运行仍需预先冻结地图、TF、UAV执行和连续GADEN状态；按当前任务“诊断完成停止”要求，本轮不新算气体或启动CFD。此指南不把尚未跑过的官方链路标成验收通过。
