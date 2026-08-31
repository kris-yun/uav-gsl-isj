# CTT causal-temporal PMFS shadow Stage-1 freeze

Stage 1 completed before native PMFS source posteriors, `case_result.json`,
source truth, or localization error were opened by the evaluator.

- Git commit: `4127540fed09905105a8f6ff9f938d424edef7f3`
- evaluator SHA-256:
  `201fb8933b9c309863bc8e7bb80424a294a56e08a928a2b3f4495abe009dee58`
- preregistration SHA-256:
  `ed0a2759fb3d7ab4771b25e056fef679d476c9c0cbde00bff81f5b0981b1aae1`
- Stage-1 records: `150`
- verified train shards: `4936`
- exact historical-measured/train-member tape matches: `0`
- online-versus-batch invariant: PASS during Stage 1
- `METHOD_POSTERIORS.npz` SHA-256:
  `e1c2e15f2778272f4ad3bcffa84414cfc1829736af2740065afb95cdd5dc3926`
- `METHOD_POSTERIORS_MANIFEST.json` SHA-256:
  `f6af7ad328dc40db7554a9f2daee8f80619e627f8c26c1ed5067529c7de94518`
- `INPUT_FREEZE.json` SHA-256:
  `6d0ce89c50e90d564b2344fd21c7f5d50c3d9a48b1db004a0aa151e939bbc1dd`
- semantic pre-truth posterior SHA-256:
  `95d68bf4078fa6117a0555acfad78f827a5c51f4b69d2a55869c5dca16f65032`

Stage 2 is permitted to read comparator and truth files only when supplied
the externally recorded manifest hash above.  It may evaluate the frozen
posteriors but cannot recompute or change them.
