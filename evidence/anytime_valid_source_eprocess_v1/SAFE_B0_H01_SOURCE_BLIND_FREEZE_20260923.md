# SAFE-B0 source-blind freeze — House01 seed0 corrected R1

Date: 2026-09-23  
Branch: \`research/anytime-valid-source-eprocess-v1\`  
Truth inputs read for this computation: **NO**  
Source archive: corrected R1 raw tar from \`research/native-pmfs-baseline-recovery-v1\`.

## 1. Schema freeze

Raw event stream:

- 20 HIT/MISS events;
- 4 robot stops;
- exactly 5 events per stop;
- 19 MISS, 1 HIT;
- unique HIT is event 18;
- grid 29 × 38 = 1102 cells;
- 87 candidate source regions;
- every candidate \`.f32\` map has 1102 float32 values.

Stops:

1. grid (14,20): events 1–5;
2. grid (6,23): events 6–10;
3. grid (4,6): events 11–15;
4. grid (11,24): events 16–20.

Event → map indexing is row-major:

\[
\text{cell index}=\text{robot\_j}\cdot29+\text{robot\_i}.
\]

This agrees with the measured-map export.

## 2. Official C-arm predictions at the 20 observed events

Across 20 × 87 candidate-event predictions:

- min = 0;
- median = 0.00044799214811064303;
- 90th percentile = 0.9873055219650269;
- max = 0.9999366402626038;
- exact-zero fraction ≈ 0.4252873563.

Thus the official candidate forward family is highly polarized at these four sampled cells. This makes a point-null e-process potentially very powerful but also highly brittle to model mismatch.

## 3. B/C cross-contract discrepancy at observed cells

Absolute \(|h_B-h_C|\) across candidate-event pairs:

- median = 0.00044799214811064303;
- 75th percentile = 0.09323996119201183;
- 90th percentile = 0.4902759790420532;
- max = 0.9884304404258728.

The B/C envelope is therefore a strong stress test, not a calibrated uncertainty interval.

## 4. Source-blind replay definition

For every source candidate \(s\), event \(t\):

\[
q_{s,t}
=
\frac{1}{86}
\sum_{r\ne s} h_{r,t}^{C}.
\]

This is a fixed uniform mixture over all other official-C candidate predictions and uses no observation history or truth.

At \(\alpha=0.05\), a candidate is permanently rejected once

\[
\log E_t(s)\ge \log20.
\]

Predeclared null variants:

- point: \(I_{s,t}=\{h^C_{s,t}\}\);
- absolute envelopes \(\delta\in\{0.025,0.05,0.10,0.20\}\);
- B/C envelope:
  \[
  [\min(h^B,h^C),\max(h^B,h^C)].
  \]

Predeclared event-stream variants:

- all 20 events;
- first event per stop;
- last event per stop;
- middle event per stop.

No arm was selected using truth.

## 5. Source-blind contraction results

| Stream | Null | Final survivors / 87 | Key event |
|---|---|---:|---|
| all | point | **1** | event 18 HIT collapses 49→1 |
| all | ±0.025 | 49 | no contraction at event 18 |
| all | ±0.05 | 49 | no contraction at event 18 |
| all | ±0.10 | 49 | no contraction at event 18 |
| all | ±0.20 | 50 | no contraction at event 18 |
| all | B/C envelope | **5** | event 18 HIT collapses 67→5 |
| first/stop | point | 60 | all 4 retained events are MISS |
| first/stop | B/C envelope | 81 | all MISS |
| last/stop | point | 60 | all 4 retained events are MISS |
| last/stop | B/C envelope | 81 | all MISS |
| middle/stop | point | **2** | event 18 HIT collapses 60→2 |
| middle/stop | ±0.025 | 51 | HIT removes 17 |
| middle/stop | ±0.05 | 60 | HIT removes 11 |
| middle/stop | ±0.10 | 74 | HIT removes 0 |
| middle/stop | ±0.20 | 87 | no candidate rejection at all |
| middle/stop | B/C envelope | **18** | event 18 HIT collapses 83→18 |

Important source-blind interpretation:

- the point null has extreme power but is likely fragile;
- uniform absolute widening destroys the information content of the single HIT quickly;
- the structured B/C envelope retains substantially more power than a broad uniform interval;
- apparent all-event power must not be confused with independent evidence because five correlated/repeated events are collected at each stop;
- middle-per-stop is particularly informative here because it retains the unique HIT without using multiple events from the same stop.

## 6. Frozen survivor bitmasks

Candidate order is lexicographic:

\`\`\`text
0 quadtree_10_32_5_4
1 quadtree_10_36_2_1
2 quadtree_11_1_3_4
3 quadtree_11_5_4_5
4 quadtree_12_19_5_5
5 quadtree_12_24_5_4
6 quadtree_12_36_5_1
7 quadtree_13_14_5_2
8 quadtree_14_18_3_1
9 quadtree_14_1_2_2
10 quadtree_14_31_1_1
11 quadtree_14_4_3_1
12 quadtree_15_10_1_2
13 quadtree_15_31_5_1
14 quadtree_15_32_2_4
15 quadtree_15_5_3_5
16 quadtree_16_10_1_4
17 quadtree_16_2_1_2
18 quadtree_17_10_1_2
19 quadtree_17_26_2_2
20 quadtree_17_32_4_4
21 quadtree_17_3_1_2
22 quadtree_18_14_1_2
23 quadtree_18_36_2_1
24 quadtree_19_14_1_1
25 quadtree_19_15_2_4
26 quadtree_19_19_2_4
27 quadtree_19_25_1_2
28 quadtree_19_27_2_2
29 quadtree_1_10_5_4
30 quadtree_1_18_1_4
31 quadtree_1_1_5_4
32 quadtree_1_22_5_5
33 quadtree_1_27_5_2
34 quadtree_1_5_3_5
35 quadtree_20_10_1_5
36 quadtree_20_1_5_2
37 quadtree_20_23_1_4
38 quadtree_20_29_1_3
39 quadtree_20_3_1_2
40 quadtree_20_5_4_3
41 quadtree_20_8_2_2
42 quadtree_21_14_2_2
43 quadtree_21_25_1_4
44 quadtree_21_33_4_1
45 quadtree_21_34_5_3
46 quadtree_21_4_2_1
47 quadtree_22_25_2_2
48 quadtree_22_27_4_2
49 quadtree_23_14_1_3
50 quadtree_23_3_1_2
51 quadtree_24_12_2_5
52 quadtree_24_25_1_1
53 quadtree_24_26_5_1
54 quadtree_24_3_2_5
55 quadtree_25_1_1_2
56 quadtree_26_14_2_3
57 quadtree_26_1_2_4
58 quadtree_26_27_2_2
59 quadtree_26_35_2_2
60 quadtree_26_5_2_3
61 quadtree_28_27_1_1
62 quadtree_2_18_3_1
63 quadtree_2_19_5_3
64 quadtree_2_31_3_1
65 quadtree_2_32_4_4
66 quadtree_2_36_5_1
67 quadtree_4_5_4_5
68 quadtree_5_29_1_3
69 quadtree_6_10_2_3
70 quadtree_6_13_2_3
71 quadtree_6_1_3_1
72 quadtree_6_22_2_5
73 quadtree_6_27_1_2
74 quadtree_6_2_2_3
75 quadtree_6_31_1_5
76 quadtree_7_20_1_2
77 quadtree_7_27_1_1
78 quadtree_8_14_5_2
79 quadtree_8_19_4_5
80 quadtree_8_24_4_4
81 quadtree_8_2_1_2
82 quadtree_8_4_1_5
83 quadtree_8_9_1_5
84 quadtree_9_18_5_1
85 quadtree_9_31_5_1
86 quadtree_9_32_1_3
\`\`\`

Encoding: each hex nibble stores four candidate bits little-endian within the nibble; bit 1 means final survivor.

\`\`\`text
all:point         0000800000000000000000
all:delta0.025    f4effb818fbffff3000006
all:delta0.05     f4effb818fbffff3000006
all:delta0.1      f4effb818fbffff3000006
all:delta0.2      f4effb818ffffff3000006
all:BC            0200800000000000608000

first:point       f6effff98ffffff3084066
first:delta0.025  feeffffbcffffff38e44e6
first:delta0.05   feeffffbcffffff38e44e6
first:delta0.1    fffffffbcffffff38e44e6
first:delta0.2    ffffffffcffffff78e44e7
first:BC          feffffffefffffff7fe7e7

last:point        f6effff98ffffff3084066
last:delta0.025   feeffffbcffffff38e44e6
last:delta0.05    feeffffbcffffff38e44e6
last:delta0.1     fffffffbcffffff38e44e6
last:delta0.2     ffffffffcffffff78e44e7
last:BC           feffffffefffffff7fe7e7

middle:point      0200800000000000000000
middle:delta0.025 f6effb818ffffff3000006
middle:delta0.05  f7fffbbd8ffffff3084026
middle:delta0.1   ffffffffcffffff38e4cf7
middle:delta0.2   fffffffffffffffffffff7
middle:BC         021080042000000c71ab11
\`\`\`

## 7. Freeze statement

All event-schema, prediction extraction, null choices, stream variants, survivor counts, and final survivor bitmasks above were computed **without reading the R1 runtime manifest or truth coordinate during this SAFE-B0 computation**.

Truth membership is evaluated in a separate post-freeze step.

Status:

\`SAFE-B0 SOURCE-BLIND FREEZE COMPLETE\`.
