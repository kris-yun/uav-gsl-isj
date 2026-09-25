# PRO6 NEXT TASK — In-Context Probabilistic Transport Operator (IPTO)

Date: 2026-09-25

Primary-thread status:
- CESS/FSEI: STOP;
- successor/occupation mainline: STOP;
- RR-MVSI: HOLD_LINEAR_MULTIVIEW_SIGNAL_ONLY after unified proper-score audit;
- no new GADEN simulations currently authorized.

New candidate mother theory:
**In-Context Operator Learning / Probabilistic Multi-Operator World Models**.

Core motivation:
existing GSL approaches and our failed M4 route learn one fixed source->field/operator per environment.
The proposed scientific reframing is:

  each House/wind regime E defines a transport operator G_E;
  a general model learns how to infer G_E from a few context condition->observation examples;
  at inference it applies the inferred operator to arbitrary candidate sources without weight updates;
  a probabilistic extension predicts uncertainty / stochastic observation distributions.

Recent theory anchors already found:
- Yang et al., PNAS 2023, In-Context Operator Networks (ICON), public code;
- Zhang et al., 2025, Probabilistic operator learning / GenICON, arXiv:2509.05186;
- Weihs & Schaeffer, 2026, statistical guarantees for multi-task / multiple operator learning, arXiv:2604.01961;
- VICON and related 2025/2026 high-dimensional in-context fluid/operator models.

Direct GSL overlap already found:
- 2024 Physics-Guided Neural Network GSL;
- accepted 2026 IROS physics-informed neural operator for GSL in turbulent environments;
- 2026 deep probabilistic indoor GSL with physical dependency-guided sequential inference.

Therefore ordinary 'neural operator for GSL' or 'probabilistic GSL' is NOT novel enough.

Your task:
1. Audit whether any GSL/olfaction work already performs **in-context/few-shot identification of a new transport operator** from a small set of source->observation examples without parameter updates.
2. Derive a GSL-specific mathematical object:
   E -> G_E, where G_E maps source condition + query/trajectory to expected/probabilistic plume observation.
3. Explain why this is scientifically different from:
   - M4 deterministic operator;
   - physics-guided NN/PINO/FNO;
   - domain adaptation/meta-learning;
   - ordinary fine-tuning;
   - deep probabilistic source-posterior networks.
4. Define the minimum context set needed in a new House/wind regime, and why it can be realistic for sim-to-real.
5. Design a **smallest possible cross-operator D0 acquisition** only if existing data are insufficient.
   Target <=150 new GADEN runs.
   It must compare:
   - no-context global operator;
   - per-operator fitted baseline;
   - fine-tuning/meta-learning baseline;
   - in-context operator prediction.
6. D0 must leave query source locations completely unseen within the target operator.
7. Define STOP conditions:
   - if few-shot context does not improve unseen-source proper score;
   - if fine-tuning/meta-learning matches it at same context budget;
   - if new environment needs dense source coverage;
   - if GSL prior art already contains the same mechanism.
8. Sim-to-real: propose a calibration protocol using a small number of controlled releases or natural known-source events, never an exhaustive source bank.

Deliver only:
- IPTO_THEORY_AND_2025_2026_ANCHORS.md
- GSL_OPERATOR_PRIOR_ART_AUDIT.md
- MINIMAL_CROSS_OPERATOR_D0.md
- M4_VS_IPTO_DIFFERENCE.md
- SIM_TO_REAL_CONTEXT_PROTOCOL.md
- one-page GO/HOLD/STOP recommendation.

Do not run simulations.
Do not recommend a large multi-House bank before the minimal D0 passes.