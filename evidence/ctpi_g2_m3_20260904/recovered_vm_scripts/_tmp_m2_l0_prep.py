#!/usr/bin/env python3
"""L0 prep: 构建 coarse grid (29x38) 的 free 掩码 + wind 场 + 坐标，验证与 cell_manifest 一致。
输出 /dev/shm/m2_l0_data.npz
"""
import numpy as np, os, csv

H = "/mnt/hgfs/workspace/GADEN_files/scenarios/House01"
B = "/mnt/hgfs/workspace/CPIR_M1_FULLGRID_LOOKUP_20260831_R1/H01"
WIND = os.path.join(H, "gas_simulations/2,4-1_fast/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30/wind")
FINE_NX, FINE_NY, FINE_NZ = 87, 114, 33
COARSE_NX, COARSE_NY = 29, 38
SCALE = 3
FLIGHT_Z = 13  # flight_height=0.3 -> z_idx=13
NCELL = FINE_NX * FINE_NY * FINE_NZ

# ---- 1. cell_manifest: 626 free cell (stream, native, x, y) ----
manifest = []  # (stream, native, x, y)
with open(os.path.join(B, "cell_manifest.csv")) as f:
    r = csv.reader(f); next(r)
    for row in r:
        manifest.append((int(row[0]), int(row[1]), float(row[2]), float(row[3])))
stream_xy = {s: (x, y) for s, n, x, y in manifest}
stream_native = {s: n for s, n, x, y in manifest}
native_xy = {n: (x, y) for s, n, x, y in manifest}

# ---- 2. occupancy (z=13 层) -> 87x114 -> reduce 到 29x38 ----
lines = open(os.path.join(H, "OccupancyGrid3D.csv")).read().splitlines()
data = [l for l in lines if l.strip() and not l.startswith("#") and ";" not in l]
assert len(data) == 33 * 87, f"occupancy 数据行 {len(data)} != {33*87}"
occ3d = np.array([[int(v) for v in l.split()] for l in data], dtype=np.int8).reshape(33, 87, 114)
occ2d = occ3d[FLIGHT_Z]  # 87 x 114, 1=occupied/obstacle, 0=free
print(f"occ2d (z={FLIGHT_Z}): shape={occ2d.shape}, free={int((occ2d==0).sum())}, obs={int((occ2d==1).sum())}")

# reduce: coarse free 当且仅当 3x3 全 free
coarse_free = np.ones((COARSE_NX, COARSE_NY), dtype=bool)
for ix in range(COARSE_NX):
    for iy in range(COARSE_NY):
        block = occ2d[ix*SCALE:ix*SCALE+SCALE, iy*SCALE:iy*SCALE+SCALE]
        coarse_free[ix, iy] = (block == 0).all()
n_free = int(coarse_free.sum())
print(f"coarse free={n_free}, obstacle={COARSE_NX*COARSE_NY-n_free}, total={COARSE_NX*COARSE_NY}")

# 验证：cell_manifest 的 native -> (ix,iy) 都应是 free，且数量一致
manifest_free = np.zeros((COARSE_NX, COARSE_NY), dtype=bool)
for s, n, x, y in manifest:
    ix, iy = n % COARSE_NX, n // COARSE_NX
    manifest_free[ix, iy] = True
mismatch = int((coarse_free != manifest_free).sum())
print(f"coarse_free vs manifest_free mismatch = {mismatch} (期望 0)")
print(f"manifest_free count = {int(manifest_free.sum())} (期望 626)")

# ---- 3. wind: 11 iteration, z=13 层 -> 87x114 (u,v) -> reduce 到 29x38 ----
wind_u = np.zeros((11, COARSE_NX, COARSE_NY))
wind_v = np.zeros((11, COARSE_NX, COARSE_NY))
for wi in range(11):
    arr = np.frombuffer(open(os.path.join(WIND, f"wind_iteration_{wi}"), "rb").read(), dtype=np.float64)
    u = arr[:NCELL].reshape(FINE_NX, FINE_NY, FINE_NZ)[:, :, FLIGHT_Z]
    v = arr[NCELL:2*NCELL].reshape(FINE_NX, FINE_NY, FINE_NZ)[:, :, FLIGHT_Z]
    for ix in range(COARSE_NX):
        for iy in range(COARSE_NY):
            bu = u[ix*SCALE:ix*SCALE+SCALE, iy*SCALE:iy*SCALE+SCALE]
            bv = v[ix*SCALE:ix*SCALE+SCALE, iy*SCALE:iy*SCALE+SCALE]
            wind_u[wi, ix, iy] = np.nanmean(bu)
            wind_v[wi, ix, iy] = np.nanmean(bv)
print("wind 11 iteration 平均 u,v (coarse):")
for wi in range(11):
    print(f"  it{wi}: u={np.nanmean(wind_u[wi]):+.4f} v={np.nanmean(wind_v[wi]):+.4f}")

# ---- 4. 真源 carrier 峰值场 (ground truth) ----
peak = np.fromfile(os.path.join(B, "g2m1_peak_field.bin"), dtype=np.float32, offset=20)
cc, cellc, mc = 210, 626, 8
peak = peak.reshape(cc, mc, cellc)
member_dir = os.path.join(B, "worlds", "member_00")
sorted_carriers = sorted(f[:-4] for f in os.listdir(member_dir) if f.endswith(".bin"))
carrier_to_idx = {c: i for i, c in enumerate(sorted_carriers)}
true_carrier = "quadtree_22_16_2_2"
true_idx = carrier_to_idx[true_carrier]
src_peak = peak[true_idx, 0, :]
src_stream = int(np.argmax(src_peak))          # stream ordinal
src_native = int(stream_native[src_stream])    # 正确: stream -> native
src_ix, src_iy = src_native % COARSE_NX, src_native // COARSE_NX
src_xy = stream_xy[src_stream]
print(f"真源 carrier={true_carrier}, stream={src_stream}, native={src_native}, (ix,iy)=({src_ix},{src_iy}), (x,y)=({src_xy[0]:.2f},{src_xy[1]:.2f})")

# ---- 保存 ----
np.savez_compressed("/dev/shm/m2_l0_data.npz",
    coarse_free=coarse_free, wind_u=wind_u, wind_v=wind_v,
    src_stream=src_stream, src_native=src_native, src_xy=np.array(src_xy),
    manifest_stream=np.array([m[0] for m in manifest], dtype=np.int64),
    manifest_native=np.array([m[1] for m in manifest], dtype=np.int64),
    manifest_x=np.array([m[2] for m in manifest]),
    manifest_y=np.array([m[3] for m in manifest]),
    src_peak=src_peak,
)
print("保存到 /dev/shm/m2_l0_data.npz 完成")
