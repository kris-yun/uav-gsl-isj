# 外部保护器与启动接口修正

修正均位于隔离运行器，未重新编译 PMFS 核心。

1. 删除从发送 goal 起累计 300 模拟秒的外部搜索截止；官方搜索计时仍归 PMFS 初始化后的 startTime 所有。独立 monotonic 墙钟 345 秒、停钟、进程与资源保护保留；Action future 在同时到达的保护事件之前优先处理。
2. 客户端时钟积压只记为未资格化的观测警告，不能自动判为播放器跳变。实际时钟断续另行核验；真实停钟仍受墙钟保护。
3. 气体/风场记录代理等待两项后端服务就绪后再开放。真实 ROS 延迟后端测试通过，首个请求和响应保留字节一致；正式 B4 的原生 PID 已持续产生读数。
4. 参数记录使用指定节点的 list_parameters/get_parameters ROS 服务，并持续 spin，不依赖 CLI daemon 的节点列表。真实 ROS 中四次参数读取、持续时钟、实际积压与实际停钟测试通过；正式运行捕获 GSL 51 项和播放器 21 项生效参数。
5. Nav2 生命周期管理器显式绑定 /PioneerP3DX。正式 goal 前五个 Nav2 节点均 active，原生地图、TF、PID、风场查询及传感器消息时间检查通过。

本轮的三个失败启动检查均发送 0 个 goal，证据分别保存在 preflight_cli_discovery、preflight_nav2_map、preflight_lifecycle_namespace。不得把它们作为算法定位失败。为诊断 Nav2 曾加入延迟 TimerAction，真实日志显示该派生写法使管理器落到根命名空间，等待 /map_server/get_state，而实际服务在 /PioneerP3DX；随后撤回延迟写法，恢复原启动顺序，并显式绑定命名空间。这个临时写法的问题属于本轮启动脚本，不能归咎于上游科学模型。

保留 14 项离线保护测试和真实 ROS 集成证据；测试 fixture 未进入正式 PMFS 输入。后续不要再使用过期的 nav2_ordered_launch.py 或 CLI 参数记录版本；正式执行文件以 run/runtime_driver.py、run/N1_B4_launch.py、run/nav2_explicit_namespace_launch.py 为准。
