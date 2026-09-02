# START HERE — CTPI V0.4 CREL + PSRG + APRS

Date: 2026-09-02

Latest development branch:

`research/ctpi-crel-psrg-aprs-v04-20260902`

This supersedes **V0.3 as the active development candidate**. V0.3 remains historical evidence and must not be silently rewritten.

## Three modules

1. **M1 CREL — Causal Route-Encounter Law（因果路径遭遇规律）**  
   Identity: physical causal generator（物理因果生成器）.
2. **M2 PSRG — Pullback Source Resolution Geometry（拉回源分辨几何）**  
   Identity: local source metrology / resolution geometry（局部源计量/分辨几何）.
3. **M3 APRS — Adaptive Proper-Score Resolution（自适应恰当评分分辨）**  
   Identity: observation evidence arbiter（观测证据裁决器）.

Read:

1. `docs/CTPI_V04_THREE_MODULE_FREEZE_20260902.md`
2. `docs/CTPI_V04_OFFLINE_DEVELOPMENT_AUDIT_20260902.md`
3. `docs/CODEX_CTPI_V04_VM_OFFLINE_THEN_CLOSED_LOOP_20260902.md`
4. `experiments/cg_pc_ctt/ctpi_v04_reference.py`

First command:

```bash
python3 experiments/cg_pc_ctt/ctpi_v04_reference.py --selftest --iterations 3000
```

Required:

`CTPI_V04_REFERENCE_SELFTEST=PASS`

## Current authorization

`CTPI_V04_DEVELOPMENT_GO_TO_VM_EXACT_OFFLINE_AND_RUNTIME_PARITY`

This is **not** paper-level confirmation. It does **not** authorize treating PSRG's local scale as a localization confidence radius. Codex must run the exact VM fixed-trajectory/offline and runtime-parity stages before any active closed-loop qualification.
