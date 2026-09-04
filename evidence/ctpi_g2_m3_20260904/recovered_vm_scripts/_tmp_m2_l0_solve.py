#!/usr/bin/env python3
"""L0 定位 rank：advection-diffusion 数值解（时变 wind）vs 峰值场 vs Gaussian plume。

下游观测定位任务：真源在下游(y>-1.8)的峰值浓度观测，各 carrier 用其预测场匹配，rank 真源。
对比：峰值场(197) / 时变 plume(95) / 数值解(?)
"""
import numpy as np, csv, random, os

B = "/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1/H01"
D = np.load("/dev/shm/m2_l0_data.npz")
coarse_free = D["coarse_free"]
wind_u = D["wind_u"]; wind_v = D["wind_v"]
manifest_stream = D["manifest_stream"]; manifest_native = D["manifest_native"]
manifest_x = D["manifest_x"]; manifest_y = D["manifest_y"]
src_peak = D["src_peak"]

NX, NY = 29, 38
CELL = 0.3
DC = 0.01  # 标定的扩散系数

stream_native = {int(s): int(n) for s, n in zip(manifest_stream, manifest_native)}
stream_xy = {int(s): (float(x), float(y)) for s, x, y in zip(manifest_stream, manifest_x, manifest_y)}
native_xy = {int(n): (float(x), float(y)) for n, x, y in zip(manifest_native, manifest_x, manifest_y)}

peak = np.fromfile(os.path.join(B, "g2m1_peak_field.bin"), dtype=np.float32, offset=20).reshape(210, 8, 626)
member_dir = os.path.join(B, "worlds", "member_00")
sorted_carriers = sorted(f[:-4] for f in os.listdir(member_dir) if f.endswith(".bin"))
carrier_to_idx = {c: i for i, c in enumerate(sorted_carriers)}
true_carrier = "quadtree_22_16_2_2"

def advance(C, u2d, v2d, dt, src):
    dx = CELL
    C_left = np.roll(C, 1, axis=0); C_left[0, :] = 0.0
    C_right = np.roll(C, -1, axis=0); C_right[-1, :] = 0.0
    C_down = np.roll(C, 1, axis=1); C_down[:, 0] = 0.0
    C_up = np.roll(C, -1, axis=1); C_up[:, -1] = 0.0
    dCdx = np.where(u2d >= 0, (C - C_left) / dx, (C_right - C) / dx)
    dCdy = np.where(v2d >= 0, (C - C_down) / dx, (C_up - C) / dx)
    adv = -u2d * dCdx - v2d * dCdy
    lap = (C_left + C_right + C_down + C_up - 4 * C) / (dx * dx)
    Cnew = C + dt * (adv + DC * lap)
    Cnew = np.maximum(Cnew, 0.0)
    Cnew[src[0], src[1]] += dt * 1.0
    Cnew[~coarse_free] = 0.0
    return Cnew

def run_peak(src_ix, src_iy, T_total=300.0, wind_cycle=11):
    dt = min(1.0, 0.4 * CELL * CELL / DC)
    C = np.zeros((NX, NY)); pk = np.zeros((NX, NY))
    steps = int(T_total / dt); seg = max(1, steps // wind_cycle)
    for wi in range(wind_cycle):
        u2d = wind_u[wi]; v2d = wind_v[wi]
        for _ in range(seg):
            C = advance(C, u2d, v2d, dt, (src_ix, src_iy))
            np.maximum(pk, C, out=pk)
    return pk

# 观测：真源下游峰值
downstream = [s for s, (x, y) in stream_xy.items() if y > -1.8]
random.seed(1)
obs_streams = sorted(random.sample(downstream, min(40, len(downstream))))
obs = {s: max(0.0, src_peak[s] + random.gauss(0, 2.0)) for s in obs_streams}

def norm_mse(obs_v, pred_v):
    op = np.array([obs_v[s] for s in obs_streams]); op = op / (op.max() + 1e-9)
    pp = np.array([pred_v[s] for s in obs_streams]); pp = pp / (pp.max() + 1e-9)
    return -np.mean((op - pp)**2)

def rank_true(scores):
    ordered = sorted(scores.items(), key=lambda kv: -kv[1])
    for i, (cid, _) in enumerate(ordered, 1):
        if cid == true_carrier:
            return i
    return -1

# 每个 carrier 的源 native（bank 峰值 argmax -> stream -> native）
carrier_src_native = {}
for cid in sorted_carriers:
    ci = carrier_to_idx[cid]
    s = int(np.argmax(peak[ci, 0, :]))   # stream ordinal
    carrier_src_native[cid] = stream_native[s]

# 1) 峰值场（抹风向）基线
pred_peak = {}
for cid in sorted_carriers:
    ci = carrier_to_idx[cid]
    pred_peak[cid] = {s: float(peak[ci, 0, s]) for s in obs_streams}
r_peak = rank_true({c: norm_mse(obs, pred_peak[c]) for c in sorted_carriers})
print(f"峰值场(抹风向) rank = {r_peak}")

# 2) 数值解（时变 advection-diffusion）
pred_num = {}
for k, cid in enumerate(sorted_carriers):
    n = carrier_src_native[cid]
    six, siy = n % NX, n // NX
    pk = run_peak(six, siy)
    pred_num[cid] = {s: float(pk[stream_native[s] % NX, stream_native[s] // NX]) for s in obs_streams}
    if (k + 1) % 40 == 0:
        print(f"  数值解 {k+1}/{len(sorted_carriers)}", flush=True)
r_num = rank_true({c: norm_mse(obs, pred_num[c]) for c in sorted_carriers})
print(f"数值解(时变, D={DC}) rank = {r_num}")

# 3) 时变 Gaussian plume（参照）
def plume_field(sx, sy, u, v, k=0.5):
    speed = max(np.hypot(u, v), 1e-3)
    cosd, sind = u / speed, v / speed
    pred = {}
    for s, (x, y) in stream_xy.items():
        dx = (x - sx) * cosd + (y - sy) * sind
        dy = -(x - sx) * sind + (y - sy) * cosd
        if dx <= 0.15:
            pred[s] = 0.0
        else:
            sigma = k * dx + 0.3
            pred[s] = (1.0 / sigma) * np.exp(-dy**2 / (2 * sigma**2)) / dx
    return pred
winds = []
for wi in range(11):
    winds.append((float(np.mean(wind_u[wi])), float(np.mean(wind_v[wi]))))
carrier_xy = {cid: native_xy[n] for cid, n in carrier_src_native.items()}
pred_plume = {}
for cid in sorted_carriers:
    sx, sy = carrier_xy[cid]
    acc = {s: 0.0 for s in stream_xy}
    for u, v in winds:
        pf = plume_field(sx, sy, u, v)
        for s in stream_xy:
            acc[s] = max(acc[s], pf[s])
    pred_plume[cid] = acc
r_plume = rank_true({c: norm_mse(obs, {s: pred_plume[c][s] for s in obs_streams}) for c in sorted_carriers})
print(f"时变 Gaussian plume rank = {r_plume}")
