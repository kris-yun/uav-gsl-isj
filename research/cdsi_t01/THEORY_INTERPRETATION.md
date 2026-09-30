# Theory interpretation at the prerequisite stop

Final status: **CDSI_T01_MATCHED_INTERVENTION_FAIL**.

The proposed T0.1 assumes A/B runs within each context and replicate share the
same master disturbance stream. S2/S2X were explicitly generated with disjoint
master seeds. A replicate index is an ordinal, not an exogenous-noise identity.

Therefore `x_B,r - x_A,r` is a difference between independent realizations,
not a verified same-disturbance source intervention. It includes source
variation and both independent realization fluctuations. This distinction
does not imply that an independent-sample difference cannot be statistically
useful; it invalidates the specific fixed-disturbance interpretation required
by this request's Gate A.

No conclusion about positive/zero directional information, dynamic advantage,
cross-time advantage, or CDSI theoretical validity follows from this audit.
The prescribed crossnobis, cosine, covariance and sign-flip tests were not run.

Environmental matching remains verified for all 32 proposed pairs. The 64-run
bank remains valid for its original independent-source-distribution purpose.
No past PASS or STOP result is rewritten.

Additional boundary visible in the metadata: within both Houses, the two
configured source locations have different z values (H01 0.4/-0.3 m;
H02 0.2/-0.1 m). A later claim about only an xy displacement on one common
known-height plane must address this existing geometry. This observation does
not alter Gate A's decision and authorizes no new source or simulation.

Next action is human review of the execution contract. Do not automatically
pair seeds, reassign observations, generate common-random-number runs, modify
the null test, or proceed to R3A/3D/training/confirmation.
