# 经典基线对比结果 (初步)

## PMFS (TRO 2023)
| House | Seed 0 | Seed 1 | Seed 2 | Median |
|-------|--------|--------|--------|--------|
| House01 | 2.997m | 3.094m | 3.094m | 3.094m |
| House02 | 6.772m | 5.242m | 5.242m | 5.242m |
| House03 | 5.517m | 6.269m | 6.269m | 6.269m |
| **Overall** | | | | **5.242m** |

## GrGSL (MAPIRlab)
| House | Seed 0 | Seed 1 | Seed 2 | Median |
|-------|--------|--------|--------|--------|
| House01 | 3.659m | 4.178m | 4.178m | 4.178m |
| House02 | 7.312m | 3.556m | 6.532m | 6.532m |
| House03 | 2.208m | 7.646m | (running) | ~4.9m |
| **Overall** | | | | **~4.2m** |

## CP-SBD-GSL Full
| House | Seed 0 | Seed 1 | Seed 2 | Median |
|-------|--------|--------|--------|--------|
| House01 | 1.574m | 1.015m | 1.130m | 1.130m |
| House02 | 1.616m | 1.690m | 1.983m | 1.690m |
| House03 | 1.294m | 1.244m | 1.333m | 1.294m |
| **Overall** | | | | **1.333m** |

## 总结
| 方法 | 中位数(m) | vs CP-SBD-GSL |
|------|----------|---------------|
| **CP-SBD-GSL** | **1.333** | — |
| GrGSL | ~4.2 | 3.1x worse |
| PMFS | 5.242 | 3.9x worse |

CP-SBD-GSL 在所有 3 个 House 上都显著优于经典方法。
PMFS 和 GrGSL 在某些 House 上超时 (300s+)。