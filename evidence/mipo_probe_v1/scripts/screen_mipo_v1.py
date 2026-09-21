#!/usr/bin/env python3
"""Reproduce the fixed MIPO V1 mechanism screen.

This is a source-blind probe-definition / truth-last evaluation script.
It does not optimize amplitude, frequency or anchor selection against source
truth.
"""
from __future__ import annotations
import csv, gzip, json, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
A = 0.4
DT = 0.2
FREQS = (0.125, 0.25, 0.5)
TAU = 1.2


def load_patch(path: Path):
    with gzip.open(path, "rt", newline="") as f:
        rows = list(csv.DictReader(f))
    g = np.zeros((160, 7, 7), dtype=float)
    wind = np.zeros((160, 2), dtype=float)
    cx = cy = None
    house = None
    for r in rows:
        t = int(r["sample_index"])
        i = int(round((float(r["dx_m"]) + 0.6) / 0.2))
        j = int(round((float(r["dy_m"]) + 0.6) / 0.2))
        g[t, i, j] = float(r["raw_gaden_concentration_ppm"])
        if i == 3 and j == 3:
            wind[t] = [float(r["wind_x_mps"]), float(r["wind_y_mps"])]
            cx, cy = float(r["center_x_m"]), float(r["center_y_m"])
            house = r["House"]
    return g, wind, np.array([cx, cy]), house


def bilinear(grid, x, y):
    ux = np.clip((x + 0.6) / 0.2, 0, 6)
    uy = np.clip((y + 0.6) / 0.2, 0, 6)
    i0 = np.minimum(5, np.floor(ux).astype(int))
    j0 = np.minimum(5, np.floor(uy).astype(int))
    tx, ty = ux - i0, uy - j0
    out = np.empty(len(grid), dtype=float)
    for t in range(len(grid)):
        i, j = i0[t], j0[t]
        out[t] = (
            (1-tx[t])*(1-ty[t])*grid[t,i,j]
            + tx[t]*(1-ty[t])*grid[t,i+1,j]
            + (1-tx[t])*ty[t]*grid[t,i,j+1]
            + tx[t]*ty[t]*grid[t,i+1,j+1]
        )
    return out


def amp_at(x, f):
    x = np.asarray(x, float)
    x = x - x.mean()
    t = np.arange(len(x))*DT
    c = 2*np.mean(x*np.cos(2*np.pi*f*t))
    s = 2*np.mean(x*np.sin(2*np.pi*f*t))
    return float(np.hypot(c, s))


def circular_probe(grid, f):
    t = np.arange(len(grid))*DT
    th = 2*np.pi*f*t
    x, y = A*np.cos(th), A*np.sin(th)
    signal = bilinear(grid, x, y)
    q = signal - signal.mean()
    gx = 2*np.mean(q*np.cos(th))/A
    gy = 2*np.mean(q*np.sin(th))/A
    return signal, np.array([gx, gy])


def angle_deg(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return None
    c = np.clip(float(a@b/(na*nb)), -1, 1)
    return float(np.degrees(np.arccos(c)))


def main():
    # Source-blind features first.
    features = []
    for path in sorted(RAW.glob("*.csv.gz")):
        g, wind, center, house = load_patch(path)
        stationary = g[:,3,3]
        static_grad = np.array([
            np.mean((g[:,4,3]-g[:,2,3])/0.4),
            np.mean((g[:,3,4]-g[:,3,2])/0.4),
        ])
        fs = []
        for f in FREQS:
            moving, grad = circular_probe(g, f)
            stat_amp = amp_at(stationary, f)
            mov_amp = amp_at(moving, f)
            H = 1/math.sqrt(1+(2*math.pi*f*TAU)**2)
            merit = H*H/(stat_amp*stat_amp + 1e-12)
            fs.append(dict(f=f, ratio=mov_amp/(stat_amp+1e-9),
                           gx=float(grad[0]), gy=float(grad[1]),
                           merit=merit))
        chosen = max(fs, key=lambda x: x["merit"])
        features.append(dict(file=path.name, house=house,
                             center=center.tolist(),
                             mean_wind=wind.mean(0).tolist(),
                             static_grad=static_grad.tolist(),
                             fstats=fs, asf_f=chosen["f"],
                             asf_grad=[chosen["gx"],chosen["gy"]]))

    # Truth is opened only after the feature list is frozen.
    truth = json.loads((ROOT/"truth_eval.json").read_text())["cases"]
    for x in features:
        case = x["file"].split("_anchor")[0]
        src = np.array(truth[case]["source_xyz_m"][:2]) - np.array(x["center"])
        x["source_distance_m"] = float(np.linalg.norm(src))
        x["static_source_angle_deg"] = angle_deg(np.array(x["static_grad"]), src)
        x["asf_source_angle_deg"] = angle_deg(np.array(x["asf_grad"]), src)

    print(json.dumps(features, indent=2))


if __name__ == "__main__":
    main()
