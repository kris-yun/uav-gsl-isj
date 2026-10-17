"""Export each original consumer gas row once per case, no epoch duplication."""
from pathlib import Path
import csv,json,hashlib
R=Path(__file__).resolve().parents[1];data=[];counts={}
for case in ['C4','C3']:
    source=R/'inputs'/f'{case}_consumer_messages.csv'
    with source.open(encoding='utf-8',newline='') as f:original=list(csv.DictReader(f))
    count=0
    for i,a in enumerate(original):
        if a['kind']!='gas':continue
        data.append(dict(case=case,original_consumer_row=i+2,**a));count+=1
    counts[case]=dict(original_gas_rows=count,consumer_file_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
with (R/'analysis/RAW_PID_BY_CASE.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
assert len({(a['case'],a['original_consumer_row']) for a in data})==len(data)
(R/'lineage/PID_EXPORT_IDENTITY.json').write_text(json.dumps(dict(status='PASS_ONE_EXPORT_PER_ORIGINAL_CONSUMER_ROW',cases=counts,rows=len(data),
    raw_pid_unthresholded_csv='Update views: C4 observations appear for both update_0 and update_1; not additional independent samples.',
    raw_pid_by_case_csv='Original source callback rows exported once per case, retaining all original columns and original CSV row numbers.',
    independence_claim=False),indent=2),encoding='utf-8')
print('PASS_ORIGINAL_GAS_ROWS',len(data),counts)
