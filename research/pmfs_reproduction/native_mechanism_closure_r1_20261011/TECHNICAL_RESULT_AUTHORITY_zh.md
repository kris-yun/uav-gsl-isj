# 主结果与技术影子分支

主原生结果：QUALIFIED_N0_COMPLETE_MAP_RESULTS.csv、QUALIFIED_FRESH_N0_COMPLETE_MAP_RESULTS.csv，RAW/support/native全部18条历史。主点源：QUALIFIED_N_POINT_*。NATIVE_*无QUALIFIED前缀及N_POINT_*为初始化修正前技术影子，保留以解释修复，不计主要端点。原历史E3/B4冻结成功及错误收敛并未变化。

第一次薄入口错误在于把未初始化相位0与预加载缓存结合；原算法Gaussian懒初始化发生在初始释放之后，相位19。修正冷入口只恢复原Uniform状态并由原函数按原顺序初始化。冷锚点包括图、释放点、初始缓存/顺序、RNG与评分全匹配；10点图的ready初态明确。

OTHER技术问题：代码include路径、序列化列名、HGFS不支持symlink、资源计数重复CFD副本、协调器错误消息的路径字符串替换。相应原日志与修复源码保留。新物理气体38次均合格，无新物理重试，无通过更换种子救结果。

核验脚本为只读Python、NumPy；不得自动运行包中实验启动脚本或未知二进制。接下来等待独立审核，不启动新的实验。
