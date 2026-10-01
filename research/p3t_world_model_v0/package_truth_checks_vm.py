"""Retain eight truth center files and original occupancy for review; post-result only."""
import hashlib,json,tarfile
from pathlib import Path
root=Path('/mnt/hgfs/workspace');bank=root/'P3T_D0_CENTERS_20261001'
with tarfile.open(root/'P3T_D0_TRUTH_CENTER_AND_OCCUPANCY.tar.gz','w:gz') as t:
 for case in ['House01_seed0_off_off','House01_seed1_off_off','House02_seed0_off_off','House02_seed1_off_off']:
  cid='quadtree_23_16_1_1' if case.startswith('House01') else 'quadtree_16_21_5_1'
  for arm in ['oracle2d','oracle3d']:
   p=bank/case/arm/'trajectories'/f'{cid}.trajbin';t.add(p,arcname=str(p.relative_to(bank)))
 for house in ['House01','House02']:
  p=root/'GADEN_files/scenarios'/house/'OccupancyGrid3D.csv';t.add(p,arcname=house+'/OccupancyGrid3D.csv')
