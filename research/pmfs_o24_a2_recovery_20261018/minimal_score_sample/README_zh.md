此样例取补跑A2的第一次源更新，供Pro不安装ROS复算原生全图源评分和后验。运行python3 replay_score.py；需要NumPy。它只验证保存计算，不产生新航线、观测或闭环收益。C++主程序位于recovery/source_runtime，C++原生读出复算位于recovery/native_readout_check.cpp。
