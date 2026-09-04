import numpy as np, os
D = np.load("/dev/shm/m2_l0_data.npz")
cf = D["coarse_free"]; wu = D["wind_u"]; wv = D["wind_v"]
mn = D["manifest_native"]; ms = D["manifest_stream"]
sn = {int(s): int(n) for s, n in zip(ms, mn)}
NX, NY = 29, 38; CELL = 0.3; DC = 0.01
src_native = int(D["src_native"]); six, siy = src_native % NX, src_native // NX
print("真源", (six, siy), "native", src_native)

def advance(C, u2d, v2d, dt):
    dx = CELL
    Cl = np.roll(C, 1, axis=0); Cl[0, :] = 0
    Cr = np.roll(C, -1, axis=0); Cr[-1, :] = 0
    Cd = np.roll(C, 1, axis=1); Cd[:, 0] = 0
    Cu = np.roll(C, -1, axis=1); Cu[:, -1] = 0
    dCdx = np.where(u2d >= 0, (C - Cl) / dx, (Cr - C) / dx)
    dCdy = np.where(v2d >= 0, (C - Cd) / dx, (Cu - C) / dx)
    adv = -u2d * dCdx - v2d * dCdy
    lap = (Cl + Cr + Cd + Cu - 4 * C) / (dx * dx)
    Cn = C + dt * (adv + DC * lap)
    Cn = np.maximum(Cn, 0); Cn[six, siy] += dt * 1.0; Cn[~cf] = 0
    return Cn

dt = min(1.0, 0.4 * CELL * CELL / DC)
# 单 wind it1（朝 +y）瞬时场
u2d = wu[1]; v2d = wv[1]
C = np.zeros((NX, NY))
for _ in range(int(300 / dt)):
    C = advance(C, u2d, v2d, dt)
amax = np.unravel_index(np.argmax(C), C.shape)
print("单 wind it1(朝+y) 瞬时场峰值位置 =", amax, "真源 =", (six, siy))
print("it1 wind: u=%.4f v=%.4f" % (np.mean(u2d), np.mean(v2d)))
# 峰值场（max over time，11 wind）
pk = np.zeros((NX, NY))
for wi in range(11):
    C = np.zeros((NX, NY))
    for _ in range(int(300 / dt)):
        C = advance(C, wu[wi], wv[wi], dt)
    np.maximum(pk, C, out=pk)
print("峰值场(max over time) 峰值位置 =", np.unravel_index(np.argmax(pk), pk.shape))
