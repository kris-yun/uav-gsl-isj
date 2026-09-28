"""Read-only DS-PMFS D1 shadow identity scoring on fixed Native trajectories."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

import cv2
import numpy as np

EPS = 1e-9  # Archived AOD B2 contract.
cv2.setNumThreads(1)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def csv_bytes(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


def original_files(ep: dict) -> dict[str, bytes]:
    wanted = ("measurement_events.csv", "measurement_blocks.csv",
              "measurement_samples.csv", "source_update_complete.txt")
    if "archive" not in ep:
        root = Path(ep["raw_dir"])
        result = {name: (root / name).read_bytes() for name in wanted}
        for name, content in result.items():
            if sha_bytes(content) != ep["raw_files_sha256"][name]:
                raise ValueError(f"raw file changed: {ep['case_id']} {name}")
        return result
    archive = Path(ep["archive"])
    if sha_file(archive) != ep["archive_sha256"]:
        raise ValueError(f"Native archive changed: {archive}")
    zstd = shutil.which("zstd")
    if not zstd:
        raise RuntimeError("zstd executable required to read frozen Native tar.zst")
    process = subprocess.run([zstd, "-dc", str(archive)], capture_output=True, check=True)
    with tarfile.open(fileobj=io.BytesIO(process.stdout), mode="r:") as tf:
        result = {}
        for name in wanted:
            members = [m for m in tf.getmembers() if m.isfile() and m.name.endswith("_raw/" + name)]
            if len(members) != 1:
                raise ValueError(f"missing/ambiguous archive member: {archive} {name}")
            result[name] = tf.extractfile(members[0]).read()
    metadata = json.loads(Path(ep["episode_metadata"]).read_text(encoding="utf-8"))
    for name, expected in metadata["raw_files_sha256"].items():
        if name in result and sha_bytes(result[name]) != expected:
            raise ValueError(f"encoded/original raw parity failed: {archive} {name}")
    return result


def load_episode(ep: dict) -> tuple[np.ndarray, np.ndarray, list[int], list[dict]]:
    raw = original_files(ep)
    events = csv_bytes(raw["measurement_events.csv"])
    blocks = csv_bytes(raw["measurement_blocks.csv"])
    samples = csv_bytes(raw["measurement_samples.csv"])
    if not events or len(events) != len(blocks):
        raise ValueError("event/block mismatch")
    if ep.get("event_count") and len(events) != ep["event_count"]:
        raise ValueError("frozen event count mismatch")
    grouped = defaultdict(list)
    for s in samples:
        grouped[int(s["measurement_cycle_id"])].append(s)
    xy, y, compact = [], [], []
    for n, (ev, block) in enumerate(zip(events, blocks), 1):
        if int(ev["event_id"]) != n or int(block["measurement_cycle_id"]) != n:
            raise ValueError("noncontiguous deployed event")
        if len(grouped[n]) != 10:
            raise ValueError("expected ten actual sensor readings per event")
        gas = float(ev["concentration"])
        if not np.isfinite(gas) or gas < 0:
            raise ValueError("invalid gas concentration")
        if abs(gas - float(block["gas_value_used_by_algorithm"])) > 2e-5 + 5e-6 * max(1., gas):
            raise ValueError("deployed concentration parity failed")
        px, py = float(ev["robot_x"]), float(ev["robot_y"])
        if abs(px - float(block["pose_x"])) > .01 or abs(py - float(block["pose_y"])) > .01:
            raise ValueError("deployed position parity failed")
        xy.append((px, py))
        y.append(gas)
        compact.append(dict(event_id=n, x=px, y=py, concentration=gas,
                            sim_time_end=float(block["sim_time_end"])))
    if "archive" in ep:
        # Frozen V1 extraction contains the source-update mask from Native settings.
        name = Path(ep["archive"]).name.removeprefix("native_").removesuffix(".tar.zst")
        encoded = Path(ep["episode_metadata"]).with_suffix(".npz")
        with np.load(encoded, allow_pickle=False) as z:
            if z["positions"].shape != (len(xy), 2) or not np.allclose(z["positions"], xy, atol=1e-5):
                raise ValueError("frozen encoded trajectory mismatch")
            prefixes = (np.flatnonzero(z["source_update_mask"]) + 1).tolist()
    else:
        prefixes = [n for n in range(1, len(events) + 1)
                    if n % 5 == 0 and (n // 5 - 1) >= 2 and (n // 5 - 1) % 3 == 0]
    expected = [p for p in (20, 35, 50, 65) if p <= len(events)]
    if prefixes != expected:
        raise ValueError(f"source-update prefix mismatch: {prefixes} != {expected}")
    completed = [int(v) for v in raw["source_update_complete.txt"].decode().split()]
    if completed != list(range(1, len(prefixes) + 1)):
        raise ValueError(f"Native completion log mismatch: {completed}")
    return np.asarray(xy), np.asarray(y), prefixes, compact


def gaussian_occurrence_blur(rawu: np.ndarray, occupancy: np.ndarray, width: int, height: int) -> np.ndarray:
    """C++ marked-forward GaussianBlur(raw count)/GaussianBlur(free mask)."""
    mask = occupancy.astype(np.float32).reshape(height, width)
    den = cv2.GaussianBlur(mask, (0, 0), 1.5, 1.5)
    out = np.empty_like(rawu, dtype=np.float64)
    for i, row in enumerate(rawu):
        src = np.asarray(row.reshape(height, width), dtype=np.float32)
        num = cv2.GaussianBlur(src, (0, 0), 1.5, 1.5)
        out[i] = np.divide(num, den, out=np.zeros_like(num), where=den != 0).ravel()
    return out


def bank_for_env(env: int, inputs: Path, f1: Path):
    if env < 3:
        with np.load(inputs / f"env_{env}_bank.npz", allow_pickle=False) as z:
            meta = json.loads(z["metadata"].item())
            ids = [str(s) for s in z["source_ids"]]
            rawu = np.asarray(z["rawu"], dtype=np.float64)
        occupancy = np.fromfile(inputs / f"env_{env}_occupancy.u8", np.uint8)
        u = gaussian_occurrence_blur(rawu, occupancy, int(meta["width"]), int(meta["height"]))
        support = "Native legal"
    else:
        with (inputs / "h03_f1_meta.csv").open(newline="") as stream:
            meta = next(csv.DictReader(stream))
        with (f1 / "CANDIDATE_SUPPORT.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        ids = [r["source_id"] for r in rows]
        if [int(r["source_index"]) for r in rows] != list(range(624)):
            raise ValueError("House03 F1 624-candidate ordering mismatch")
        rawu = np.load(f1 / "nominal_rawu_full_maps.npy")
        u = np.load(f1 / "nominal_u_full_maps.npy")
        occupancy = np.fromfile(inputs / "h03_f1_occupancy.u8", np.uint8)
        reconstructed = gaussian_occurrence_blur(rawu[:5], occupancy, int(meta["width"]), int(meta["height"]))
        if np.max(np.abs(reconstructed - u[:5])) > 5e-5:
            raise ValueError("House03 frozen u/rawu blur parity failed")
        support = "F1 624 shadow only; Native Action Map uses 615"
    width, height = int(meta["width"]), int(meta["height"])
    if len(set(ids)) != len(ids) or rawu.shape != u.shape or rawu.shape[1] != width * height:
        raise ValueError("template shape/identity mismatch")
    if not np.isfinite(rawu).all() or not np.isfinite(u).all() or (rawu < 0).any() or (u < 0).any():
        raise ValueError("invalid amplitude template")
    return meta, ids, {"u": u, "rawu": rawu}, support


def project(maps: np.ndarray, meta: dict, positions: np.ndarray) -> np.ndarray:
    width, height = int(meta["width"]), int(meta["height"])
    d, ox, oy = (float(meta[k]) for k in ("resolution", "origin_x", "origin_y"))
    left = ox + np.arange(width) * d
    bottom = oy + np.arange(height) * d
    pred = np.empty((maps.shape[0], len(positions)), dtype=np.float64)
    for n, (x, y) in enumerate(positions):
        wx = np.maximum(0., np.minimum(left + d, x + .1) - np.maximum(left, x - .1))
        wy = np.maximum(0., np.minimum(bottom + d, y + .1) - np.maximum(bottom, y - .1))
        w = np.outer(wy, wx).ravel() / .04
        if abs(w.sum() - 1.) > 1e-7:
            raise ValueError(f"outside-map 0.2m footprint at {x,y}; no renormalization")
        idx = np.flatnonzero(w)
        pred[:, n] = maps[:, idx] @ w[idx]
    return np.maximum(pred, EPS)


def b2(pred: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    dot = pred @ observed
    norm = np.einsum("ij,ij->i", pred, pred)
    gain = np.maximum(0., dot / norm)
    sse = np.sum((observed[None, :] - gain[:, None] * pred) ** 2, axis=1)
    return sse, gain


def readout(scores: np.ndarray, truth: int) -> dict:
    correct = float(scores[truth])
    wrong = scores.copy()
    wrong[truth] = np.inf
    rank = int(1 + np.sum(scores < correct))
    unique = int(np.sum(scores == np.min(scores)) == 1 and rank == 1)
    return dict(truth_rank=rank, unique_top1=unique, top3=int(rank <= 3),
                best_wrong_margin=float(np.min(wrong) - correct),
                truth_sse=correct, best_wrong_sse=float(np.min(wrong)))


def aggregate(records: list[dict]) -> dict:
    by_source = defaultdict(list)
    for r in records:
        by_source[(r["house"], r["wind"], r["source_id"])].append(r)
    sources = []
    for (house, wind, source), rows in sorted(by_source.items()):
        out = dict(house=house, wind=wind, source_id=source, trajectories=len(rows))
        for arm in ("u", "rawu"):
            out[arm] = {key: float(np.mean([r[arm][key] for r in rows]))
                        for key in ("truth_rank", "unique_top1", "top3", "best_wrong_margin")}
        out["rawu_minus_u_rank"] = out["rawu"]["truth_rank"] - out["u"]["truth_rank"]
        sources.append(out)
    houses = []
    for house in sorted(set(s["house"] for s in sources)):
        group = [s for s in sources if s["house"] == house]
        physical = defaultdict(list)
        for s in group:
            physical[s["source_id"]].append(s)
        source_delta = [float(np.mean([s["rawu_minus_u_rank"] for s in rows]))
                        for rows in physical.values()]
        houses.append(dict(house=house, physical_source_units=len(physical),
                           source_environment_units=len(group),
                           trajectories=sum(s["trajectories"] for s in group),
                           u_mean_physical_source_rank=float(np.mean([
                               np.mean([s["u"]["truth_rank"] for s in rows])
                               for rows in physical.values()])),
                           rawu_mean_physical_source_rank=float(np.mean([
                               np.mean([s["rawu"]["truth_rank"] for s in rows])
                               for rows in physical.values()])),
                           physical_sources_improved=sum(v < 0 for v in source_delta),
                           physical_sources_harmed=sum(v > 0 for v in source_delta),
                           physical_sources_tied=sum(v == 0 for v in source_delta)))
    return dict(sources=sources, houses=houses)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--f1", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    for name, digest in manifest["input_sha256"].items():
        path = args.f1 / name.removeprefix("f1/") if name.startswith("f1/") else args.inputs / name
        if sha_file(path) != digest:
            raise ValueError(f"frozen template changed: {path}")
    if manifest["trajectory_count"] != len(manifest["episodes"]):
        raise ValueError("frozen trajectory count mismatch")
    banks = {e: bank_for_env(e, args.inputs, args.f1) for e in range(4)}
    finals, updates, compact_events = [], [], []
    all_scores = {}
    for ep in manifest["episodes"]:
        xy, y, prefixes, compact = load_episode(ep)
        meta, ids, maps, support = banks[ep["env"]]
        if ep["source_id"] not in ids:
            raise ValueError(f"truth absent from shadow support: {ep['case_id']}")
        truth = ids.index(ep["source_id"])
        predictions = {arm: project(maps[arm], meta, xy) for arm in ("u", "rawu")}
        compact_events.append(dict(case_id=ep["case_id"], events=compact, prefixes=prefixes))
        for prefix in prefixes:
            row = dict(case_id=ep["case_id"], house=ep["house"], wind=ep["wind"],
                       source_id=ep["source_id"], event_prefix=prefix, support=support,
                       candidate_count=len(ids), observation_count=prefix)
            for arm in ("u", "rawu"):
                scores, gains = b2(predictions[arm][:, :prefix], y[:prefix])
                row[arm] = readout(scores, truth)
                all_scores[f"{ep['case_id']}__{prefix}__{arm}"] = dict(
                    candidate_ids=ids, sse=scores.tolist(), gain=gains.tolist())
            updates.append(row)
        finals.append(updates[-1])
    grouped = aggregate(finals)
    result = dict(status="DS_PMFS_IDENTITY_D1_DESCRIPTIVE_SHADOW_ONLY", manifest_sha256=sha_file(args.manifest),
                  trajectory_count=len(finals), update_count=len(updates),
                  caveat="H03 has one Native trajectory and its truth is absent from Native615; H03 identity scores use same frozen F1 624 support for both arms; no cross-House PASS can be claimed from this sample",
                  no_posterior_or_planner_change=True, source_aggregates=grouped["sources"],
                  house_aggregates=grouped["houses"], final_trajectory_results=finals,
                  update_results=updates)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, obj in (("D1_RESULT.json", result), ("COMPACT_EVENTS.json", compact_events),
                      ("ALL_CANDIDATE_SCORES.json", all_scores)):
        (args.output / name).write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                                 separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=result["status"], houses=grouped["houses"],
                          result_sha256=sha_file(args.output / "D1_RESULT.json")), ensure_ascii=False))


if __name__ == "__main__":
    main()
