"""Frozen H0-R reconstruction and source-blind scoring, with no truth input."""
import argparse
import ast
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tarfile

import numpy as np
from scipy.stats import spearmanr

CASES = [f"{house}_seed{seed}_off_off" for house in ("House01", "House02") for seed in (0, 1)]
ARMS = ("P2", "P3", "G2", "G3")
ROOT = Path(__file__).resolve().parents[2]
HISTORY = ROOT / "evidence/ts_p3t_h0_temporal_closure_20261001"
D0 = ROOT / "evidence/p3t_d0_gaussian_support_20261001"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def param(text, key):
    matches = re.findall(r"^\s*" + key + r":\s*([-+0-9.eE]+)\s*$", text, re.M)
    assert len(matches) == 1, (key, matches)
    return float(matches[0])


def banks():
    """Only parse candidate map bytes and source-blind saved score columns."""
    expected = {name: digest for digest, name in (line.split("  ", 1) for line in (D0 / "SHA256SUMS.txt").read_text().splitlines())}
    data, old, manifest, archives = {}, {}, [], []
    for basename, pattern, armmap in [
        ("point_controls.tar.gz", r"^point_controls/([^/]+)/(oracle2d|oracle3d)/(.*)$", {"oracle2d": "P2", "oracle3d": "P3"}),
        ("gaussian_outputs.tar.gz", r"^\./repeat1/([^/]+)/(g2|g3)/(.*)$", {"g2": "G2", "g3": "G3"}),
    ]:
        path = D0 / basename
        digest = sha(path.read_bytes())
        assert digest == expected[basename], basename
        archives.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": digest})
        with tarfile.open(path) as tar:
            for member in tar:
                match = re.match(pattern, member.name)
                if not member.isfile() or not match or match[1] not in CASES:
                    continue
                case, arm, rest = match[1], armmap[match[2]], match[3]
                if rest.startswith("maps/") and rest.endswith(".f32"):
                    raw = tar.extractfile(member).read()
                    cid = Path(rest).stem
                    data.setdefault((case, arm), {})[cid] = np.frombuffer(raw, dtype="<f4").copy()
                    manifest.append([case, arm, cid, basename, member.name, len(raw), sha(raw)])
                elif rest == "candidate_log_scores.csv":
                    content = tar.extractfile(member).read().decode()
                    old[(case, arm)] = {r["candidate_id"]: float(r["log_score"]) for r in csv.DictReader(io.StringIO(content))}
    assert len(data) == 16 and len(old) == 16
    return data, old, sorted(manifest), archives


def write_tsv(path, header, values):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header); writer.writerows(values)


