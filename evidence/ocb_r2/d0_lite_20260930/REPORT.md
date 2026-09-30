# D0-Lite single-case zero-shot replay
Decision: `D0_LITE_ZERO_SHOT_TRANSFER_POOR`

Run: `ocb_r2_cfg00_r01`; House01 / 1,3-2,4_fast; immutable GADEN seed 2026900001.
Truth XY [-0.6, 1.95]; Native top5% XY [-1.4079720973968506, 2.148707628250122]; error 0.832048 m.
Native termination declared_success; final available belief at 258.200000 s, maximum budget300s.
80 completed events; 36 hits; 8 unique encounter pixels.

| checkpoint | channels | centroid XY | XY error m | peak error m | inference s |
|---|---:|---|---:|---:|---:|
| unet_model_final.pth | 2 | [-3.1691036146151133, -2.083097891682277] | 4.781859 | 9.707904 | 0.476846 |
| unet_model_final_1.pth | 3 | [-3.1214599213690324, -3.123193268859997] | 5.665249 | 9.655227 | 0.048443 |
| unet_model_final_2.pth | 3 | [-3.126880190255288, -1.735301770890862] | 4.468397 | 4.108455 | 0.049859 |
| unet_model_final_3.pth | 3 | [-3.206624333371412, -1.4797944588326724] | 4.307897 | 4.692483 | 0.052974 |

No primary/best checkpoint selected. Four checkpoint outputs are retained; two-channel semantic ambiguity remains explicit.
No training, no new GADEN, no second case, no confirmation/H03. Formal logger OFF/ON parity was waived for this engineering pilot; D1A remains paused.
This single-case screen does not establish U-Net superiority or deep-learning failure. Native consumes full-field state0 forward wind; U-Net receives encounter-local measured wind only.
STOP after packaging.
