# 气体域隔离补丁独立代码审查

判决：`PASS_READ_ONLY_CODE_AND_FROZEN_INPUT_REVIEW_NOT_RUNTIME_PARITY`。

本次只读审查 `candidate_domain.cpp`、`Simulations_gas_domain.cpp`、`GasDomain.hpp`、`M3Audit.hpp` 与冻结域/风输入；没有新增编译、前向、GADEN或ROS。四个源文件哈希均与 `DOMAIN_BUILD_RESULT.json` 保存的构建源哈希相同。当前构建可执行文件记录SHA256为 `c6ba8271fd7d200dbd9565cb116059773aa41105ac8fb688705b7fe3cf4481a6`，该值来自已有构建记录，不是本审查重新构建。

实际代码边界核验：

- 运动原点、终点和fallback路径三处freeAt（隔离核417、424、465行）均查询独立GasDomain支持。
- entry仍在原nav图上`simulation.initializeMap(image)`（87行）；gas mask未交给候选树、源支持或freeSpaceMask。gas visibility单独以原range5及原`GridUtils::PathFree`生成（113–121行），只供候选运动使用。
- 记录循环在非nav格可以累计临时计数并记审计计数器；循环结束保持navfree格除原timesteps，并将全部非nav格精确清0（394–395行）。函数返回后才执行`before_blur`和原生blur，未归一化off-nav计数不会回灌到合法观察格。
- 没有在非nav格continue掉运动。所有颗粒仍执行原move、出界删除和Gaussian随机读取。新增审计函数只调用nav路径谓词计数，没有修改位置、地图或随机初态。
- entry强制精确点与native壁面规则，显式拒绝wallSlide=true（137–142行）；原生200步、dt、noise、D和blur参数检查保持冻结。
- 独立读取1530行新旧输入确认：447个原navfree格风值逐字一致；全部1530格除u/v外的字段逐字一致。新增1083个非nav风值按预注册columnmean规则延拓。baseline无法进入非nav格，因此这些延拓值不改变其已使用的运动核。

重要解释边界：本次columnunion掩码中1530/1530格均为gasfree，而观测/score候选支持仍为447格。这是气体域投影上界oracle，实质允许跨越所有原平面障碍；可能连接实际不同高度、不可连通的三维自由层。该对照可检验“固定投影运动域+预定风延拓”是否足以改变本次源偏好，不能代表恢复真实三维物理，也不能作为部署方法的定位成绩。

补丁的静态隔离合同通过；执行资格仍依赖原计划的两个 `gas_domain=native_nav` 禁用干预锚点与既有前向逐层数值一致。两个锚点不通过则停止后续四个scientific调用。记录实际预热时长、释放数、运动域外停留和首次差异；域改变后的自适应预热变化不能被隐藏。所有结果都应保留，不追加域/高度/seed搜索。

完整数值/哈希审查记录保存于 `DOMAIN_PATCH_INDEPENDENT_REVIEW.json`。本审查没有依据定位结果给补丁打分。
