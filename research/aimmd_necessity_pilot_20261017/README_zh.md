# AIMMD路径采样必要性Pilot

先读`科研裁决_zh.md`、`analysis/DECISION.json`。实际完成900次原生二维源计算：4次逐位核验、896次普通MC预测。没有实现WE或AIMMD；本轮定位联系停止门未过，未执行同CPU20%算法比较。

资料是2026修风开发实现，在固定360秒预热＋20秒记录协议下的数值试验。没有新GADEN物理世界和ROS回合，不是2024论文精确复现、三维因果实验或新闭环收益。

包内包括完整C++源与DDA头文件、输入、全部随机表与初始状态、逐次原始/模糊图、种群事件轨迹、命令退出码、成本、所有批结果和停止裁决。`理论与移植边界_zh.md`列出原始论文链接及联合观测要求。

无需ROS，可复核已保存数据（Python3.10+与NumPy）：

```sh
python reproduce.py --verify-only
python reproduce.py --analysis-out /absolute/NEW/replay
```

默认入口不会重新模拟。`run.py`是本次有界执行记录，保留原起点、900次源调用上限和拒绝科学重复执行的保护；不要在已完成目录重新运行。C++完整前向程序可在Linux用`cmake -S code -B NEW_BUILD`、`cmake --build NEW_BUILD --target timed`构建，需要OpenCV core/imgproc与zlib。若复核者需要重新产生预测，须明确使用独立目录及自己的新预算，不覆盖本次证据。

本轮普通MC两源采用独立源预测状态，未评测共随机数对照。参考仅供误差评估，没有用于免费训练候选；MC1与MC4计算量不同，不能拿它们的误差下降当成同预算效率创新。
