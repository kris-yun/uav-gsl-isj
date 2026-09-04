#!/usr/bin/env python3
"""M3 offline falsification v2（向量化）：动作选择策略对比。

对比 random / exploit / myopic-EIG / non-myopic-EIG 的 true-source rank 收敛。
用 M2 bank-free 数值解做环境。
"""
import numpy as np, os, random

B = "/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1/H01"
D = np.load("/dev/shm/m2_l0_data.npz")
coarse_free = D["coarse_free"]
wind_u = D["wind_u"]; wind_v = D["wind_v"]
manifest_stream = D["manifest_stream"]; manifest_native = D["manifest_native"]
src_native = int(D["src_native"])

NX, NY = 29, 38
CELL = 0.3
DC = 0.01
stream_native = {int(s): int(n) for s, n in zip(manifest_stream, manifest_native)}
native_stream = {int(n): int(s) for s, n in zip(manifest_stream, manifest_native)}

peak = np.fromfile(os.path.join(B, "g2m1_peak_field.bin"), dtype=np.float32, offset=20).reshape(210, 8, 626)
member_dir = os.path.join(B, "worlds", "member_00")
sorted_carriers = sorted(f[:-4] for f in os.listdir(member_dir) if f.endswith(".bin"))
carrier_to_idx = {c: i for i, c in enumerate(sorted_carriers)}
true_carrier = "quadtree_22_16_2_2"
true_idx = carrier_to_idx[true_carrier]

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

def run_peak(six, siy, T_total=300.0, wind_cycle=11):
    dt = min(1.0, 0.4 * CELL * CELL / DC)
    C = np.zeros((NX, NY)); pk = np.zeros((NX, NY))
    steps = int(T_total / dt); seg = max(1, steps // wind_cycle)
    for wi in range(wind_cycle):
        u2d = wind_u[wi]; v2d = wind_v[wi]
        for _ in range(seg):
            C = advance(C, u2d, v2d, dt, (six, siy))
            np.maximum(pk, C, out=pk)
    return pk

# 210 carrier 数值场矩阵 (210, 626) 按 stream 序
print("预计算 210 carrier 数值峰值场...", flush=True)
num_mat = np.zeros((210, 626))
for ci, cid in enumerate(sorted_carriers):
    s = int(np.argmax(peak[carrier_to_idx[cid], 0, :]))
    n = stream_native[s]
    pk = run_peak(n % NX, n // NX)
    for ss, nn in stream_native.items():
        num_mat[ci, ss] = pk[nn % NX, nn // NX]
true_bank = peak[true_idx, 0, :]

free_streams = sorted(stream_native.keys())
NC = len(free_streams)
free_idx = np.array(free_streams)  # 用于索引 num_mat 的列

def be(p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return -p * np.log2(p) - (1 - p) * np.log2(1 - p)

def myopic_scores(carrier_mass, ref=5.0):
    """向量化：返回 (626,) 的 myopic EIG 分数。"""
    cm = np.array([carrier_mass[c] for c in sorted_carriers])
    ph = num_mat / (num_mat + ref)          # (210, 626)
    mixture = cm @ ph                        # (626,)
    cond = cm @ be(ph)                       # (626,)
    return np.maximum(0.0, be(mixture) - cond)

def update_posterior(carrier_mass, obs_idx_list, obs_vals, like_scale=0.5):
    cm = np.array([carrier_mass[c] for c in sorted_carriers])
    ov = np.array(obs_vals)
    if ov.max() <= 0:
        return carrier_mass.copy()
    on = ov / ov.max()
    pv = num_mat[:, obs_idx_list]           # (210, nobs)
    pv = pv / (pv.max(axis=1, keepdims=True) + 1e-9)
    logp = -like_scale * np.mean((on[None, :] - pv)**2, axis=1) + np.log(cm + 1e-12)
    logp -= logp.max()
    p = np.exp(logp); p /= p.sum()
    return {c: float(p[ci]) for ci, c in enumerate(sorted_carriers)}

def true_rank(carrier_mass):
    cm = np.array([carrier_mass[c] for c in sorted_carriers])
    return int((cm > cm[true_idx]).sum()) + 1

def run_episode(strategy, seed=0, n_steps=40):
    random.seed(seed); np.random.seed(seed)
    carrier_mass = {c: 1.0 / len(sorted_carriers) for c in sorted_carriers}
    visited = set()
    true_native = src_native
    start_s = max(free_streams, key=lambda s: abs(stream_native[s] % NX - true_native % NX) + abs(stream_native[s] // NX - true_native // NX))
    cur = start_s
    obs_idx = []; obs_vals = []
    ranks = {}
    for step in range(n_steps):
        visited.add(cur)
        obs_idx.append(cur); obs_vals.append(max(0.0, true_bank[cur] + random.gauss(0, 2.0)))
        carrier_mass = update_posterior(carrier_mass, obs_idx, obs_vals)
        ranks[step + 1] = true_rank(carrier_mass)
        avail = [s for s in free_streams if s not in visited]
        if not avail: break
        if strategy == "random":
            cur = random.choice(avail)
        elif strategy == "exploit":
            cm = np.array([carrier_mass[c] for c in sorted_carriers])
            exp_val = cm @ num_mat            # (626,) 后验加权浓度
            cur = max(avail, key=lambda s: exp_val[s])
        elif strategy == "myopic":
            sc = myopic_scores(carrier_mass)
            cur = max(avail, key=lambda s: sc[s])
        elif strategy == "nonmyopic":
            gamma = 0.8
            sc = myopic_scores(carrier_mass)
            top = sorted(avail, key=lambda s: -sc[s])[:15]
            total = {s: sc[s] for s in top}
            for ss in top:
                ev = float(np.array([carrier_mass[c] for c in sorted_carriers]) @ num_mat[:, ss])
                m2 = update_posterior(carrier_mass, obs_idx + [ss], obs_vals + [max(0.0, ev)])
                s2 = myopic_scores(m2)
                cand2 = [j for j in avail if j != ss]
                lookahead = max(s2[j] for j in cand2) if cand2 else 0.0
                total[ss] = sc[ss] + gamma * lookahead
            cur = max(total, key=total.get)
    return ranks

print("=== M3 动作选择策略对比（true-source rank 随采样步数，越小越好）===", flush=True)
for strat in ["random", "exploit", "myopic", "nonmyopic"]:
    checks = [5, 10, 15, 20, 25, 30, 35, 40]
    agg = {k: [] for k in checks}
    for seed in range(4):
        ranks = run_episode(strat, seed=seed)
        for k in checks:
            if k in ranks: agg[k].append(ranks[k])
    line = f"{strat:10s} |"
    for k in checks:
        line += f" {int(np.mean(agg[k])):4d}" if agg[k] else "  -- "
    print(line, flush=True)
print("(rank 1=完美定位；210=完全错误)")
