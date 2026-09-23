# M6 GT-wind prompt range preflight

Date: 2026-09-23

Using the recovered Native House01 GADEN ground-truth wind field (626 free cells), the pretraining-aligned GeoPT dynamics prompt was checked numerically.

With:
- House x normalization to target extent 5;
- tau_ref = 1 s;

normalized advective step length has:
- median ~0.0355;
- Q95 ~0.156;
- max ~0.268;
- 0% above GeoPT's released synthetic pretraining max_step=2.

Thus the gas wind-displacement prompt is not outside GeoPT's pretraining numerical support.

This is only a range/interface check; transfer quality and source rank remain unproven.
