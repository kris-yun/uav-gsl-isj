# D0-Lite single-case authorization, 2026-09-30

User supersedes the batch stage: D1A is retained and PAUSED, with no OFF/ON smoke or 64-run campaign executed. D0-Lite permits exactly one Native replay and zero-shot inference, no training or second target. No confirmation/H03, no generator, no source/path/threshold changes. Branch research/icra2025-pmfs-d0-lite-20260930.

Case selection is lexicographically first H01 row in frozen discovery runlist, not selected by output: ocb_r2_cfg00_r01. This existing archive passed all1803 raw-record hashes. Source truth is bookkeeping/evaluation only, never a U-Net channel or planner input. Native's existing top5% endpoint and declaration/timeout rules remain unchanged;300s is maximum budget and early declaration is separately reported rather than disabled.

Logger isolated code/diffs and all input/runtime contracts are frozen before this first Native target. The exact-/map read-only subscriber only saves existing map messages. No topic writes, random draws or estimator changes. Formal logger OFF/ON noninvasiveness is NOT established in D0-Lite and must not be claimed.

Official weight audit: upstream ca0c387be9f27716a422588ac2299e2d816c3e2a README does not identify a unique default checkpoint; notebook points to a different absent filename unet_model_3d_final_1.pth. Therefore no primary/best checkpoint is selected; all four supplied checkpoints will be reported.

Three3-channel checkpoints receive the exact audited occupancy + encounter-local wind halfplanes + encountered-location channels. unet_model_final.pth has2input channels and cannot consume the same3-channel tensor. Its diagnostic uses the upstream inference notebook's explicit commented two-channel construction `[padded_map, windmap]`, where map contains233at encountered pixels. Report this input-variant ambiguity and do not silently call it the3-channel model. Report compatible-three and all-four means/ranges separately; no result-selected winner.

No rescaling, resize, sensor/threshold normalization, wall masking or posterior softmax. Actual-/map shape/origin/resolution retained, zero padding to279only. Network receives only actual completed Native StopAndMeasure positive events <=300s, their actual pose/quaternion and local measured downwind direction. Upwind raster conversion uses the pre-target32case vector-angle parity proof. No unvisited concentration query. Native retains original full-field state0 `/wind_value` interface; U-Net receives measured local wind only, so D0-Lite is an engineering transfer screen, not equal-model-information proof.

All weights are zero-shot/eval, exact upstream architecture, GPU deterministic settings. Location is the paper's unmasked centroid within original map extent; peak is diagnostic, no best-checkpoint selection. Preserve tensors/maps/event list and repeat identical inference for byte parity, without retraining.

Engineering labels, not scientific gates: per checkpoint, finite/valid output with free-map peak and centroid error at least0.5m below Native is PROMISING; difference within0.5m is PLAUSIBLE; larger error or invalid output is ZERO_SHOT_TRANSFER_POOR. Overall requires all three semantically compatible3-channel models to be promising for PROMISING, all poor for POOR, otherwise PLAUSIBLE (mixed results explicitly shown). Threshold0.5m is a pre-result descriptive engineering band, not a publishable statistical test. Raw errors and map morphology take priority over label.

One target only; after plots, results, hashes and review package STOP. No automatic1->4expansion.
