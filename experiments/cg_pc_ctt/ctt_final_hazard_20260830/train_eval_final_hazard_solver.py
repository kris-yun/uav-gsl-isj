#!/usr/bin/env python3
"""Frozen CTT H01 final spatial wind/map hazard solver.

Scientific role: physics-conditioned first-passage hazard solver.  It is NOT a
source classifier, posterior corrector, reliability gate, or end-to-end
localizer.

Freeze contract: FREEZE_FINAL_HAZARD_SOLVER_20260830.json (same directory).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from torch import nn

from ctt_h01_wind_bank_io import (
    FIRST_PASSAGE_THRESHOLD_PPM,
    STOP_SAMPLES,
    first_passage,
    read_physical,
    read_wind,
    sensor_forward,
    sha256_file,
)

# --- frozen constants (mirror FREEZE_FINAL_HAZARD_SOLVER_20260830.json) ---
SEED = 20260835
BATCH = 512
MAX_EPOCHS = 60
PATIENCE = 7
TOLERANCE = 1e-5
BOOTSTRAPS = 5000
PATCH = 32           # 32x32 cells = 3.2 m
CELL_M = 0.1
NEVER = 80
HAZARDS = 80
WIND_SCALE = 1.0     # frozen spatial wind scale (m/s)
Z_SLICE = 13         # flight height 0.3 m -> z index (0.3 - (-1.019)) / 0.1
GEO_DIM = 16
CNN_CH = 3           # occupancy, wind_u, wind_v

TRAIN_CONTEXTS = (0, 3, 5, 6, 8, 9)
VAL_CONTEXTS = (4, 7)
TRAIN_MEMBERS = (0, 1, 2, 3, 4, 5)
TEST_MEMBERS = (6, 7)
TRAIN_ROUTES = (0, 1, 2)
VAL_ROUTES = (3,)
TEST_ROUTES = (4,)
ROUTE_SEEDS = (4001, 4002, 4003, 4004, 4005)


def digest(text: str) -> bytes:
    return hashlib.sha256(text.encode("utf-8")).digest()


# --------------------------------------------------------------------------
# map loader
# --------------------------------------------------------------------------
class Map2D:
    def __init__(self, csv_path: Path) -> None:
        # parse GADEN OccupancyGrid3D.csv: header then z-major
        # (per z-layer: one line per x-column of ny y-values, then a ';' separator)
        with csv_path.open() as source:
            lines = [line.rstrip("\n") for line in source]
        header = lines[:4]
        self.min_x, self.min_y, self.min_z = (float(v) for v in header[0].split()[1:4])
        self.max_x, self.max_y, self.max_z = (float(v) for v in header[1].split()[1:4])
        self.nx, self.ny, self.nz = (int(v) for v in header[2].split()[1:4])
        self.cell = float(header[3].split()[1])
        cells = np.zeros((self.nx, self.ny, self.nz), dtype=np.float32)
        z = 0
        x = 0
        for line in lines[4:]:
            if line.strip() == ";":
                z += 1
                x = 0
                continue
            tokens = line.split()
            for j, v in enumerate(tokens):
                cells[x, j, z] = float(v)
            x += 1
        self.occ = (cells > 0).astype(np.float32)   # 0 free, 1 occupied
        self.slice = self.occ[:, :, Z_SLICE].T      # (ny, nx) occupancy at flight height

    def idx(self, px: float, py: float) -> tuple[int, int]:
        ix = int((px - self.min_x) / self.cell)
        iy = int((py - self.min_y) / self.cell)
        return ix, iy

    def patch(self, qx: float, qy: float, half: int = PATCH // 2) -> np.ndarray:
        # world-aligned, query-centered occupancy patch of shape (PATCH, PATCH)
        ix, iy = self.idx(qx, qy)
        x0, y0 = ix - half, iy - half
        out = np.zeros((PATCH, PATCH), dtype=np.float32)
        xa, xb = max(x0, 0), min(x0 + PATCH, self.nx)
        ya, yb = max(y0, 0), min(y0 + PATCH, self.ny)
        if xa < xb and ya < yb:
            out[ya - y0:yb - y0, xa - x0:xb - x0] = self.slice[ya:yb, xa:xb]
        return out


# --------------------------------------------------------------------------
# feature building
# --------------------------------------------------------------------------
def load_carriers(path: Path) -> list[dict]:
    result = []
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    for row in rows:
        parts = row["carrier_id"].split("_")
        if len(parts) != 5 or parts[0] != "quadtree":
            raise ValueError(f"CTT_H01_CARRIER_ID_FORMAT_FAIL:{row['carrier_id']}")
        result.append({
            "index": int(row["carrier_index"]), "id": row["carrier_id"],
            "x": float(row["x"]), "y": float(row["y"]),
            "size_i": float(parts[3]), "size_j": float(parts[4]),
        })
    result.sort(key=lambda item: item["index"])
    if len(result) != 210 or [r["index"] for r in result] != list(range(210)):
        raise ValueError("CTT_H01_CARRIER_CONTRACT_FAIL")
    return result


def load_schedule(path: Path) -> list[dict]:
    rows = []
    with path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            rows.append({
                "t": float(row["t_sim_s"]), "x": float(row["x"]), "y": float(row["y"]),
                "z": float(row["z"]), "yaw": float(row["yaw"]),
                "moving": int(row["is_moving"]), "stop": int(row["stop_id"]),
            })
    return rows


def wind_patch(map2d: Map2D, samples_xy: np.ndarray, samples_uv: np.ndarray,
               qx: float, qy: float, half: int = PATCH // 2) -> np.ndarray:
    """Bin causal wind samples onto a query-centered (PATCH, PATCH, 2) grid."""
    ix, iy = map2d.idx(qx, qy)
    x0, y0 = ix - half, iy - half
    acc = np.zeros((PATCH, PATCH, 2), dtype=np.float32)
    cnt = np.zeros((PATCH, PATCH), dtype=np.float32)
    for (px, py), (u, v) in zip(samples_xy, samples_uv):
        cx = int((px - map2d.min_x) / map2d.cell) - x0
        cy = int((py - map2d.min_y) / map2d.cell) - y0
        if 0 <= cx < PATCH and 0 <= cy < PATCH:
            acc[cy, cx, 0] += u
            acc[cy, cx, 1] += v
            cnt[cy, cx] += 1.0
    mask = cnt > 0
    acc[mask, 0] /= cnt[mask]
    acc[mask, 1] /= cnt[mask]
    if mask.any():
        acc[~mask, 0] = acc[mask, 0].mean()
        acc[~mask, 1] = acc[mask, 1].mean()
    return acc


def compute_stops(sched: list[dict], wind: np.ndarray) -> list[dict]:
    """Return per-stop records for one route (query poses + causal wind prefix)."""
    xy = np.asarray([[r["x"], r["y"]] for r in sched], dtype=np.float64)
    uv = wind[:, :2]
    cum = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))])
    stops = []
    previous = None
    for stop_id in sorted({r["stop"] for r in sched}):
        idxs = [i for i, r in enumerate(sched) if r["stop"] == stop_id and r["moving"] == 0]
        if len(idxs) < STOP_SAMPLES:
            continue
        idxs = idxs[:STOP_SAMPLES]
        start, end = int(idxs[0]), int(idxs[-1]) + 1
        cur = xy[start]
        delta = np.zeros(2) if previous is None else cur - previous
        route_vec = np.asarray([sched[start]["t"], cum[start], delta[0], delta[1],
                                math.sin(sched[start]["yaw"]), math.cos(sched[start]["yaw"])], dtype=np.float32)
        stops.append({"indices": idxs, "xy": cur, "route": route_vec,
                      "wind_xy": xy[:end], "wind_uv": uv[:end]})
        previous = cur
    return stops


def spatial_patch(stop: dict, map2d: Map2D) -> np.ndarray:
    qx, qy = stop["xy"][0], stop["xy"][1]
    occ = map2d.patch(qx, qy)
    wind = wind_patch(map2d, stop["wind_xy"], stop["wind_uv"], qx, qy)
    # NCHW layout: (3, PATCH, PATCH) = [occupancy, wind_u, wind_v]
    return np.stack([occ, wind[:, :, 0], wind[:, :, 1]], axis=0).astype(np.float32)


def geo_feature(carrier: dict, stop: dict) -> np.ndarray:
    source = np.asarray([carrier["x"], carrier["y"]], dtype=np.float64)
    query = stop["xy"]
    delta = query - source
    distance = max(float(np.linalg.norm(delta)), 1e-6)
    unit = delta / distance
    half_diagonal = 0.5 * 0.3 * math.hypot(carrier["size_i"], carrier["size_j"])
    geo = np.asarray([
        carrier["x"], carrier["y"], query[0], query[1], delta[0], delta[1], distance,
        unit[0], unit[1], half_diagonal, *stop["route"],
    ], dtype=np.float32)
    if geo.shape != (GEO_DIM,) or not np.isfinite(geo).all():
        raise ValueError(f"CTT_H01_GEO_CONTRACT_FAIL:{geo.shape}")
    return geo


# --------------------------------------------------------------------------
# model
# --------------------------------------------------------------------------
class SpatialWindMapHazard(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(CNN_CH, 32, 3, 1, 1), nn.SiLU(),
            nn.Conv2d(32, 64, 3, 2, 1), nn.SiLU(),
            nn.Conv2d(64, 128, 3, 2, 1), nn.SiLU(),
            nn.Conv2d(128, 128, 3, 2, 1), nn.SiLU(),
            nn.AdaptiveAvgPool2d(1),
        )
        self.geo = nn.Sequential(
            nn.Linear(GEO_DIM, 64), nn.SiLU(),
            nn.Linear(64, 64), nn.SiLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(128 + 64, 128), nn.SiLU(),
            nn.Linear(128, HAZARDS),
        )

    def hazards(self, spatial: torch.Tensor, geo: torch.Tensor) -> torch.Tensor:
        s = self.cnn(spatial).flatten(1)
        g = self.geo(geo)
        logits = self.decoder(torch.cat([s, g], dim=1))
        return torch.sigmoid(logits)   # (B, 80) hazards h_0..h_79

    def distribution(self, hazards: torch.Tensor) -> torch.Tensor:
        # induced P(F=j)=h_j*prod_{r<j}(1-h_r), P(F=never)=prod(1-h_r)
        log_h = torch.log(torch.clamp(hazards, 1e-7, 1 - 1e-7))
        log_1mh = torch.log(torch.clamp(1 - hazards, 1e-7, 1 - 1e-7))
        log_p_j = log_h + torch.cumsum(torch.cat([torch.zeros_like(log_1mh[:, :1]), log_1mh[:, :-1]], dim=1), dim=1)
        log_p_never = log_1mh.sum(dim=1, keepdim=True)
        return torch.cat([log_p_j, log_p_never], dim=1)   # log probs (B, 81)


def hazard_loss(model: SpatialWindMapHazard, spatial: torch.Tensor, geo: torch.Tensor,
                labels: torch.Tensor) -> torch.Tensor:
    hazards = model.hazards(spatial, geo)
    log_h = torch.log(torch.clamp(hazards, 1e-7, 1 - 1e-7))
    log_1mh = torch.log(torch.clamp(1 - hazards, 1e-7, 1 - 1e-7))
    cdf_prefix = torch.cumsum(torch.cat([torch.zeros_like(log_1mh[:, :1]), log_1mh[:, :-1]], dim=1), dim=1)
    per_sample = torch.zeros_like(log_h[:, 0])
    event = labels < NEVER
    if bool(event.any()):
        idx = labels[event].long()
        rows = torch.nonzero(event, as_tuple=True)[0]
        per_sample[rows] = log_h[rows, idx] + cdf_prefix[rows, idx]
    never_rows = torch.nonzero(~event, as_tuple=True)[0]
    if bool(never_rows.numel()):
        per_sample[never_rows] = log_1mh[never_rows].sum(dim=1)
    return -per_sample.mean()


# --------------------------------------------------------------------------
# training
# --------------------------------------------------------------------------
def fit(name: str, spatial_array, skey, x_geo, y, spatial_v, skey_v, xv_geo, yv,
        geo_mean, geo_std, output: Path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    xs = torch.from_numpy(spatial_array).to(device)
    sk = torch.from_numpy(skey).to(device)
    xg = torch.from_numpy((x_geo - geo_mean) / geo_std).to(device)
    xvs = torch.from_numpy(spatial_v).to(device)
    skv = torch.from_numpy(skey_v).to(device)
    xvg = torch.from_numpy((xv_geo - geo_mean) / geo_std).to(device)
    yt = torch.from_numpy(y).to(device)
    yvt = torch.from_numpy(yv).to(device)
    torch.manual_seed(SEED)
    model = SpatialWindMapHazard().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-5)
    gen = torch.Generator().manual_seed(SEED)
    dataset = torch.utils.data.TensorDataset(sk, xg, yt)
    loader = torch.utils.data.DataLoader(dataset, batch_size=BATCH, shuffle=True, generator=gen)
    best = math.inf
    stale = 0
    history = []
    for epoch in range(MAX_EPOCHS):
        model.train()
        total = count = 0
        for xb_idx, gb, yb in loader:
            loss = hazard_loss(model, xs[xb_idx], gb, yb)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            total += float(loss.detach()) * len(xb_idx)
            count += len(xb_idx)
        model.eval()
        with torch.no_grad():
            val = float(hazard_loss(model, xvs[skv], xvg, yvt))
        history.append({"epoch": epoch, "train": total / count, "validation": val})
        print(f"CTT_H01_HAZARD_TRAIN arm={name} epoch={epoch} train={total/count:.8f} val={val:.8f}", flush=True)
        if val < best - TOLERANCE:
            best = val
            stale = 0
            torch.save({"state": model.state_dict(), "geo_mean": geo_mean, "geo_std": geo_std,
                        "epoch": epoch, "validation": val}, output / f"{name}_best.pt")
        else:
            stale += 1
            if stale >= PATIENCE:
                break
    (output / f"{name}_history.json").write_text(json.dumps(history, indent=2) + "\n")
    ckpt = torch.load(output / f"{name}_best.pt", weights_only=True)
    model.load_state_dict(ckpt["state"])
    return model, ckpt


def predict(model, ckpt, spatial_array, skey, x_geo):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    xs = torch.from_numpy(spatial_array).to(device)
    sk = torch.from_numpy(skey).to(device)
    xg = torch.from_numpy((x_geo - ckpt["geo_mean"]) / ckpt["geo_std"]).to(device)
    chunks = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(sk), BATCH):
            h = model.hazards(xs[sk[start:start + BATCH]], xg[start:start + BATCH])
            chunks.append(model.distribution(h).exp().cpu().numpy())
    return np.concatenate(chunks)


def proper_scores(prob, labels):
    clipped = np.clip(prob, 1e-12, 1.0)
    nll = -np.log(clipped[np.arange(len(labels)), labels])
    cdf = np.cumsum(clipped[:, :80], axis=1)
    observed = (labels[:, None] <= np.arange(80)[None, :]).astype(np.float32)
    brier = ((cdf - observed) ** 2).mean(axis=1)
    return nll, brier


def cluster_mean(values, clusters):
    groups: dict[tuple[int, int], list[float]] = defaultdict(list)
    for v, c in zip(values, clusters):
        groups[(c[0], c[1])].append(float(v))
    return {k: float(np.mean(v)) for k, v in groups.items()}


def bootstrap(delta, rng):
    vals = np.asarray(list(delta.values()), dtype=np.float64)
    means = np.asarray([rng.choice(vals, len(vals), replace=True).mean() for _ in range(BOOTSTRAPS)])
    return float(vals.mean()), [float(v) for v in np.quantile(means, [0.025, 0.975])]


def rank(score, truth):
    return float(1 + np.count_nonzero(score > score[truth]) + 0.5 * (np.count_nonzero(score == score[truth]) - 1))


def sign_test(left, right):
    left = np.asarray(left); right = np.asarray(right)
    wins = int((left < right).sum()); losses = int((left > right).sum()); ties = int((left == right).sum())
    count = wins + losses
    p = (sum(math.comb(count, v) for v in range(wins, count + 1)) / (2 ** count)) if count else 1.0
    return {"wins": wins, "losses": losses, "ties": ties, "p": p}


def summarize(ranks):
    vals = np.asarray(ranks, dtype=np.float64)
    return {"mean_normalized_rank": float(((vals - 1) / 209).mean()), "median_rank": float(np.median(vals)),
            "top5": float((vals <= 5).mean()), "top10": float((vals <= 10).mean())}


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", type=Path, required=True, help="development bank (contexts 0..9)")
    parser.add_argument("--test-bank", type=Path, default=None, help="fresh bank (contexts 10..13); defaults to --bank")
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--schedule-root", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    test_bank = args.test_bank or args.bank
    if args.output.exists():
        raise SystemExit(f"REFUSE_OVERWRITE:{args.output}")
    args.output.mkdir(parents=True)
    np.random.seed(SEED); torch.manual_seed(SEED); torch.set_num_threads(4)

    map2d = Map2D(args.map)
    carriers = load_carriers(args.support)
    schedules = [load_schedule(args.schedule_root / "H01" / "reserved" / f"trajectory_seed_{s}.csv") for s in ROUTE_SEEDS]

    # precompute per-context route wind
    def build(bank, contexts, members, routes, capture=False):
        # pass 1: unique spatial patches per (context, route, stop) -- tiny
        spatial_list = []
        lookup = {}
        for context in contexts:
            winds = read_wind(bank / f"context_{context:02d}" / "exact_wind_routes.bin")
            for route in routes:
                stops = compute_stops(schedules[route], winds[route])
                for stop_idx, stop in enumerate(stops):
                    key = (context, route, stop_idx)
                    lookup[key] = len(spatial_list)
                    spatial_list.append(spatial_patch(stop, map2d))
        spatial_array = np.asarray(spatial_list, dtype=np.float32)

        # pass 2: per-example geo + label + spatial index (no spatial duplication)
        xg, ys, skey, clusters, binary = [], [], [], [], {}
        for context in contexts:
            winds = read_wind(bank / f"context_{context:02d}" / "exact_wind_routes.bin")
            stops_by_route = {route: compute_stops(schedules[route], winds[route]) for route in routes}
            for carrier in carriers:
                for member in members:
                    streams = read_physical(bank / f"context_{context:02d}" / f"member_{member:02d}" / f"{carrier['id']}.bin")
                    for route in routes:
                        stops = stops_by_route[route]
                        measured = sensor_forward(streams[route])
                        tape = []
                        for stop_idx, stop in enumerate(stops):
                            label = first_passage(measured[stop["indices"]])
                            xg.append(geo_feature(carrier, stop))
                            ys.append(label)
                            skey.append(lookup[(context, route, stop_idx)])
                            clusters.append((context, carrier["index"], member, route, stop_idx))
                            tape.append(measured[stop["indices"]] > FIRST_PASSAGE_THRESHOLD_PPM)
                        if capture:
                            binary[(context, carrier["index"], member, route)] = np.asarray(tape, dtype=bool)
        return (spatial_array, np.asarray(skey, dtype=np.int64), np.asarray(xg, dtype=np.float32),
                np.asarray(ys, dtype=np.int64), clusters, binary, lookup)

    print("CTT_H01_HAZARD_BUILD_TRAIN", flush=True)
    xt_spatial, xt_skey, xt_geo, yt, _, _, _ = build(args.bank, TRAIN_CONTEXTS, TRAIN_MEMBERS, TRAIN_ROUTES)
    print("CTT_H01_HAZARD_BUILD_VAL", flush=True)
    xv_spatial, xv_skey, xv_geo, yv, _, _, _ = build(args.bank, VAL_CONTEXTS, TRAIN_MEMBERS, VAL_ROUTES)

    geo_mean = xt_geo.mean(axis=0); geo_std = xt_geo.std(axis=0); geo_std[geo_std < 1e-6] = 1.0
    # STATIC comparator: zero out spatial wind channels (channels 1,2), keep occupancy
    xt_spatial_static = xt_spatial.copy(); xt_spatial_static[:, 1:, :, :] = 0.0
    xv_spatial_static = xv_spatial.copy(); xv_spatial_static[:, 1:, :, :] = 0.0

    contract = {
        "contract": "CTT_H01_FINAL_HAZARD_SOLVER_FREEZE_V1",
        "bank": str(args.bank), "map": str(args.map), "seed": SEED,
        "train_contexts": TRAIN_CONTEXTS, "val_contexts": VAL_CONTEXTS,
        "test_opened": False,
    }
    (args.output / "06_TRAINING_CONTRACT.json").write_text(json.dumps(contract, indent=2) + "\n")
    conditional, ckpt_c = fit("conditional", xt_spatial, xt_skey, xt_geo, yt, xv_spatial, xv_skey, xv_geo, yv, geo_mean, geo_std, args.output)
    static, ckpt_s = fit("static", xt_spatial_static, xt_skey, xt_geo, yt, xv_spatial_static, xv_skey, xv_geo, yv, geo_mean, geo_std, args.output)
    contract["test_opened"] = True
    contract["checkpoints"] = {"conditional": sha256_file(args.output / "conditional_best.pt"),
                               "static": sha256_file(args.output / "static_best.pt")}
    (args.output / "06_TRAINING_CONTRACT.json").write_text(json.dumps(contract, indent=2) + "\n")

    # TEST (fresh contexts 10..13)
    print("CTT_H01_HAZARD_BUILD_TEST", flush=True)
    test_contexts = (10, 11, 12, 13)
    xt_spatial_test, xt_skey_test, xt_geo_test, y_test, test_clusters, test_binary, test_lookup = \
        build(test_bank, test_contexts, TEST_MEMBERS, TEST_ROUTES, capture=True)
    xt_spatial_test_static = xt_spatial_test.copy(); xt_spatial_test_static[:, 1:, :, :] = 0.0
    p_cond = predict(conditional, ckpt_c, xt_spatial_test, xt_skey_test, xt_geo_test)
    p_static = predict(static, ckpt_s, xt_spatial_test_static, xt_skey_test, xt_geo_test)
    repeat_err = float(np.max(np.abs(p_cond - predict(conditional, ckpt_c, xt_spatial_test, xt_skey_test, xt_geo_test))))
    norm_err = float(np.max(np.abs(p_cond.sum(axis=1) - 1.0)))
    cond_nll, cond_brier = proper_scores(p_cond, y_test)
    static_nll, static_brier = proper_scores(p_static, y_test)
    c_nll = cluster_mean(cond_nll, test_clusters); s_nll = cluster_mean(static_nll, test_clusters)
    c_brier = cluster_mean(cond_brier, test_clusters); s_brier = cluster_mean(static_brier, test_clusters)
    rng = np.random.default_rng(SEED)
    d_nll = {k: s_nll[k] - c_nll[k] for k in c_nll}
    d_brier = {k: s_brier[k] - c_brier[k] for k in c_brier}
    mn_nll, ci_nll = bootstrap(d_nll, rng); mn_brier, ci_brier = bootstrap(d_brier, rng)

    # wind-shuffle (swap spatial wind channels across matched examples/contexts)
    shuf_array = xt_spatial_test.copy()
    for (ctx, route, stop_idx), pidx in test_lookup.items():
        other_ctx = (ctx - 10 + 1) % 4 + 10
        opidx = test_lookup[(other_ctx, route, stop_idx)]
        shuf_array[pidx, 1:, :, :] = xt_spatial_test[opidx, 1:, :, :]
    p_shuf = predict(conditional, ckpt_c, shuf_array, xt_skey_test, xt_geo_test)
    shuf_nll, _ = proper_scores(p_shuf, y_test)
    shuf_cluster = cluster_mean(shuf_nll, test_clusters)
    d_shuf = {k: shuf_cluster[k] - c_nll[k] for k in c_nll}
    mn_shuf, ci_shuf = bootstrap(d_shuf, rng)

    per_context = {}
    for ctx in test_contexts:
        m = np.asarray([c[0] == ctx for c in test_clusters])
        per_context[str(ctx)] = {"conditional_nll": float(cond_nll[m].mean()), "static_nll": float(static_nll[m].mean()),
                                 "conditional_brier": float(cond_brier[m].mean()), "static_brier": float(static_brier[m].mean())}
    physical_gate = {
        "static_minus_conditional_nll_ci_lower_positive": ci_nll[0] > 0,
        "static_minus_conditional_brier_ci_lower_positive": ci_brier[0] > 0,
        "all_fresh_contexts_nonreversing": all(per_context[str(c)]["conditional_nll"] < per_context[str(c)]["static_nll"] and
                                               per_context[str(c)]["conditional_brier"] < per_context[str(c)]["static_brier"] for c in test_contexts),
        "wind_shuffle_worsens_nll": ci_shuf[0] > 0,
        "normalization": norm_err < 1e-6,
        "repeat_determinism": repeat_err == 0.0,
        "all_queries_in_support": len(carriers) == 210,
    }
    physical_report = {"contract": contract["contract"], "examples": len(y_test), "per_context": per_context,
                       "static_minus_conditional_nll": mn_nll, "nll_95ci": ci_nll,
                       "static_minus_conditional_brier": mn_brier, "brier_95ci": ci_brier,
                       "wind_shuffle_minus_conditional_nll": mn_shuf, "shuffle_95ci": ci_shuf,
                       "normalization_error": norm_err, "repeat_max_abs": repeat_err, "gate": physical_gate,
                       "verdict": "CTT_FINAL_HAZARD_NEURAL_M1_PASS" if all(physical_gate.values()) else "CTT_FINAL_HAZARD_NEURAL_M1_NO_GO"}
    (args.output / "07_M1_PHYSICAL_GATE.json").write_text(json.dumps(physical_report, indent=2) + "\n")
    if not all(physical_gate.values()):
        (args.output / "VERDICT.txt").write_text(physical_report["verdict"] + "\n")
        print(json.dumps(physical_report, indent=2)); return 2

    # source-evidence gate
    example_idx = {c: i for i, c in enumerate(test_clusters)}
    rows = []
    for ctx in test_contexts:
        candidate_prob = np.zeros((210, 10, 81), dtype=np.float32)
        for s in range(210):
            for st in range(10):
                candidate_prob[s, st] = p_cond[example_idx[(ctx, s, TEST_MEMBERS[0], TEST_ROUTES[0], st)]]
        static_prob = np.zeros_like(candidate_prob)
        for s in range(210):
            for st in range(10):
                static_prob[s, st] = p_static[example_idx[(ctx, s, TEST_MEMBERS[0], TEST_ROUTES[0], st)]]
        for member in TEST_MEMBERS:
            perm_seed = int.from_bytes(digest(f"CTT-H01-HAZARD-CANDIDATE|{ctx}|{member}")[:8], "big")
            phase_perm = np.random.default_rng(perm_seed).permutation(210)
            for truth in range(210):
                tape = test_binary[(ctx, truth, member, TEST_ROUTES[0])]
                labels = np.asarray([int(np.argmax(r)) if bool(r.any()) else NEVER for r in tape])
                full = np.log(np.clip(candidate_prob[:, np.arange(10), labels], 1e-12, 1.0)).sum(axis=1)
                static_full = np.log(np.clip(static_prob[:, np.arange(10), labels], 1e-12, 1.0)).sum(axis=1)
                # survival-only: only ever/never
                ever = 1.0 - candidate_prob[:, :, -1]
                survival = np.where(labels[None, :] < NEVER, np.log(np.clip(ever, 1e-12, 1.0)), np.log(np.clip(1 - ever, 1e-12, 1.0))).sum(axis=1)
                permuted = []
                for st, t in enumerate(tape):
                    sd = int.from_bytes(digest(f"CTT-H01-HAZARD-TIME|{ctx}|{member}|{truth}|{st}")[:8], "big")
                    sh = t[np.random.default_rng(sd).permutation(STOP_SAMPLES)]
                    permuted.append(int(np.argmax(sh)) if bool(sh.any()) else NEVER)
                permuted = np.asarray(permuted)
                time_full = np.log(np.clip(candidate_prob[:, np.arange(10), permuted], 1e-12, 1.0)).sum(axis=1)
                rows.append({"context": ctx, "member": member, "truth": truth, "carrier_id": carriers[truth]["id"],
                             "rank_full": rank(full, truth), "rank_survival": rank(survival, truth),
                             "rank_time_permute": rank(time_full, truth), "rank_static_wind_full": rank(static_full, truth)})
    with (args.output / "08_SOURCE_EVIDENCE_CASES.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    keys = ("rank_full", "rank_survival", "rank_time_permute", "rank_static_wind_full")
    arrays = {k: np.asarray([r[k] for r in rows]) for k in keys}
    summaries = {k: summarize(v) for k, v in arrays.items()}
    comparisons = {"full_vs_survival": sign_test(arrays["rank_full"], arrays["rank_survival"]),
                   "full_vs_time_permute": sign_test(arrays["rank_full"], arrays["rank_time_permute"]),
                   "full_vs_static_wind": sign_test(arrays["rank_full"], arrays["rank_static_wind_full"])}
    context_dir = {}
    for ctx in test_contexts:
        m = np.asarray([r["context"] == ctx for r in rows])
        context_dir[str(ctx)] = {"full_minus_survival": float(arrays["rank_full"][m].mean() - arrays["rank_survival"][m].mean()),
                                 "full_minus_time_permute": float(arrays["rank_full"][m].mean() - arrays["rank_time_permute"][m].mean())}
    source_gate = {
        "full_beats_survival": summaries["rank_full"]["mean_normalized_rank"] < summaries["rank_survival"]["mean_normalized_rank"] and comparisons["full_vs_survival"]["p"] <= 0.01,
        "full_top10_non_degrade_survival": summaries["rank_full"]["top10"] >= summaries["rank_survival"]["top10"],
        "full_beats_time_permute": summaries["rank_full"]["mean_normalized_rank"] < summaries["rank_time_permute"]["mean_normalized_rank"] and comparisons["full_vs_time_permute"]["p"] <= 0.01,
        "full_beats_static_wind": summaries["rank_full"]["mean_normalized_rank"] < summaries["rank_static_wind_full"]["mean_normalized_rank"] and comparisons["full_vs_static_wind"]["p"] <= 0.01,
        "nonnegative_direction_each_context": all(v["full_minus_survival"] <= 0 and v["full_minus_time_permute"] <= 0 for v in context_dir.values()),
    }
    source_report = {"contract": "CTT_H01_FINAL_HAZARD_SOURCE_EVIDENCE_V1", "case_count": len(rows),
                     "summary": summaries, "comparisons": comparisons, "per_context_direction": context_dir,
                     "gate": source_gate,
                     "verdict": "CTT_FINAL_HAZARD_SOURCE_EVIDENCE_PASS" if all(source_gate.values()) else "CTT_FINAL_HAZARD_SOURCE_EVIDENCE_NO_GO"}
    (args.output / "08_SOURCE_EVIDENCE_GATE.json").write_text(json.dumps(source_report, indent=2) + "\n")
    (args.output / "VERDICT.txt").write_text(source_report["verdict"] + "\n")
    print(json.dumps({"physical": physical_report, "source": source_report}, indent=2))
    return 0 if all(source_gate.values()) else 3


if __name__ == "__main__":
    raise SystemExit(main())
