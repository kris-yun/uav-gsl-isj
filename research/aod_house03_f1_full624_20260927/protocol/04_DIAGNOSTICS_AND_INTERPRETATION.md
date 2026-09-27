# Fixed diagnostics — not alternate PASS routes

Report on the full 624-candidate support:

- exact true-source rank;
- unique Top-1 / Top-3;
- MAP source-center error;
- number of targets rescued/harmed by rawu;
- source-level results;
- path-A and path-B results separately;
- zero/signal counts.

## Neighbour-pair margin

For the true source s and its predeclared 0.30 m partner k:

`D_arm = [SSE_arm(k)-SSE_arm(s)] / ||y||^2`.

If `||y||^2=0`, define D=0.

`Delta_pair=D_rawu-D_u`.

Report:
- all target values;
- source means;
- six pair means.

This is a fixed mechanism diagnostic, NOT the primary PASS endpoint.

A positive neighbour margin cannot compensate for a distant candidate becoming
Top-1.

## Secondary comparators

Report only:
- Native binary occurrence B0, if available under the frozen support;
- ICRA-2026 EDF-rank comparator;
- u B2;
- rawu B2.

No secondary baseline can rescue the primary full-support gate.

Do not report pseudo-posterior probabilities derived by arbitrary
`softmax(-SSE)`.
