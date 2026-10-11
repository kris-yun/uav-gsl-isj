# 气体域投影单项对照：补丁边界检查

只读源码检查，未编译或执行新的前向。父任务拟将运动自由支持由原生二维导航支持替换为“原三维自由体素的高度柱union”，并以预先固定columnmean风作延拓。该支持是oracle诊断：不同高度的自由段可能在XY投影中产生实际三维不可通行的虚假连接，不能部署为已经验证的新算法。

需要严格拆开的对象：

| 对象 | 本对照处理 |
|---|---|
| 候选源、观测图、score支持 | 保持原447个navfree格 |
| `moveAlongPath`原点/终点/路径自由谓词 | 用独立gasfree mask替换，位置是锁定源码407、413、453行 |
| 运动visibility shortcut | 原range5、原`GridUtils::PathFree`算法，在gas mask上单独重建；只给move使用 |
| 测量传播visibility | 冻结原nav visibility，不能改变50块观测生成的地图 |
| source tree与freeSpaceMask | 冻结原nav；不要调用`PMFSLib::InitializeMap`来安装gas mask，因为它还会Prune、改树和blur mask |
| 场读取 | 只在navfree格累计centre-hit，再除原200步；在blur前非nav格精确为0 |
| blur及score | 固定原navfreeSpaceMask、sigma和447格评分 |
| 风延拓 | 先冻结完整1530格columnmean表；其447个navfree值须逐位等于已完成columnmean分支 |
| 边界删除/壁面步法 | 原生算法与原二维metadata不变；union不等于另行引入滑移或三维出口 |

关键风险是原生统计只对navfree格除以 `timesteps`（源码379–384行）。允许颗粒进入新gasfree但navnonfree格后，若仍给那些格累计原始计数，再直接blur，会将未归一化的大整数扩散到观测格，造成第二项读出修改。应当只屏蔽count或在blur前清零；**不要在非nav格直接continue整个颗粒循环**，那会跳过move、删除检查及随机数消耗，改变运动和RNG。

旧nav visibility对新增gas路径是保守/空映射，不能当作已对齐的gas visibility。若仍沿用旧表，可见路径被迫走floor残步的fallback，产生额外实现混杂。另建gas-only visibility采用相同算法，mask差异才是有界输入干预；无需重建候选树。

新增可达格需要风值。把预先定义的columnmean公式延拓到非nav格是该oracle域的必要模型合同。应同时冻结整张表并证明baseline轨迹无法进入这些新增格、原nav值不变；不能把这次结果宣传成“只改一行mask就恢复了真实三维运动”。实际预热停止仍由原生首次出界/min200/max500逻辑决定，记录有效预热步数与总释放数；若随域变化，这属于干预后的中介变化，不能隐藏并声称有效模拟预算逐项相同。

如发现补丁改变候选支持、测量传播、blur mask、score格、浮力、随机初态或原壁面步法，应停止把它解释成单项气体域对照。判决只针对这一次固定路径/候选/观测的原语鉴别，不增加定位闭环。
