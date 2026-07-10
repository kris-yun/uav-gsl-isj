import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import subprocess
import re

# Extract trajectory from Full_s0 log
result = subprocess.run(
    ['ssh', 'zyc@192.168.111.128', 
     "grep 'OPGSL-AI step=' /tmp/v8_exp/ablation/Full_s0.log | sed 's/.*step=\\([0-9]*\\) (\\([^)]*\\)) hits=\\([0-9]*\\) t=\\([0-9.]*\\)/\\1|\\2|\\3|\\4/'"],
    capture_output=True, text=True
)

steps, xs, ys, ts = [], [], [], []
for line in result.stdout.strip().split('\n'):
    parts = line.split('|')
    if len(parts) == 4:
        try:
            step = int(parts[0])
            coords = parts[1].split(',')
            x, y = float(coords[0]), float(coords[1])
            t = float(parts[3])
            # Filter corrupted data
            if abs(x) < 10 and abs(y) < 10:
                steps.append(step)
                xs.append(x)
                ys.append(y)
                ts.append(t)
        except:
            pass

# Source location for H01_gnd
src_x, src_y = -0.40, -2.90

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: Trajectory
ax1 = axes[0]
ax1.plot(xs, ys, 'b.-', label='UAV trajectory', markersize=4, linewidth=1)
ax1.plot(xs[0], ys[0], 'go', markersize=10, label='Start')
ax1.plot(xs[-1], ys[-1], 'rs', markersize=10, label='End')
ax1.plot(src_x, src_y, 'r*', markersize=15, label='True source')
ax1.set_xlabel('X (m)')
ax1.set_ylabel('Y (m)')
ax1.set_title('UAV Trajectory (Full model, seed 0, H01\\_gnd)')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_aspect('equal')

# Plot 2: Distance to source over time
ax2 = axes[1]
dists = [np.sqrt((x - src_x)**2 + (y - src_y)**2) for x, y in zip(xs, ys)]
ax2.plot(ts, dists, 'b-', linewidth=2)
ax2.axhline(y=3.0, color='r', linestyle='--', label='Success threshold (3m)')
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Distance to source (m)')
ax2.set_title('Convergence (Full model, seed 0)')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('D:/ZYC/A-gas/ASCi/sci/paper-isj-final-en/figures/fig_trajectory.pdf', dpi=300, bbox_inches='tight')
plt.savefig('D:/ZYC/A-gas/ASCi/sci/paper-isj-final-en/figures/fig_trajectory.png', dpi=150, bbox_inches='tight')
print(f"Trajectory plot saved. {len(steps)} steps, final dist={dists[-1]:.2f}m")
