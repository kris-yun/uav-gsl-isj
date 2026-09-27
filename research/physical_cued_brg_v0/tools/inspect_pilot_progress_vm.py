from pathlib import Path
import json
r=Path('/mnt/hgfs/workspace/_staging/BRG_NATIVE615_PILOT_P1_V2_20260927')
for p in sorted(r.glob('source_*__*.json')):
 a=json.loads(p.read_text());print(json.dumps({k:a.get(k) for k in ['case_id','arm','status','geometric_success','final_source_error_m','wall_time_s','measurement_count','hit_count']}))

for raw in sorted(r.glob('source_*__*_raw')):
 b=raw/'beliefs.jsonl'
 if b.exists() and b.stat().st_size:
  x=json.loads(b.read_text().splitlines()[-1]);print(raw.name,'last_belief_time',x['search_time_s'],'events',x['brg_event_count'])
