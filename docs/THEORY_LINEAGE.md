# Theory lineage and the second innovation step

The method is an adaptation, not a relabeling of any single external paper.

1. **PMFS baseline.** The original PMFS work contrasts online dispersion simulations from candidate sources with a probabilistic gas-hit map designed to abstract the time-dependent plume. V10 preserves the PMFS posterior representation, planner, and official top-5% expected-location error definition. Source: [Ojeda, Monroy & Gonzalez-Jimenez, TRO 2024 / arXiv](https://arxiv.org/abs/2304.08879).

2. **Inverse cause-from-effect viewpoint.** Assimilative causal inference frames dynamic causal identification as solving an inverse problem from observed effects and explicitly targets intermittent, time-evolving systems. V10 transfers that viewpoint to gas source evidence: it scores candidate causes from observed hit/miss effects rather than requiring a candidate forward simulator to be correct. Source: [Andreou, Chen & Bollt, Nature Communications 2026](https://www.nature.com/articles/s41467-026-68568-0).

3. **Misspecification and data splitting.** Robust universal inference treats misspecification as fundamental and uses split-sample relative-fit tests to obtain inference under weak regularity. V10 does not claim its finite-sample theorem, but borrows the defensible design principle: disjoint temporal folds must each be identifying, and nuisance-model members are marginalized rather than selected using truth. Source: [Park, Balakrishnan & Wasserman, Biometrika 2026](https://academic.oup.com/biomet/article/113/2/asaf070/8321921).

4. **Our added mechanism.** Gas/wind evidence is conditionally scored after fixing the total hit count, which removes an unknown release/sensor intercept. An evidence reservoir then delays posterior feedback until hit/miss contrast exists in both temporal folds and hits replicate at two spatial locations. This sequential spatial-replication contract is the project-specific second innovation that made the borrowed inverse/split principles work in a real PMFS closed loop.

The defensible paper claim is therefore not “we imported a 2026 method.” It is: **we derived a conditional inverse-transport likelihood and a sequential spatiotemporal identifiability rule for turbulent gas-source localization, motivated by recent inverse-causal and misspecification-robust inference principles.**

