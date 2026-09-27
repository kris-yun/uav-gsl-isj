# AOD House03 F0 — preregistration freeze only

Date: 2026-09-27

Input implementation review SHA256:
`b43e27a141c1ac6e732fa150516b35c4605dc7c5c6e1b8ad281ccf28d969f7d6`

This is **NOT** a scientific run.

Purpose:
freeze all choices that could otherwise be influenced by fresh House03 gas
outcomes before generating any new GADEN plume:

1. 12 House03 source candidates = 6 predeclared 0.30 m neighbour pairs;
2. two source-blind feasible 10-step single-UAV-like probe paths;
3. House03 wind contract;
4. one fixed transport-mismatch diagnostic;
5. candidate-template forward budget and seed matrix;
6. the exact objects that the later F1 gate will evaluate.

Forbidden in F0:
- no new GADEN plume;
- no new PMFS scientific forward bank;
- no House03 concentration target;
- no source-score/rank inspection;
- no change to u/rawu/B2;
- no neural model;
- no closed loop.

The OPEN implementation remains:
`research/amplitude-operator-decoupling-v0-20260927`
final `25803d287aa299f78a06458e37437a91c3fa3890`.
