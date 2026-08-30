# CTT M2 fixed-U prospective-K premise: terminal NO-GO

## Decision

`CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_NO_GO`

The proposed M2 mechanism—retaining one native stochastic forward realization
across completed physical stops—does not improve source ordering relative to
independently marginalizing/redrawing the transport realization at each stop.
It must not be promoted to PMFS runtime or closed-loop validation.

## Prospective design actually evaluated

- House: H01; wind context: 0; source placement: fixed `U0` for every world.
- Sources: all 210 persistent carriers.
- Predictive native transport realizations: six (`K=101,211,307,401,503,601`).
- Prospective observation transport realizations: seven SHA-derived seeds that
  did not occur in the surviving repository/VM manifests before materialization.
- Measurement designs: routes 4004 and 4005; they were aggregated within each
  prospective transport unit, not treated as independent probability units.
- Physical bank: 2730/2730 shards, 210/210 K0 byte-identical runtime sentinels.
- Independent statistical units: the seven prospective observation transport
  realizations. The 210 source ranks and two routes were not pseudo-replicated.

## Result

| Quantity | Coherent M2 | Per-stop redraw |
|---|---:|---:|
| Mean normalized true-carrier rank | 0.0984498584 | 0.0983782508 |
| Median true-carrier rank | 17.0 | 16.5 |
| Top-5 recall | 0.191836735 | 0.192176871 |
| Top-10 recall | 0.328231293 | 0.329591837 |

The registered primary statistic (redraw rank minus coherent rank) was
`-7.16075904e-05`. Transport-unit outcomes were 3 wins and 4 losses with no
ties; the one-sided exact sign-test p-value was `0.7734375`. Both fixed routes
slightly reversed direction (`-1.30196e-05` for 4004 and `-1.30196e-04` for
4005). The requirement that all seven transport-unit effects be positive was
not met.

The absolute source ordering itself was informative (coherent mean normalized
rank 0.09845, below the registered 0.35 ceiling), but this information was
already present in the one-stop nuisance marginals. Cross-stop K identity added
no reproducible ordering information.

## Destruction controls and invariances

- observation-source association: empirical upper-tail `p=0.57977`;
- candidate-stop association: `p=0.14008`;
- predictive-K identity: `p=0.81323`;
- candidate-row invariance: exact (`0` maximum absolute difference);
- global K permutation and online/batch arithmetic: `1.78e-15`, within the
  frozen `1e-12` tolerance.

Thus the failure is not a numerical-order or tie-handling artifact. The
registered coherent statistic is not selectively destroyed by removing the
claimed source/stop/K structure.

## Tooling closure before outcome read

Two interface defects stopped evaluation before any source score was written:

1. the preregistration JSON contained one trailing comma;
2. the initial evaluator/null map counted raw stop IDs rather than complete
   80-sample physical sensing blocks.

The frozen observation operator used everywhere else in the CTT chain is:
take the first 80 stationary samples of a stop with at least 80 samples and
exclude an incomplete final stop. Before scoring, this rule was restored,
covered by a regression test, and the valid-block-aware V3 null map was frozen
with the same null families, replicate count and RNG seeds. The physical bank
was not regenerated. The repair freeze and both old/new null maps are retained.

## Scientific implication

This result rejects M2 as the main innovation. It also gives a concrete
explanation for the prior seed instability: simulator-internal transport
coherence does not provide stable incremental source evidence beyond per-stop
transport marginals, so any improvement can change sign with the realized
trajectory/seed.

M1 (native concentration-to-sensor observation operator) remains a valid
supporting physical module. M3 remains uncalibrated. Neither can rescue the
failed M2 premise, and no closed loop is authorized from this experiment.

The next main-mechanism derivation must operate on information not tested away
here: source-discriminating structure after legal marginalization of placement,
transport and sensor nuisance, with a prospective ordering/destruction gate
before any PMFS integration.
