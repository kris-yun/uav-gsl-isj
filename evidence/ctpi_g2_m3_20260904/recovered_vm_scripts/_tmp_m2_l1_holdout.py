#!/usr/bin/env python3
"""M2 L1 held-out 验证：D 从 H01 标定(0.01)，H02 直接复用，bank-free 跨环境在线定位。

验证 M2 的最终目标：陌生 House 不跑 GADEN bank、不重新标定 D，
只用 wind+geometry 就能达到 rank 收敛。
"""
import numpy as np, os, csv, random, struct

HOUSE = "H03"
B = f"/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1/{HOUSE}"
SCEN = {"H02": "House02", "H03": "House03"}[HOUSE]
H = f"/mnt/hgfs/workspace/GADEN_files/scenarios/{SCEN}"
DC = 0.01  # 从 H01 标定，跨环境复用

# H02/H03 参数
PARAMS = {
    "H02": dict(env_min=(-5.39273, -7.45088, -1.00095), fine=(83, 119, 26),
                coarse=(27, 39), cell=631, carrier=201,
                src=(0.00, -1.00), z_idx=13,
                wind_cfg="3,5-1_fast", wind_src="0.00_-1.00_0.20"),
    "H03": dict(env_min=(-0.85, -1.863, -0.9505), fine=(138, 83, 25),
                coarse=(46, 27), cell=626, carrier=206,
                src=(-0.45, 1.90), z_idx=12,
                wind_cfg="1-2,5_fast", wind_src="-0.45_1.90_-0.10"),
}
P = PARAMS[HOUSE]
NX, NY = P["coarse"]
CELL = 0.3
FNX, FNY, FNZ = P["fine"]
NCELL3 = FNX * FNY * FNZ

# ---- cell_manifest ----
manifest = []
with open(os.path.join(B, "cell_manifest.csv")) as f:
    r = csv.reader(f); next(r)
    for row in r:
        manifest.append((int(row[0]), int(row[1]), float(row[2]), float(row[3])))
stream_native = {s: n for s, n, x, y in manifest}
native_stream = {n: s for s, n, x, y in manifest}
stream_xy = {s: (x, y) for s, n, x, y in manifest}

