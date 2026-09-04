#!/usr/bin/env python3
"""L0 瞬态版（修复源坐标 bug + 数值稳定性）：标定 D + 形态对比。"""
import numpy as np, os

D = np.load("/dev/shm/m2_l0_data.npz")
coarse_free = D["coarse_free"]
wind_u = D["wind_u"]; wind_v = D["wind_v"]
manifest_stream = D["manifest_stream"]; manifest_native = D["manifest_native"]
src_peak = D["src_peak"]
src_native = int(D["src_native"])

NX, NY = 29, 38
CELL = 0.3
src_ix, src_iy = src_native % NX, src_native // NX
print(f"真源 native={src_native} (ix,iy)=({src_ix},{src_iy})")

# bank 峰值场 grid（用 C-order 正确映射: flat = ix + iy*NX）
bank_grid = np.zeros((NX, NY))
for s, n in zip(manifest_stream, manifest_native):
    bank_grid[int(n) % NX, int(n) // NX] = src_peak[int(s)]
print("bank 峰值场 argmax =", np.unravel_index(np.argmax(bank_grid), bank_grid.shape),
      "值 =", bank_grid.max(), "(应为", (src_ix, src_iy), ")")

def advance(C, u2d, v2d, dt, Dcoef):
    dx = CELL
    C_left = np.roll(C, 1, axis=0); C_left[0, :] = 0.0
    C_right = np.roll(C, -1, axis=0); C_right[-1, :] = 0.0
    C_down = np.roll(C, 1, axis=1); C_down[:, 0] = 0.0
    C_up = np.roll(C, -1, axis=1); C_up[:, -1] = 0.0
    dCdx = np.where(u2d >= 0, (C - C_left) / dx, (C_right - C) / dx)
    dCdy = np.where(v2d >= 0, (C - C_down) / dx, (C_up - C) / dx)
    adv = -u2d * dCdx - v2d * dCdy
    lap = (C_left + C_right + C_down + C_up - 4 * C) / (dx * dx)
    Cnew = C + dt * (adv + Dcoef * lap)
    Cnew = np.maximum(Cnew, 0.0)
    Cnew[src_ix, src_iy] += dt * 1.0
    Cnew[~coarse_free] = 0.0
    return Cnew

def run_transient(Dcoef, T_total=300.0, wind_cycle=11):
    dt = min(1.0, 0.4 * CELL * CELL / max(Dcoef, 1e-6))
    C = np.zeros((NX, NY)); peak = np.zeros((NX, NY))
    steps = int(T_total / dt)
    seg = max(1, steps // wind_cycle)
    for wi in range(wind_cycle):
        u2d = wind_u[wi]; v2d = wind_v[wi]
        for _ in range(seg):
            C = advance(C, u2d, v2d, dt, Dcoef)
            np.maximum(peak, C, out=peak)
    return peak

best_D, best_corr = None, -1
for Dcoef in [0.001, 0.003, 0.01, 0.03, 0.1]:
    pk = run_transient(Dcoef)
    pred = pk[coarse_free].flatten()
    gt = bank_grid[coarse_free].flatten()
    if pred.max() > 0 and gt.max() > 0:
        corr = np.corrcoef(pred / pred.max(), gt / gt.max())[0, 1]
    else:
        corr = -1
    # 峰值位置对比
    pk_amax = np.unravel_index(np.argmax(pk), pk.shape)
    print(f"D={Dcoef:.4f}: corr={corr:.4f}  数值峰值位置={pk_amax} (真源={src_ix,src_iy})")
    if corr > best_corr:
        best_corr, best_D = corr, Dcoef
print(f"最佳 D={best_D}, corr={best_corr:.4f}")
np.save("/dev/shm/m2_l0_bestD.npy", np.array([best_D]))
