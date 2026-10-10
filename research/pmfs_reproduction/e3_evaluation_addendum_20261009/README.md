# E3独立评价补充包

先读E3_EVALUATION_CRITERIA_ADDENDUM_zh.md及E3_POST_RESULT_EXIT_REVIEW_zh.md。原E3包不变，本包只含解释补充、冻结数据副本、只读核验结果和算术复算，不含新ROS实验。

默认只读核验（Python + numpy）：

```text
python verify_e3_addendum.py
```

核验范围：本包manifest、原证据副本血统、top5选格与加权位置、官方结果、原判决保留、关闭时序、当前只读VM记录。原生全部候选传播图与评分的复核应使用原E3 ZIP中的verify_e3.py；本包附其此次默认只读执行结果，不声称小补充包复制了全部原生模拟资产。

可选复核排序：在与记录相同的libstdc++环境中编译top5_sort_review.cpp，然后分别读取top5_inputs/update_0.csv与update_1.csv。C++只做排序/加权坐标算术，不使用ROS、随机状态或传播模拟。跨标准库的并列格顺序可能不同，应比较版本并保留差异，不能将其当作新的定位结果。

```text
g++ -std=c++17 -O2 top5_sort_review.cpp -o top5_sort_review
./top5_sort_review top5_inputs/update_1.csv
```

原E3审核ZIP及提交的身份、SHA256在ORIGINAL_E3_PRESERVATION.json；公开论文版本/章节和出处在PAPER_EVIDENCE.json。B4尚未获本轮执行授权。
