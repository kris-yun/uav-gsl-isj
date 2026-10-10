"""Re-render frozen B4-M0 figures into an explicitly selected new directory. No simulation."""
import sys
sys.dont_write_bytecode=True
import argparse, importlib.util
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--audit',type=Path,default=Path(__file__).resolve().parent)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
assert not args.output.exists(), 'choose a new output directory'
assert not args.output.resolve().is_relative_to(args.audit.resolve()), 'do not modify the frozen audit package'
OUT=args.output.resolve();OUT.mkdir(parents=True)
spec=importlib.util.spec_from_file_location('m0',args.audit/'verify_m0.py')
m0=importlib.util.module_from_spec(spec);spec.loader.exec_module(m0)
computed=m0.analyse(args.audit/'evidence');result,cells=computed[0],computed[1]
# One full-map figure: measured hit map, both native predictions, cellwise attribution.
figures = OUT / 'figures'
figures.mkdir()
table = cells['update_2_FINAL_PEAK_FIXED']
free = np.array([r['free'] for r in table]).reshape(45, 34)
fields = [(r'Measured hit map $p_i$ (propagated)', 'measured_probability', 'viridis', 0, 1),
          ('True-neighbour 5 x 1 region prediction', 'true_hit', 'viridis', 0, 1),
          ('Wrong-MAP 1 x 1 region prediction', 'wrong_hit', 'viridis', 0, 1),
          (r'Cell attribution $\log f_W-\log f_T$', 'delta_log_wrong_over_true', 'RdBu_r', -.5, .5)]
extent = [-7.55, -7.55 + 34 * .25, -7.88, -7.88 + 45 * .25]
fig, axes = plt.subplots(2, 2, figsize=(10.4, 12.2), layout='constrained')
stops = result['observation']['stops']
true_leaf = result['updates'][-1]['pairs']['FINAL_PEAK_FIXED']['true_leaf']
wrong_leaf = result['updates'][-1]['pairs']['FINAL_PEAK_FIXED']['wrong_leaf']
for panel, ax, (title, key, colour, low, high) in zip('ABCD', axes.flat, fields):
    values = np.array([r[key] for r in table]).reshape(45, 34)
    masked = np.ma.masked_where(~free, values)
    cmap = plt.get_cmap(colour).copy()
    cmap.set_bad('#d9d9d9')
    image = ax.imshow(masked, origin='lower', extent=extent, cmap=cmap, vmin=low, vmax=high,
                      interpolation='nearest', aspect='equal')
    ax.scatter([s['x'] for s in stops], [s['y'] for s in stops], marker='o', s=26,
               facecolors='none', edgecolors='#00b4ff', linewidths=1.5, label='Direct stops (10)')
    ax.scatter([-3.2], [-3.3], c='black', s=85, marker='x', linewidths=2, label='True source projection')
    ax.scatter([-1.675], [1.495], c='#ff9f00', edgecolors='black', s=125, marker='*', label='Final wrong MAP')
    for leaf, color in [(true_leaf, 'black'), (wrong_leaf, '#ff9f00')]:
        x0, y0, x1, y1 = leaf['bounds_xy']
        ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fill=False, edgecolor=color, linewidth=1.4, linestyle='--'))
    for y in (1.7, 2.7):
        ax.axhline(y, color='#ae7700', linestyle=':', linewidth=1)
    ax.set_title(f'{panel}  {title}', loc='left', fontsize=10)
    ax.set_xlabel('World x (m)')
    ax.set_ylabel('World y (m)')
    fig.colorbar(image, ax=ax, shrink=.66, pad=.015)
axes[1, 1].legend(loc='lower left', fontsize=7, framealpha=.9)
fig.suptitle('Frozen B4-M0 attribution: native region predictions, no new simulation\n'
             'Red in D favours the wrong source; blue favours the true-neighbour region. Grey = excluded cells.', fontsize=11)
fig.savefig(figures / 'B4_M0_SPATIAL_ATTRIBUTION.png', dpi=210)
fig.savefig(figures / 'B4_M0_SPATIAL_ATTRIBUTION.pdf')
plt.close(fig)

cross = result['fixed_region_cross_map_scoring']
matrix = np.array([[next(r['log_ratio'] for r in cross if r['observation_update'] == f'update_{i}'
                        and r['maps_update'] == f'update_{j}') for j in range(3)] for i in range(3)])
fig, ax = plt.subplots(figsize=(6.6, 4.7), layout='constrained')
image = ax.imshow(matrix, cmap='YlOrRd', vmin=0, vmax=11)
for i in range(3):
    for j in range(3):
        ax.text(j, i, f'{matrix[i,j]:.3f}\n({np.exp(matrix[i,j]):,.1f}x)', ha='center', va='center',
                color='white' if matrix[i,j]>7 else 'black', fontsize=10)
ax.set_xticks(range(3), ['Update 0\n2 x 2 wrong leaf', 'Update 1\n1 x 1 wrong leaf', 'Update 2\n1 x 1 wrong leaf'])
ax.set_yticks(range(3), ['20 blocks', '35 blocks', '50 blocks'])
ax.set_xlabel('Frozen source-region prediction pair')
ax.set_ylabel('Frozen observation map')
ax.set_title('Conditional fixed-map scoring, log(wrong / true)\nNot native branches or independent physical trials', fontsize=11)
fig.colorbar(image, ax=ax, label='Log score ratio')
fig.savefig(figures / 'B4_M0_FIXED_MAP_DIAGNOSTIC.png', dpi=200)
fig.savefig(figures / 'B4_M0_FIXED_MAP_DIAGNOSTIC.pdf')
plt.close(fig)
