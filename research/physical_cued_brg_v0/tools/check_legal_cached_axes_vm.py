import csv,json
from pathlib import Path
import numpy as np
r=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
for e in range(3):
 p=r/f'full_support/inputs/env_{e}/sources.csv';rows=list(csv.DictReader(p.open()));print('HEAD',e,rows[0])
 m=json.loads((r/f'full_support/inputs/env_{e}/meta.json').read_text());legal=set(np.flatnonzero(np.fromfile(r/f'legal_support_v2/env_{e}_occupancy.u8',np.uint8)).tolist())
 cols=set(rows[0]);cell_key=next((x for x in ['cell','grid_index','source_cell','index'] if x in cols),None)
 if cell_key:cache={int(x[cell_key]) for x in rows}
 else:cache={int(x['source_id'].split('_')[1])+m['width']*int(x['source_id'].split('_')[2]) for x in rows}
 print(json.dumps({'environment':e,'cache_count':len(cache),'legal':len(legal),'missing_from_cache':sorted(legal-cache),'illegal_cache_count':len(cache-legal)}))