def cosine(x, y):
    nx, ny = float(np.linalg.norm(x)), float(np.linalg.norm(y))
    return float(np.dot(x, y) / (nx * ny)) if nx > 0 and ny > 0 else None


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    (out / "recent_maps").mkdir()
    audit = json.loads((HISTORY / "P0_ARCHIVE_AUDIT.json").read_text())
    assert audit["archive_sidecar_match"] and audit["archive_sha256"] == "81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708"
    expected = {r["path"]: r["archive_sha256"] for r in csv.DictReader((HISTORY / "P0_VERIFIED_INPUTS.tsv").open(), delimiter="\t")}
    maps, frozen_scores, map_manifest, archives = banks()
    input_hashes, reconstruction, memories, scores = [], {}, [], []
    all_score_parity = []
    for case in CASES:
        original = HISTORY / "retained_inputs/native" / case
        u4 = original / "context_bank/source_update_0004/measured_hit_probability.csv"
        u5 = original / "context_bank/source_update_0005/measured_hit_probability.csv"
        timing = original / "context_bank/source_update_timing.csv"
        configs = list((original / "resolved_runtime").glob("launch_params_*"))
        config = next(p for p in configs if "sourceDiscriminationPower:" in p.read_text())
        for path in (u4, u5, timing, config):
            key = path.relative_to(HISTORY / "retained_inputs").as_posix()
            digest = sha(path.read_bytes())
            assert digest == expected[key], key
            input_hashes.append([key, path.stat().st_size, digest])
        text = config.read_text()
        prior = param(text, "hitPriorProbability")
        weight = param(text, "confidenceMeasurementWeight")
        power = param(text, "sourceDiscriminationPower")
        recent = out / "recent_maps" / (case + ".csv")
        result = subprocess.run([sys.executable, str(ROOT / "research/ts_p3t_h0r/reconstruct_recent_map.py"),
                                 "--update4", str(u4), "--update5", str(u5), "--prior", str(prior),
                                 "--confidence-weight", str(weight), "--out", str(recent)], capture_output=True, text=True, check=True)
        integrity = ast.literal_eval(result.stdout.strip())
        c4, c5, cr = rows(u4), rows(u5), rows(recent)
        index = np.array([int(r["cell_index"]) for r in c5 if r["occupancy"] == "Free"])
        assert [int(r["cell_index"]) for r in c5] == list(range(len(c5)))
        assert all(x[k] == y[k] for x, y in zip(c4, c5) for k in ["cell_index", "grid_i", "grid_j", "x", "y", "occupancy"])
        m = {label: {field: np.array([float(r[field]) for r in cells])[index] for field in ["probability", "logOdds", "omega", "confidence"]}
             for label, cells in [("UPDATE4", c4), ("FULL", c5), ("RECENT", cr)]}
        times = {int(r["source_update_id"]): r for r in rows(timing)}
        assert all(times[4][k] == times[5][k] for k in ["grid_width", "grid_height", "cell_size", "origin_x", "origin_y"])
        t4, t5 = float(times[4]["sim_time"]), float(times[5]["sim_time"])
        assert t5 > t4
        w4, w5, wr = (m[k]["omega"] for k in ["UPDATE4", "FULL", "RECENT"])
        negative_raw = w5 - w4
        # An independent vectorized recomposition check supplements the frozen script.
        recomposition = {
            "logOdds": float(np.max(np.abs(m["UPDATE4"]["logOdds"] + m["RECENT"]["logOdds"] - math.log(prior / (1 - prior)) - m["FULL"]["logOdds"]))),
            "omega": float(np.max(np.abs(w4 + wr - w5))),
            "confidence": float(np.max(np.abs(1 - np.exp(-w5 / weight ** 2) - m["FULL"]["confidence"]))),
        }
        assert max(recomposition.values()) <= 1e-12
        assert float(np.min(negative_raw)) >= -1e-12
        reconstruction[case] = {**integrity, "independent_vector_recomposition_max_abs": recomposition,
                                "pass": True, "free_cells": len(index), "prior": prior, "confidence_weight": weight,
                                "sourceDiscriminationPower": power, "map_metadata_equal": True, "update_times_s": [t4, t5],
                                "recent_map_sha256": sha(recent.read_bytes()), "negative_omega_cells": int(np.count_nonzero(negative_raw < 0))}
        memory = {"case": case, "update4_time_s": t4, "update5_time_s": t5, "interval_duration_s": round(t5 - t4, 10),
                  "terminal_omega_sum": float(w5.sum()), "recent_omega_sum": float(wr.sum()), "older_omega_fraction": float(w4.sum() / w5.sum()),
                  "recent_positive_confidence_cells": int(np.count_nonzero(m["RECENT"]["confidence"] > 0)),
                  "recent_positive_confidence_fraction": float(np.mean(m["RECENT"]["confidence"] > 0)),
                  "FULL_RECENT_probability_L1": float(np.abs(m["FULL"]["probability"] - m["RECENT"]["probability"]).sum()),
                  "FULL_RECENT_logOdds_L1": float(np.abs(m["FULL"]["logOdds"] - m["RECENT"]["logOdds"]).sum()),
                  "FULL_RECENT_probability_cosine": cosine(m["FULL"]["probability"], m["RECENT"]["probability"]),
                  "FULL_RECENT_logOdds_cosine": cosine(m["FULL"]["logOdds"], m["RECENT"]["logOdds"])}
        canonical = sorted(maps[(case, "P2")])
        for arm in ARMS:
            bank = maps[(case, arm)]
            assert sorted(bank) == canonical == sorted(frozen_scores[(case, arm)])
            vectors = {}
            for observation in ("FULL", "RECENT"):
                state = m[observation]
                values = []
                for cid in canonical:
                    hit = bank[cid]
                    assert len(hit) == len(c5) and np.isfinite(hit).all() and float(hit.min()) >= 0 and float(hit.max()) <= 1
                    factor = 1 - state["confidence"] * np.abs(state["probability"] - hit[index].astype(np.float64)) * power
                    assert np.isfinite(factor).all() and float(factor.min()) > 0
                    score = float(np.log(factor).sum())
                    scores.append([case, arm, observation, cid, format(score, ".17g")])
                    values.append(score)
                vectors[observation] = np.array(values)
            error = float(np.max(np.abs(vectors["FULL"] - np.array([frozen_scores[(case, arm)][cid] for cid in canonical]))))
            assert error <= 1e-10, (case, arm, error)
            all_score_parity.append({"case": case, "arm": arm, "candidate_count": len(canonical), "FULL_D0_max_abs_score_error": error})
            memory[arm + "_FULL_RECENT_score_spearman"] = float(spearmanr(vectors["FULL"], vectors["RECENT"]).statistic)
        memories.append(memory)
    save(out / "H0R_RECENT_MAP_AUDIT.json", {"integrity_pass": True, "cases": reconstruction, "FULL_D0_score_parity": all_score_parity})
    save(out / "H0R_INPUT_PROVENANCE.json", {"archive_sha256": audit["archive_sha256"], "candidate_archives": archives,
                                            "truth_ownership_loaded": False, "source_blind": True,
                                            "reconstruct_script_sha256": sha((ROOT / "research/ts_p3t_h0r/reconstruct_recent_map.py").read_bytes())})
    write_tsv(out / "H0R_INPUT_SNAPSHOTS.tsv", ["path", "bytes", "sha256"], input_hashes)
    write_tsv(out / "H0R_CANDIDATE_MAPS.tsv", ["case", "arm", "candidate_id", "archive", "member", "bytes", "sha256"], map_manifest)
    write_tsv(out / "H0R_OBSERVATION_MEMORY.tsv", list(memories[0]), [[r[k] for k in memories[0]] for r in memories])
    write_tsv(out / "H0R_CANDIDATE_SCORES.tsv", ["case", "arm", "observation", "candidate_id", "log_score"], scores)
    print(json.dumps({"integrity_pass": True, "case_count": len(reconstruction), "candidate_map_count": len(map_manifest),
                      "candidate_score_count": len(scores), "max_FULL_D0_error": max(r["FULL_D0_max_abs_score_error"] for r in all_score_parity)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
