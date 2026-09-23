# M6 external transfer evidence update

Date: 2026-09-23

An independent public technical project (`OzasaHiro/thermal-geopt`) reports preliminary low-data transfer of the **original GeoPT checkpoint** to OpenFOAM solid conduction.

Reported paired improvement vs same-architecture scratch:
- Benchmark A: +13.4% (25 cases), +17.2% (50 cases);
- Benchmark B: +10.8% (25 cases), +15.7% (50 cases).

Their custom small thermal-specific pretraining showed negative transfer.

The report is explicitly non-peer-reviewed and preliminary, so this is only feasibility evidence.

Notably, their original GeoPT transfer could not load the first input-projection weight due to a downstream shape mismatch, yet still improved. M6 is designed to preserve GeoPT's original pos3 + fx11 input shape.

This raises M6 feasibility confidence but does not replace the gas/source-rank test.
