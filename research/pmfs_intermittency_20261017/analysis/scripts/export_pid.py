"""ROS message deserialization only: does not initialize rclpy or any node."""
from pathlib import Path
import json,csv
from rclpy.serialization import deserialize_message
from olfaction_msgs.msg import GasSensor
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA';out=R/'results/RAW_PID_MESSAGES.csv';rows=[]
for e in json.loads((P/'CASE_INDEX.json').read_text())['cases']:
 root=P/e['native_path']
 for line in (root/'runtime/raw_ros_cdr.jsonl').open():
  a=json.loads(line)
  if 'PID/Sensor_reading' not in a['topic']:continue
  m=deserialize_message(bytes.fromhex(a['cdr_hex']),GasSensor);assert m.raw_units==3 and m.technology==51
  rows.append(dict(case=e['case'],sensor_stamp_ns=m.header.stamp.sec*10**9+m.header.stamp.nanosec,receipt_ns=int(a['receipt_ns']),raw_ppm=float(m.raw),raw_units=int(m.raw_units),technology=int(m.technology)))
with out.open('w',newline='') as f:w=csv.DictWriter(f,rows[0]);w.writeheader();w.writerows(rows)
print(json.dumps(dict(raw_PID_messages=len(rows),cases=len({r['case'] for r in rows}),new_ROS_nodes=0,scope='Exact CDR deserialization, not a new world/sensor experiment. Zero receipt stamps preserved, never used to fabricate alignment.')))
