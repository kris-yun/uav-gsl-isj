# Pilot infrastructure patch before learned-arm replay

The first frozen case (ordinal 009) was executed once under the initial pilot
runner. Native PMFS reached the 300 s budget and its result is retained. All
three learned arms stopped at the first source update with `service_error`.
The raw archives and receipts are preserved under their original `pilot_*`
names. They are infrastructure failures, not model comparison results.

The archived ROS log contains `Exception while running GSL: invalid run
token`; each sidecar log contains only the initial `HELLO` requests. The
deployed `NeuralEvidenceClient.hpp` accepts only ASCII letters, digits,
period, underscore, and hyphen in `RESET` run tokens. The original binder
passed `out.stem`, which embeds comma-separated wind names. The rejection
therefore occurs before the model receives any observation.

The binder now sends `run_` followed by 32 hexadecimal characters derived
from SHA256 of the unchanged output stem. Case ID, plume, source, wind,
candidate support, 300 s budget, checkpoint, feature encoder, planner, and
scoring remain unchanged. The safe token is recorded in `runtime_binding.json`.
The Native 009 run is reused; learned reruns use separate `pilot_fix1_*`
paths. Later selected cases use the same patched implementation. The original
failed archives are included in the final pilot review package.

Original 009 archive SHA256:

- Native: `3c689b54553602880798f6607718d39e32aa9742e6ea0c48d10c7e9cc856ba9f`
- candidate-GRU failure: `4eae9ab35fadb0b5344651d08abe00020dd3d9b3ffc7337f1455124de6d9a56e`
- BRG failure: `ad6d039701e4d23dd4f5314e462dbb382ca47263b842d59478c56b5b8bf9a763`
- ungated failure: `9043acfd56fdbe79485466889c49353890710b52869de66c1146ae65f307a3ea`

Patched binder SHA256:
`b977112331e6540081785a94951639c8cc3008417ef7e30837bb53da4cc985be`

This patch was made without inspecting learned-arm localization outcomes;
none were produced before the protocol rejection. It does not change the
frozen three-case scientific contract or reselect model weights.
