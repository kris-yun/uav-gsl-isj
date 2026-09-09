"""Quantify source, wind, and source-by-wind signal in the current 2x2 assets.

This is evaluator-only: source and wind arm labels select four immutable
records after the traces are loaded.  It asks whether a signal that is stable
across the two controlled wind regimes exists; it does not construct a source
posterior and cannot by itself validate a candidate set beyond SA/SB.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "evidence/cstar_current_runtime_assets240_20260907"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def rms(values):
    return float(np.sqrt(np.mean(np.square(values))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", type=Path, default=ASSETS)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    assets = args.assets.resolve()
    houses = {}
    for house in ("H01", "H02", "H03"):
        manifest_path = assets / "manifests" / f"{house}.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = {entry["source_id"] + "_" + entry["transport_intervention_id"].rsplit("_", 1)[-1]: entry
                   for entry in manifest["m1_episodes"]}
        if set(entries) != {"SA_fast", "SA_slow", "SB_fast", "SB_slow"}:
            raise RuntimeError(f"EXPECTED_2X2_FACTORIAL:{house}:{sorted(entries)}")
        signals = {}
        for key, entry in entries.items():
            path = assets / entry["history_trace_path"]
            if sha(path) != entry["history_trace_sha256"]:
                raise RuntimeError(f"HISTORY_HASH_MISMATCH:{entry['episode_id']}")
            trace = rows(path)
            if len(trace) != 1200:
                raise RuntimeError(f"EXPECTED_240S_HISTORY:{entry['episode_id']}")
            signals[key] = np.asarray([row["gas_ppm"] for row in trace], dtype=float)
        # Orthogonal 2x2 contrasts.  Dividing by two puts all terms on the
        # same scale as an ordinary difference between arms.
        source = ((signals["SA_fast"] - signals["SB_fast"]) +
                  (signals["SA_slow"] - signals["SB_slow"])) / 2.0
        wind = ((signals["SA_fast"] - signals["SA_slow"]) +
                (signals["SB_fast"] - signals["SB_slow"])) / 2.0
        interaction = ((signals["SA_fast"] - signals["SB_fast"]) -
                       (signals["SA_slow"] - signals["SB_slow"])) / 2.0
        prefix = {}
        for seconds in (60, 120, 180, 240):
            n = seconds * 5
            source_rms, wind_rms, interaction_rms = rms(source[:n]), rms(wind[:n]), rms(interaction[:n])
            prefix[str(seconds)] = {
                "source_main_effect_rms_ppm": source_rms,
                "wind_main_effect_rms_ppm": wind_rms,
                "source_wind_interaction_rms_ppm": interaction_rms,
                "source_over_interaction": source_rms / max(interaction_rms, 1e-12),
            }
        houses[house] = {"factorial_verified": True, "prefixes_s": prefix,
                         "trace_hashes": {key: sha(assets / entry["history_trace_path"])
                                          for key, entry in entries.items()}}
    report = {
        "contract": "CSTAR_M1_CURRENT_RUNTIME_FACTORIAL_SIGNAL_AUDIT_V1",
        "assets": str(assets),
        "asset_manifest_sha256": sha(assets / "MANIFEST.json"),
        "evaluator_only_arm_labels": ["source_id", "transport_intervention_id"],
        "model_inputs_not_modified": ["pose_xy", "gas_ppm", "wind_uv", "candidate_geometry"],
        "interpretation": "source_over_interaction > 1 is an empirical stability diagnostic, not a source-posterior or closed-loop PASS",
        "houses": houses,
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CSTAR_M1_CURRENT_RUNTIME_FACTORIAL_SIGNAL_AUDIT=PASS")


if __name__ == "__main__":
    main()
