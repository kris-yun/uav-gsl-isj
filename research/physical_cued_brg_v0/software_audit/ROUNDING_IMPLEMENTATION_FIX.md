# Pre-training floating overlap correction

Two H01 projected presence entries evaluated as 1.0000000000000004 because
overlap arithmetic accumulates floating point roundoff. Raw maps satisfy [0,1].
Feature validation correctly refused these entries before any optimizer step.

The physical projection now rejects excursions larger than 1e-12 and clamps
only representational excursions at [0,1]. Multiplicity, footprint weights,
feature/model formulas, labels, seed, train/dev split and thresholds unchanged.
Failed dataset and empty training-output directory retained under *_pre_roundoff.
