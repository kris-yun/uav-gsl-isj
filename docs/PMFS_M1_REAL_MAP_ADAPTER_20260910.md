# M1 full-map input checkpoint

Implemented a map-only 3D occupancy adapter, not an evaluator gas/wind reader.
GADEN ASCII rows are constant x with y values; layers are separated by ';'.
The adapter stores cells[z,y,x], rejects malformed sizes and unknown cell
states, and uses float32 coordinate indexing consistent with the existing
audited reader. Map extents can have a partial final voxel; they are not
silently resized to navigation dimensions. Free=0, obstacle=1, outlet=2.

Read-only copied original House maps from the connected VM. All three SHA256
hashes match the frozen geometry manifest. Every navigation-plane candidate
was checked for free-space membership, unique voxel and correct z slice:

| House | 3D dimensions | Candidates checked |
|---|---|---|
| H01 | 87 x 114 x 33 | 6866 |
| H02 | 83 x 119 x 26 | 6811 |
| H03 | 138 x 83 x 25 | 7258 |

This is real-data input validation, not synthetic-only testing. It does not
validate ray visibility, sliding boundary dynamics, concentration prediction,
source height support, or causal closed-loop utility. Existing wind history
availability remains a separate requirement: local wind samples and a single
height slice cannot silently become a 3D estimated field.

Evidence: evidence/cstar_m1_real_maps3d_alignment_20260910.json.
Code: experiments/ctpi_cstar/m1_causal/occupancy3d.py.
Checks: selftest_m1_occupancy3d.py and audit_m1_real_maps3d.py. The audit refuses
to overwrite its prior result; the selftest uses disposable synthetic maps.

No ROS run, new seed, bank construction, navigation modification or M2 work
was performed. Next: geometry visibility/boundary integration and explicit
physical-parameter/wind provenance before same-route prediction evaluation.
