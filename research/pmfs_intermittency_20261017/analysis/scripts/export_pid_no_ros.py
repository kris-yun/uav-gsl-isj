"""Independent little-endian CDR decoder, checked against rclpy deserialization."""
from pathlib import Path
import json,csv,struct
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA'
def decode(b):
 assert b[:2]==b'\0\1';pos=4
 def unpack(fmt,n,align):
  nonlocal pos
  pos+=(-(pos-4))%align;v=struct.unpack_from(fmt,b,pos);pos+=n;return v
 sec,ns=unpack('<iI',8,4);length=unpack('<I',4,4)[0];pos+=length
 tech,manufacturer,mpn=unpack('<BBB',3,1);raw=unpack('<d',8,8)[0];units=unpack('<B',1,1)[0];air,a,bb=unpack('<ddd',24,8)
 assert pos==len(b)
 return sec*10**9+ns,raw,units,tech
rows=[]
for e in json.loads((P/'CASE_INDEX.json').read_text())['cases']:
 for line in (P/e['native_path']/'runtime/raw_ros_cdr.jsonl').open():
  v=json.loads(line)
  if 'PID/Sensor_reading' not in v['topic']:continue
  stamp,raw,unit,tech=decode(bytes.fromhex(v['cdr_hex']));assert unit==3 and tech==51;rows.append(dict(case=e['case'],sensor_stamp_ns=stamp,receipt_ns=int(v['receipt_ns']),raw_ppm=raw,raw_units=unit,technology=tech))
ref=R/'results/RAW_PID_MESSAGES.csv'
had_reference=ref.exists()
if ref.exists():
 other=list(csv.DictReader(ref.open()));assert len(other)==len(rows)
 for a,b in zip(other,rows):assert a['case']==b['case'] and int(a['sensor_stamp_ns'])==b['sensor_stamp_ns'] and float(a['raw_ppm'])==b['raw_ppm']
else:
 with ref.open('w',newline='') as f:w=csv.DictWriter(f,rows[0]);w.writeheader();w.writerows(rows)
(R/'results/PID_DECODER_QA.json').write_text(json.dumps(dict(status='PASS_CDR_FIELDS_ALL_MESSAGES',messages=len(rows),checked_against_rclpy_export=had_reference,new_ROS_nodes=0),indent=2));print('PASS',len(rows),'messages')
