import struct, os, math, statistics

# Read GADEN filament iteration files to extract detection statistics
# GADEN binary format: each filament has (x, y, z, mass) as floats
sim_dir = "D:/ZYC/A-gas/workspace/GADEN_files/scenarios/House01/gas_simulations/2,4-1_fast/FilamentSimulation_gasType_10_sourcePosition_-0.40_-2.90_-0.30"

# Source position from directory name
src_x, src_y, src_z = -0.40, -2.90, -0.30

# Read a few iteration files to understand the format
for it in [0, 10, 100, 500, 1000]:
    fname = os.path.join(sim_dir, "iteration_%d" % it)
    if not os.path.exists(fname):
        continue
    with open(fname, 'rb') as f:
        data = f.read()
    size = len(data)
    # Try to interpret as floats (4 bytes each)
    n_floats = size // 4
    print("iteration_%d: %d bytes, %d floats" % (it, size, n_floats))
    if n_floats > 0:
        floats = struct.unpack('<%df' % min(n_floats, 20), data[:min(n_floats, 20)*4])
        print("  First 20 floats:", [round(f, 4) for f in floats])