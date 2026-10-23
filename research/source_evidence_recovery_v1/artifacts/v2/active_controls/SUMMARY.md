# V2 主动消融接口执行收据

状态：PASS_ALL_FIVE_ENGINEERING_CONTROLS

固定单个制造环境、固定学生与种子；仅检查各独立控制是否真实进入闭环。不能据此主张主动定位增益。

| 控制 | 进程退出码 | 超时 | 观测数 | 反证检验数 | full-EIG fallback | MAP误差（仅本例） |
|---|---:|---|---:|---:|---:|---:|
| m2_Aprime__m3_Aprime | 0 | False | 9 | 0 | 3 | 2.8284271247461903 |
| m2_B__m3_Aprime | 0 | False | 9 | 0 | 3 | 2.8284271247461903 |
| m2_Bprime__m3_Aprime | 0 | False | 9 | 0 | 3 | 2.8284271247461903 |
| m2_Aprime__m3_Bprime | 0 | False | 9 | 0 | 3 | 2.8284271247461903 |
| m2_Bprime__m3_B_cluster | 0 | False | 9 | 0 | 0 | 2.8284271247461903 |

完整 Bprime+Bprime 已由另一独立运行保存在 artifacts/v2/active_demo，本脚本未覆盖。
各组的 argv、stdout、stderr、实际退出码、时间和原 CLI 收据均保留；所有方法差异仍只代表本例工程行为。
