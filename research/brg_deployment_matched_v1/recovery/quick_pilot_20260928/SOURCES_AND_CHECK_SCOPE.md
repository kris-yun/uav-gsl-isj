# 来源与本轮检查范围

- 输入暂停包：BRG_V1_PAUSED_REVIEW_20260928.zip，SHA256 17171e8f552db7e284e1dcd466ba8075850a4299998cdc15636a0e8ef5548722。470项外层文件清单逐项核验。
- 三环境样本包：SHA256 0f0df96d569ee742327b7e9c95774b3a3f10b920f552b4b01ddbb5065574f657；8项内部清单核验，仅查看选择/receipt元数据，不将样本作为独立评价。
- 读取52条episode元数据与特征数组，重计事件数、更新mask和窗口；没有计算源排名或训练任何模型。
- 解码两个已有VGR原始日志归档（同一013案例Native与V3），检查runtime flags、source_update_complete记录和goal trace；没有运行VGR或读72条全数据。
- 读取train_v1_gpu.py、encode_v1_episode_vm.py、V3导航代码、原eval8与split/cost合同。
- 新trainer只增加明示的Native-only模式；AST检查及隔离数据loader实际读取40/8条成功，旧warm模式仍拒绝缺coverage的manifest。未运行网络、GPU、优化器或ROS。评价调度新入口尚需Codex绑定，不冒称本包已完成VM接入。
- 方法学参照：Ross, Gordon & Bagnell (2011), A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning. https://proceedings.mlr.press/v15/ross11a.html 。这里只用于说明行为影响后续输入分布；本pilot不是DAgger复现，没有模仿动作或援引其保证。