# ---- free 掩码直接用 cell_manifest（精确，避免 reduce 边界问题）----
coarse_free = np.zeros((NX, NY), dtype=bool)
for s, n in stream_native.items():
    coarse_free[n % NX, n // NX] = True
print(f"{HOUSE}: coarse free={coarse_free.sum()} (bank cell={P['cell']})")

# ---- occupancy（仅用于 wind reduce 不需要，wind 直接从 fine 平均）----

# ---- wind -> coarse ----
WIND = os.path.join(H, "gas_simulations", P["wind_cfg"],
    f"FilamentSimulation_gasType_10_sourcePosition_{P['wind_src']}", "wind")
wind_u = np.zeros((11, NX, NY)); wind_v = np.zeros((11, NX, NY))
for wi in range(11):
    arr = np.frombuffer(open(os.path.join(WIND, f"wind_iteration_{wi}"), "rb").read(), dtype=np.float64)
    u = arr[:NCELL3].reshape(FNX, FNY, FNZ)[:, :, P["z_idx"]]
    v = arr[NCELL3:2*NCELL3].reshape(FNX, FNY, FNZ)[:, :, P["z_idx"]]
    for ix in range(NX):
        for iy in range(NY):
            wind_u[wi, ix, iy] = np.nanmean(u[ix*3:ix*3+3, iy*3:iy*3+3])
            wind_v[wi, ix, iy] = np.nanmean(v[ix*3:ix*3+3, iy*3:iy*3+3])

# ---- bank 峰值场 ----
peak = np.fromfile(os.path.join(B, "g2m1_peak_field.bin"), dtype=np.float32, offset=20)
cc, mc, cellc = P["carrier"], 8, P["cell"]
peak = peak.reshape(cc, mc, cellc)
member_dir = os.path.join(B, "worlds", "member_00")
sorted_carriers = sorted(f[:-4] for f in os.listdir(member_dir) if f.endswith(".bin"))
carrier_to_idx = {c: i for i, c in enumerate(sorted_carriers)}

# ---- 找真源 carrier（峰值 cell 最接近已知源位置）----
env_x0, env_y0, _ = P["env_min"]
src_x, src_y = P["src"]
def xy_to_ixiy(x, y):
    ix = int(round((x - env_x0 - 0.15) / CELL))
    iy = int(round((y - env_y0 - 0.15) / CELL))
    return ix, iy
src_ix, src_iy = xy_to_ixiy(src_x, src_y)
src_native = src_ix + src_iy * NX
# 真源 carrier = 峰值 cell 距离源 < 1 cell 的 carrier
true_carrier = None
for cid in sorted_carriers:
    ci = carrier_to_idx[cid]
    s = int(np.argmax(peak[ci, 0, :]))
    n = stream_native[s]
    if abs(n % NX - src_ix) <= 1 and abs(n // NX - src_iy) <= 1:
        true_carrier = cid
        break
print(f"{HOUSE}: 真源={src_x,src_y} -> cell({src_ix},{src_iy}) native={src_native}, carrier={true_carrier}")
true_bank = peak[carrier_to_idx[true_carrier], 0, :]

# ---- 数值解 ----
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

# 每个 carrier 的源 cell + 数值峰值场
print(f"{HOUSE}: 预计算 {cc} carrier 数值峰值场 (bank-free, D={DC})...", flush=True)
carrier_src_native = {}
num_field = {}
for k, cid in enumerate(sorted_carriers):
    ci = carrier_to_idx[cid]
    s = int(np.argmax(peak[ci, 0, :]))
    n = stream_native[s]
    carrier_src_native[cid] = n
    pk = run_peak(n % NX, n // NX)
    arr = np.zeros(cellc)
    for ss, nn in stream_native.items():
        arr[ss] = pk[nn % NX, nn // NX]
    num_field[cid] = arr
    if (k + 1) % 40 == 0:
        print(f"  {k+1}/{cc}", flush=True)

bank_field = {cid: peak[carrier_to_idx[cid], 0, :] for cid in sorted_carriers}

# ---- 在线累积定位（轨迹沿真源 bank 峰值场梯度）----
free_natives = set(stream_native.values())
START = {"H02": (-0.50, -2.50), "H03": (2.00, 0.00)}[HOUSE]
_start_ix, _start_iy = xy_to_ixiy(*START)
start_native = _start_ix + _start_iy * NX
if start_native not in free_natives:
    # 找最近 free cell
    start_native = min(free_natives, key=lambda n: abs(n % NX - _start_ix) + abs(n // NX - _start_iy))
print(f"{HOUSE}: 起点={START} -> native={start_native}")
def trajectory(n_steps=60):
    traj = []; visited = set(); cur = start_native
    for _ in range(n_steps):
        visited.add(cur); traj.append(cur)
        ix, iy = cur % NX, cur // NX
        best, best_n = -1, None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0: continue
                nix, niy = ix + dx, iy + dy
                nn = nix + niy * NX
                if nn in free_natives and nn not in visited and coarse_free[nix, niy]:
                    sv = true_bank[native_stream[nn]]
                    if sv > best:
                        best, best_n = sv, nn
        if best_n is None or best <= 0:
            break
        cur = best_n
    return traj

traj = trajectory(60)
print(f"{HOUSE}: 轨迹长度 {len(traj)}")

def online_rank(field, n_obs_list=[5, 10, 20, 30, 40, 50]):
    random.seed(0)
    obs = {}; ranks = {}
    for i, nn in enumerate(traj):
        s = native_stream[nn]
        obs[s] = max(0.0, true_bank[s] + random.gauss(0, 2.0))
        if (i + 1) in n_obs_list:
            obs_vec = np.array([obs[ss] for ss in obs])
            on = obs_vec / (obs_vec.max() + 1e-9)
            scores = {}
            for cid in sorted_carriers:
                f = field[cid]
                pv = np.array([f[ss] for ss in obs])
                pn = pv / (pv.max() + 1e-9)
                scores[cid] = -np.mean((on - pn)**2)
            ordered = sorted(scores.items(), key=lambda kv: -kv[1])
            for r, (cid, _) in enumerate(ordered, 1):
                if cid == true_carrier:
                    ranks[i + 1] = r; break
    return ranks

r_bank = online_rank(bank_field)
r_num = online_rank(num_field)
print(f"\n=== {HOUSE} held-out 在线累积定位 (D={DC} 从 H01 复用) ===")
print("观测数 | bank峰值场 rank | 数值解(bank-free) rank")
for k in sorted(r_bank):
    print(f"  {k:4d}  |     {r_bank[k]:3d}        |        {r_num[k]:3d}")
