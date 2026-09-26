# SOLICM-G0 pinned upstream behavior audit

This audit was written before held-out target scoring. The 96-run grid, code,
hyperparameters, and frozen G0 gates are unchanged.

In the pinned LCA `TSClassif` implementation, `models/models.py` class
`classifier` ends in `nn.Softmax(dim=-1)`. Its output is therefore a six-class
probability vector. In `algorithms/algorithms.py`, `__loss_function` applies
`F.softmax(tgt_class, dim=-1)` again, and pseudo-label training requires its
largest component to exceed `tar_psuedo_thre=0.99` after epoch 30.

For any six-class probability vector, a second Softmax has maximum possible
component `e/(e+5)`, approximately `0.3522`; it cannot exceed `0.99`.
Consequently, the official pseudo-label path is mathematically inactive in
this exact six-class setting. `PL_ONLY` is a frozen implementation arm, but
cannot be described as an effective pseudo-label-adaptation baseline.

The issue does not change the direct `LCA_NO_ALIGN` versus `LCA_FULL`
comparison: the configured difference there remains `structure_weight=0`
versus `0.1`. It limits interpretation of G0-4 and any broader claim that
the model beats a functioning ordinary pseudo-label adaptation method.

The pinned code is kept verbatim. No threshold, classifier, model, seed, or
score formula was changed after this finding.
