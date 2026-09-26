# Post-scoring independent-checker repair

The frozen supplied scorer and complete scorer convert concentration to
float64 before log. The first independent verifier instead applied log to the
float32 target array, producing a 4.6473e-6 numerical discrepancy before its
comparison gate. Its original version is retained unchanged (and still matches
the pre-target hash). `verify_review_local_v2.py` independently uses float64
inputs and the closed-form constrained regression RSS.

V2 passed all 72 target rank comparisons. Maximum closed-form score difference
from the frozen scorer: 5.751417120336555e-10. All 12,976 original review files
passed their inventory, all 174 historical OFF/ON maps passed exact parity,
all 6,336 forward maps matched their repeat, and bank moments were reconstructed.

No scientific kernel, bank, target, score, formula, seed or gate was changed.
The first review ZIP is preserved as INITIAL_PRE_VERIFIER; the final review
adds V2 and this audit note.
