# HOLD — source-location contract must be audited before any E2C simulation

Date: 2026-09-29
Status: NO GADEN RUN AUTHORIZED

The 144-run pre-run freeze selected confirmation sources by scanning PMFS/navigation
free cells and applying an E1-style geometry rule. The selector did **not** prove
that those cells belong to the dataset/scenario's configured source-location
catalog.

Relevant implementation:
- `research/e2c_r1/select_e2c_sources_vm.py`
- `research/e2c_r1/select_e2c_unexposed_sources_vm.py`

Those scripts construct new `pmfs_i_j` source IDs from occupancy/navigation
geometry. `run_e2c_vm.py` then passes the resulting `source_xyz` to the E2
acquisition runner.

If the House GADEN dataset defines a finite configured set of admissible source
locations, arbitrary free cells are outside the dataset contract even if GADEN
can technically simulate them. In that case they must not be used as
"new confirmation sources" for the existing benchmark.

Therefore:
- the 144-run source panel remains an archived proposal only;
- zero simulations have been run and must remain zero;
- do not create the proposed data root;
- do not consume seeds;
- do not execute Ordinal or any mechanism analysis.

Next required action: audit the actual House01/02/03 scenario/configuration
files on the VM and produce the authoritative allowed source-location catalog,
including exact coordinates, source IDs/config names, wind/config compatibility,
and whether source coordinates are fixed or runtime-editable under the original
dataset contract.

Only after this audit may the benchmark-completion plan be redesigned.
