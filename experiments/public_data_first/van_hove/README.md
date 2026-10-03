# Track C reproducibility
Pinned upstream: https://github.com/AlouetteUiO/active/tree/2aec1667f10648c4be2ccc15ab2b385ec80305b7
Raw clone isolated at C:/work/SVALBARD_BOREHOLE_REAL_DATA_20261003/raw/active.
Run preprocess.py, forward_parity.py, audit_and_invert.py. Then run the same inverter with --background 2.05 --sensitivity-label background205; --background 2.13 --sensitivity-label background213; --sigma 0.30 --sensitivity-label sigma030. Finally run finalize.py.
Only pyproj 3.8.0 and shapely 2.1.2 were installed into dataset-local dependencies with pip --target --no-deps. Existing Python/pandas/scipy/matplotlib/pytest environment reused; no House/VM/global environment changed.
The inference is conditional-wind Bayesian grid STE; do not call it reproduction of the missing field calibration PF. The explicit source coordinate is used only after every posterior is saved, for evaluation. Published frame discrepancy is independently checked.
