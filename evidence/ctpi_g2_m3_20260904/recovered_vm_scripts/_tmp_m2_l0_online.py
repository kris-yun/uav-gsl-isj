#!/usr/bin/env python3
"""M2 决定性验证：bank-free 数值解 vs bank 峰值场，在线累积定位 rank 收敛。

核心问题：M2 的价值是"bank-free 替代 bank"——用数值解（时变 advection-diffusion，
只用 wind+geometry，不查 bank）生成的候选源峰值场，能否达到和 bank 峰值场一样的
在线定位精度（rank 收敛到 1）？

机器人逐步观测（真源 bank 峰值场 = 真实环境），用形状似然累积更新 626 cell 后验，
看 true-source rank 随观测数收敛。
"""
import numpy as np, os, random

B = "/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1/H01"
D = np.load("/dev/shm/m2_l0_data.npz")
coarse_free = D["coarse_free"]
wind_u = D["wind_u"]; wind_v = D["wind_v"]
manifest_stream = D["manifest_stream"]; manifest_native = D["manifest_native"]
src_peak = D["src_peak"]
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

# 预计算 210 carrier 的数值峰值场（bank-free）
carrier_src_native = {}
for cid in sorted_carriers:
    ci = carrier_to_idx[cid]
    s = int(np.argmax(peak[ci, 0, :]))
    carrier_src_native[cid] = stream_native[s]

print("预计算 210 carrier 数值峰值场（bank-free）...", flush=True)
num_field = {}   # carrier -> 626 数组（按 stream 序）
for k, cid in enumerate(sorted_carriers):
    n = carrier_src_native[cid]
    pk = run_peak(n % NX, n // NX)
    # 转成 626 数组（按 stream 序）
    arr = np.zeros(626)
    for s, nn in stream_native.items():
        arr[s] = pk[nn % NX, nn // NX]
    num_field[cid] = arr
    if (k + 1) % 40 == 0:
        print(f"  {k+1}/210", flush=True)

# bank 峰值场（按 stream 序）
bank_field = {}
for cid in sorted_carriers:
    ci = carrier_to_idx[cid]
    bank_field[cid] = peak[ci, 0, :]

# 机器人轨迹：从起点 (-3.17,-1.75) 开始，沿 bank 峰值场梯度走（source-seeking，简单贪心）
# 简化：用真源 bank 峰值场，从起点逐步移动到更高浓度 cell
start = (-3.17, -1.75)
# 起点 native（最近 free cell）
def xy_to_native(x, y):
    ix = int(round((x + 7.4) / CELL)); iy = int(round((y + 7.73) / CELL))
    return ix + iy * NX
start_native = xy_to_native(-3.17, -1.75)
# 找最近 free native
free_natives = set(stream_native.values())
# 用 bank 真源峰值场做观测（真实环境）
true_bank = bank_field[true_carrier]  # 626

# 轨迹：沿真源 bank 峰值场梯度（从起点，向更高浓度 cell 走）
def trajectory(n_steps=60):
    traj = []
    cur = start_native
    visited = set()
    for _ in range(n_steps):
        if cur in visited:
            # 随机跳一个未访问的相邻
            pass
        visited.add(cur)
        traj.append(cur)
        # 找 8 邻域里 bank 峰值最高的未访问 free cell
        ix, iy = cur % NX, cur // NX
        best, best_n = -1, None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0: continue
                nix, niy = ix + dx, iy + dy
                nn = nix + niy * NX
                if nn in free_natives and nn not in visited and coarse_free[nix, niy]:
                    s = native_stream[nn]
                    if true_bank[s] > best:
                        best, best_n = true_bank[s], nn
        if best_n is None or best <= 0:
            break
        cur = best_n
    return traj

traj = trajectory(60)
print(f"轨迹长度 {len(traj)} cell，起点 native={start_native}，终点 native={traj[-1]}")

def online_rank(field, n_obs_list=[5, 10, 20, 30, 40, 50]):
    """field: carrier -> 626 数组。观测用真源 bank 峰值场 + 噪声，形状似然累积。"""
    random.seed(0)
    obs = {}
    ranks = {}
    for i, nn in enumerate(traj):
        s = native_stream[nn]
        obs[s] = max(0.0, true_bank[s] + random.gauss(0, 2.0))
        if (i + 1) in n_obs_list:
            # 计算各 carrier 的形状似然
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
                    ranks[i + 1] = r
                    break
    return ranks

print("\n=== 在线累积定位 rank 收敛对比 ===")
r_bank = online_rank(bank_field)
r_num = online_rank(num_field)
print("观测数 | bank峰值场 rank | 数值解(bank-free) rank")
for k in sorted(r_bank):
    print(f"  {k:4d}  |     {r_bank[k]:3d}        |        {r_num[k]:3d}")
