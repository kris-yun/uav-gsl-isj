#!/usr/bin/env python3
"""List allowed existing native assets; never read sealed/H03 observations."""
import argparse,hashlib,json,os
from pathlib import Path

RUNS={f'{prefix}_r{i:02d}' for prefix in ('ocb_r2_cfg00','ocb_r2_s2x_x00') for i in range(1,5)}
DENY=('sealed','confirmation','holdout','house03','h03')
p=argparse.ArgumentParser();p.add_argument('--root',action='append',required=True);p.add_argument('--out',required=True)
a=p.parse_args();records=[];missing=[]
for arg in a.root:
    root=Path(arg)
    if not root.exists():missing.append(str(root));continue
    for parent,dirs,files in os.walk(root):
        dirs[:]=[d for d in dirs if not any(x in d.lower() for x in DENY)]
        parent=Path(parent)
        for name in files:
            if any(x in name.lower() for x in DENY):continue
            path=parent/name;is_world=bool(set(path.parts)&RUNS)
            if name=='OccupancyGrid3D.csv':
                records.append({'path':str(path.resolve()),'type':'occupancy','bytes':path.stat().st_size,
                                'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            elif is_world and (name.endswith('MANIFEST.json') or name=='BUILD_PROVENANCE.md'):
                records.append({'path':str(path.resolve()),'type':'open_discovery_metadata','bytes':path.stat().st_size,
                                'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            elif is_world and ('iteration' in name.lower() or 'simulation' in name.lower() or name.endswith('.bin')):
                # Inventory only. Actual native bytes require the extraction step.
                records.append({'path':str(path.resolve()),'type':'existing_native_frame_inventory_only','bytes':path.stat().st_size})
out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
receipt={'status':'DISCOVERY_ONLY_NO_PHYSICAL_QUALIFICATION','missing_roots':missing,'records':records,
         'authorized_run_ids':sorted(RUNS),'sealed_or_h03_content_opened':False,'new_physics_generated':False}
out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print(json.dumps({'files':len(records),'missing_roots':missing}))
