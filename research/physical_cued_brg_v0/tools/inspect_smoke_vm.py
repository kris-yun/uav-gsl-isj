import json,sys
from pathlib import Path
import numpy as np
root=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
sys.path.insert(0,str(root))
from pmfs_brg.bank import TemplateBank
b=TemplateBank.load(root/'example_banks/h03_model_only.npz')
r=json.loads(Path('/home/zyc/brg_closedloop_20260927/native_software_smoke_01_raw/beliefs.jsonl').read_text().splitlines()[0])
a=set(r['free_cells']);c=set(b.cells.tolist())
print(json.dumps({'actual_free_count':len(a),'bank_count':len(c),'only_native':sorted(a-c),'only_bank':sorted(c-a),'same_order':r['free_cells']==b.cells.tolist(),'metadata':{k:r[k] for k in ('width','height','resolution','origin_x','origin_y')}},default=str,indent=2))
