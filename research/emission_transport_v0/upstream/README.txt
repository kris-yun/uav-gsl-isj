阅读顺序：MAIN_REPORT.pdf → CODEX_NEXT_ACTION.txt → code/ → evidence/。
唯一候选：释放—输运生成泛函的全源概率求解；不新增缩写。
本轮完成数学构造和有限状态原型，未运行GADEN实验。
执行：python code/test_emission_transport.py；python code/demo_168.py。
需要numpy、scipy。运行会重写evidence中的单元检查JSON及合成演示结果（计时可能不同）。
17项通过是软件/数学验证；168合成格点不是真实168源测试。
随机算子、释放条件和观测通道必须明确，不能依赖真实部署没有的目标多源bank。
source posterior出现零可以是合法模型事件；不能加floor掩盖模型支持失配。
保留现有项目所有已冻结结论和封存环境；本包不授权新plume。
参考包只保存相关原始文本及输入hash，不重复打包大量历史资产。
