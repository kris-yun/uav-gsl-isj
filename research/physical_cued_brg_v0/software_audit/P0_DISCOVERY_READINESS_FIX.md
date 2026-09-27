# Infrastructure-only pre-clock DDS readiness fix

P0 v1 candidate-GRU delivered zero measurements and never initialized PMFS.
The benchmark waited only 10 wall seconds for the GSL action server; during
four-arm concurrent startup the server became available after this wait.
Its no-estimate error output then raised FileNotFoundError. No source ranking,
model architecture, checkpoint, gas data, seed or stopping threshold is changed.

Use 120 wall seconds for action-server discovery while /clock remains zero.
All successful runs still require PMFS initialization at simulation/search t=0.
P0 v1 retained in its original directory. Run all four P0 arms under the same
patched runner version, then complete the fixed remaining three cases; do not
selectively keep better repeated outcomes. No retraining. P1 still ends at16.
