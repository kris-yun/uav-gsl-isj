# C4源—受体响应归因交付

先读`study/科学裁决_zh.md`与`study/results/FINAL_DECISION.json`。结论为HOLD：普通随机重复、统一0.25米细化、正确面积似然边际化、精确点oracle都未救回C4末次判别；预热时长收敛、PID事件算子、二维/三维传播尚未分离，不宣布主创新或唯一物理根因。

这是一份固定真实观测历史的离线前向归因包。没有新ROS回合、新气体世界或候选方法闭环收益。C4/C3来自修风后的2026实现开发世界，并非作者论文原始轨迹。新候选使用地图、实际输入风及历史接触图，不读取源真值；精确坐标只在单列oracle与事后指标使用。

包中内容：

- `study/code/`：实际执行的C++原生二维前向核及普通区域/细格控制；对应原生函数与SHA在lineage。
- `study/oracle_code/`：单列事后精确点诊断。不能进入算法对比或被当成可部署方法。
- `study/readout_code/`：原生C++均值、Top-5%、全概率方差计算。
- `study/results/analysis/SOURCE_POSTERIOR_METRICS.csv`：57组完整定位读出；`SOURCE_RECEIVER_RESPONSES.csv`：83,918行逐源逐受体原始与模糊响应。
- `study/results/predictions/`：全部冻结随机状态的原始/模糊图、逐源评分、RNG前后状态、气团更新数与CPU/墙钟。
- `study/results/ORACLE_EXACT_POINT_RESPONSES.csv`、早期更新、C3正常控制及技术失败均保留。
- `study/results/NATIVE_TRUE_SOURCE_FORWARD_HORIZON.csv`与`OBSERVATION_PHYSICAL_AGE.csv`：预热规则与物理时间线索。年龄差不证明短预热必然无效。
- `evidence/native_histories.zip`：完整C4/C3原始闭环记录、全部候选/释放点/高斯缓存、连续未阈值PID CDR、消费窗口、配置、必要静态三维占据与风文件。不是完整20世界包，没有把全部气体世界复制进来。
- `study/EXECUTION.json`、`ORACLE_EXECUTION.json`、logs/、冻结文件与输入SHA：命令、退出码、成本和全部工具问题。

数值依赖：Linux、GCC 11.4.0、CMake 3.22.1、OpenCV C++ 4.5.4、Python、NumPy 1.26.4；原包复算另需SciPy。已有SciPy发行版对NumPy版本有声明警告，未影响本次已实际执行的复算；前向仿真和空间模糊实际由C++/OpenCV执行。分析模式的C++读出不需要OpenCV或ROS。其他编译器/库版本须重新检查浮点与排序差异。

解压外层包后：

```bash
python reproduce.py --verify-only
python reproduce.py --out /tmp/c4_analysis_new
python reproduce.py --out /tmp/c4_forward_new --forward-check
```

默认第二条只重算已保存预测的所有分析表，第三条从源码编译并重放293组历史候选，再复核一组冻结的518源细格计算；它仍是固定历史重放，不是机器人闭环。输出目录必须是全新目录，保留首次失败。需要自行提供以上常规编译依赖。`prepare.py`保留最初提取/冻结过程作血统记录，默认复算使用包内已经冻结、校正并实测的源码与fixtures。

评分是原生全图评分，不被宣称为经校准的PID伯努利概率。平均响应后评分和面积似然边际化分开导出。两臂每次各518次模拟与共同上限相同，实际工作量和CPU约有3%以内差别，不能称精确等CPU。三组预测状态不等于三个独立真实世界。C4两次更新中的相同前向条件也不能人为增加独立样本数。

下一项仅建议检验原生二维前向预热/记录时长是否收敛，先排除普通数值偏差；本包没有自动启动该项，也未开发世界模型、RL或其他主创新模块。

官方代码血统：MAPIRlab/GasSourceLocalization，2026源码针`4e141e162551e674f2f30ddb8859136c72139aac`，上游来源为https://github.com/MAPIRlab/GasSourceLocalization 。保留上游作者归属；本包不重新许可上游代码。
