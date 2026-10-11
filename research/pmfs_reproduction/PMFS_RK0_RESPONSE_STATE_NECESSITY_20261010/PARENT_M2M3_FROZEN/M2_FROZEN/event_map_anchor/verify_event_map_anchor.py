import sys
sys.dont_write_bytecode=True
import argparse,csv,hashlib,json,math
from pathlib import Path
def read(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def verify(root):
    got=read(root/'vm_evidence/observed_anchor/map.csv');expected=read(root/'frozen_expected_input.csv')
    assert len(got)==len(expected)==1530
    maxdiff={k:0. for k in ['logOdds','omega','confidence']};free=0
    for i,(a,b) in enumerate(zip(got,expected)):
        assert int(a['cell_index'])==int(b['cell_index'])==i
        assert a['occupancy']==b['occupancy']
        free+=int(a['occupancy'])==1
        for k in maxdiff:
            x=float(a[k]);y=float(b[k]);assert math.isfinite(x) and math.isfinite(y)
            maxdiff[k]=max(maxdiff[k],abs(x-y))
    assert free==447 and all(v==0. for v in maxdiff.values())
    events=read(root/'vm_evidence/observed_anchor/event_replay_ledger.csv')
    assert len(events)==50 and all(x['event_hit']=='1' for x in events)
    lineage=read(root/'vm_evidence/observed_anchor/event_cell_lineage.csv')
    assert len(lineage)==50*447
    execution=json.loads((root/'vm_evidence/observed_anchor/EXECUTION.json').read_text())
    assert execution['EstimateHitProbabilities_calls']==50
    assert all(execution[k]==0 for k in ['forward_calls','source_posterior_updates','ROS_nodes','GADEN_realizations'])
    if (root/'SHA256.json').exists():
        for x in json.loads((root/'SHA256.json').read_text()):assert hashlib.sha256((root/x['path']).read_bytes()).hexdigest()==x['sha256']
    return dict(verdict='OBSERVED_B4_NATIVE_EVENT_TO_MAP_ANCHOR_PASS',cell_count=1530,free_cells=447,maximum_absolute_difference=maxdiff,event_blocks=50,lineage_rows=len(lineage),new_forward_calls=0,new_physics_or_ROS=0)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    print(json.dumps(verify(p.parse_args().root),indent=2))
