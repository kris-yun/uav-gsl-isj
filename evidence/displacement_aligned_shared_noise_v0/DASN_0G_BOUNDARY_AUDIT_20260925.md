# DASN 0G — Free-Space Boundary Audit

Date: 2026-09-25

Status: **SHARED ERROR IS NOT BOUNDARY-DOMINATED**

Boundary labels are defined from the complete frozen 630-cell free PMFS source bank, not from the artificial edge of the 168-source D1R panel.

A D1R source is labeled boundary if any of its four PMFS grid neighbors is absent from the 630-cell free-source bank.

Counts:
- boundary = 25;
- interior = 143.

Using the unified ridge readout pipeline:

## Direction A
- all-source T = 0.02957 m^2;
- boundary mean T_s = 0.031995 m^2;
- interior mean T_s = 0.029147 m^2;
- boundary positive-T fraction = 0.64;
- interior positive-T fraction = 0.601.

## Direction B
- all-source T = 0.023995 m^2;
- boundary mean T_s = 0.020600 m^2;
- interior mean T_s = 0.024589 m^2;
- boundary positive-T fraction = 0.68;
- interior positive-T fraction = 0.643.

## Decision

The shared localization-error signal remains present in the 143 interior sources and is not explained by free-space boundary sources.

This does not yet establish displacement alignment.

Next mini-step: **DASN-0H training-half Jacobian / displacement-projection test only**.