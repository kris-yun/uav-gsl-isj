# House02 one-file wind conflict forensics

The sole nonidentical common relative path is `4,5-3_fast/4,5-3_fast_5.csv`.

| | A, original launch tree | B, nested tree |
| --- | ---: | ---: |
| Size | 3,735,552 bytes | 9,769,492 bytes |
| SHA256 | `8e149af89072cc59964e55b51b5b94c11d936e28f0f04dfb6b68497750315484` | `d00dcaeaec2567b2305c677aaf6983644751ce67a99b81485206304cd6f014b2` |
| mtime UTC | 2026-07-11 05:22:42 | 2021-10-14 04:28:46 |
| CSV records including header | 67,183 | 180,751 |
| Bad six-column rows | 1, the final partial row | 0 |
| Ends in newline | no | yes |

Byte comparison finds **zero differing bytes in the overlapping 3,735,552-byte prefix**: A is an exact prefix of B. The first divergence is A's EOF at offset 3,735,552; B has a further **6,033,940 bytes**. A's final record stops after three fields. B's header and all 180,750 data records have six columns, matching the other complete `4,5-3_fast` CFD text files. The format counts are in `CONFLICT_CSV_FORMAT.tsv`; exact lengths, hashes, prefix and difference offsets are in `A_B_SUMMARY.json` and `COMMON_DIFFERENT.tsv`.

The A state-5 `_U/_V/_W` companion files are absent, while B has all three. The concatenation of B's three binary component payloads equals the original House02 `4,5-3_fast` gas run's saved `wind_iteration_5` by SHA256. All other 43 B state payloads likewise match their historical saved winds. The original saved wind is a witness for the numeric field; it does not contain the CFD text itself. No independent complete CFD-text third copy was located.

**Conclusion: `H02_CONFLICT_B_SUPPORTED`.** The different SHA is explained by byte truncation, not by differing overlapping values or evidence of another wind realization. B supplies the full text file and the historically verified state-5 numeric components. Preserve the truncated A file as evidence; a future reconstruction must select B in a separate staging tree, with its SHA recorded. This conclusion does not authorize editing A or launching GADEN.
