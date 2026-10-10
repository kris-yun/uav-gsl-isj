"""Read frozen B4 only; reconstruct physical sampling and document ambiguity."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import csv, gzip, json, hashlib, struct, re, collections

BASE = Path(__file__).resolve().parents[3]
B4 = BASE / 'outputs/PMFS_B4_OFFICIAL_TERMINAL_RESUMED_20261010'
OUT = Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def f32(v): return struct.unpack('<f', struct.pack('<f', v))[0]

class CDR:
    def __init__(self, h):
        b=bytes.fromhex(h)
        assert b[:2] == b'\x00\x01', 'requires CDR LE'
        self.b=b[4:]; self.o=0
    def n(self, code, size):
        self.o += (-self.o) % size
        v=struct.unpack_from('<'+code,self.b,self.o)[0]; self.o+=size
        return v
    def string(self):
        n=self.n('I',4); x=self.b[self.o:self.o+n];self.o+=n
        assert x[-1:] == b'\0'; return x[:-1].decode('utf8')
    def gas(self):
        sec=self.n('i',4); ns=self.n('I',4); frame=self.string()
        tech=self.n('B',1); manu=self.n('B',1); mpn=self.n('B',1)
        raw=self.n('d',8); units=self.n('B',1)
        air=self.n('d',8); a=self.n('d',8); b=self.n('d',8)
        assert self.o==len(self.b)
        return dict(stamp_ns=sec*10**9+ns, frame=frame, technology=tech, manufacturer=manu,mpn=mpn,raw=raw,raw_units=units,raw_air=air,calib_a=a,calib_b=b)
    def gas_response(self):
        n=self.n('I',4); positions=[]
        for _ in range(n):
            k=self.n('I',4); positions.append([self.n('d',8) for _ in range(k)])
        k=self.n('I',4); gases=[self.string() for _ in range(k)]
        assert self.o==len(self.b)
        return dict(concentrations=positions,gas_types=gases)

def rows(path): return list(csv.DictReader(path.open(encoding='utf8',newline='')))
def gzrows(path): return [json.loads(x) for x in gzip.open(path,'rt',encoding='utf8')]
def write_csv(name, arr):
    with (OUT/name).open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(arr[0]));w.writeheader();w.writerows(arr)

def run():
    runtime=B4/'runtime'
    consumer=rows(runtime/'consumer_messages.csv')
    gas=[dict(x,index=i) for i,x in enumerate(consumer) if x['kind']=='gas']
    ev=list(csv.reader((runtime/'measurement_events.csv').open(encoding='utf8',newline='')))
    durations=[tuple(map(float,x)) for x in re.findall(r'(\d+) gas measurements, (\d+) wind measurements over ([\d.]+) seconds',(runtime/'launch.log').read_text(encoding='utf8')) if int(x[0])>0]
    assert len(ev)==len(durations)==50
    assert all(a==1 and b==2 for a,b,d in durations)
    cdr_all=gzrows(runtime/'raw_ros_cdr.jsonl.gz')
    raw_gas=[dict(CDR(x['cdr_hex']).gas(),cdr_line=i+1,cdr_sha256=hashlib.sha256(bytes.fromhex(x['cdr_hex'])).hexdigest(),record_receipt_ns=x['receipt_ns']) for i,x in enumerate(cdr_all) if x['topic']=='/PioneerP3DX/PID/Sensor_reading']
    queries=gzrows(runtime/'service_queries.jsonl.gz')
    for x in queries:
        if x['kind']=='GasPosition':
            x.update(CDR(x['response_cdr_hex']).gas_response())
            # Sensor is float accumulation, not double sum.
            v=0.
            for c in x['concentrations'][0]: v=f32(v+c)
            x['PID']=v
    qgas=[x for x in queries if x['kind']=='GasPosition' and len(x['x'])==1 and abs(x['z'][0]+.2)<1e-6]
    clocks=rows(runtime/'physical_clock_trace.csv')
    clockgas=[x for x in clocks if x['reason']=='gas_service']
    full=[]; canon=[]; failures=[]; ambiguities=[]
    for j,(e,counts) in enumerate(zip(ev,durations)):
        end=int(e[0]); y=float(e[1]); duration=counts[2]
        possible=[x for x in gas if end-int(duration*1e9)-20_000_000<=int(x['receipt_ns'])<=end and f32(float(x['value']))==y]
        assert len(possible) in (1,2),(j,possible)
        if len(possible)>1: ambiguities.append(dict(block_id=j,reason='equal PID at receipt before boundary and exactly at update boundary; state-before-add not captured',consumer_indices=[x['index'] for x in possible]))
        for branch,x in enumerate(possible):
            stamp=int(x['stamp_ns']); val=float(x['value'])
            rr=[r for r in raw_gas if r['stamp_ns']==stamp and f32(r['raw'])==val and r['frame']==x['frame']]
            assert len(rr)==1,(j,'cdr',len(rr))
            r=rr[0]; assert r['raw_units']==3
            qq=[q for q in qgas if q['response_ns']<=stamp and q['PID']==val and abs(q['x'][0]-float(x['map_x']))<1e-5 and abs(q['y'][0]-float(x['map_y']))<1e-5 and stamp-q['response_ns']<=1_000_000_000]
            # In case repeated raw concentrations, timestamp proximity resolves request.
            assert qq,(j,'query missing')
            q=max(qq,key=lambda q:q['response_ns'])
            same=[z for z in clockgas if q['request_ns']<=int(z['receipt_ros_ns'])<=q['response_ns']]
            assert len(same)==1,(j,'physical clock',len(same),q['request_ns'],q['response_ns'])
            z=same[0]
            rec=dict(block_id=j,stop_id=int(e[6]),block_within_stop=int(e[7]),membership_branch=branch,membership_status='UNIQUE_RECOVERY' if len(possible)==1 else 'AMBIGUOUS_EQUAL_PID_BOUNDARY',accepted_gas_count=1,accepted_wind_count=2,native_window_elapsed_logged_s=duration,block_update_ros_ns=end,consumer_receipt_ns=int(x['receipt_ns']),sensor_stamp_ns=stamp,service_serial=q['serial'],service_request_ros_ns=q['request_ns'],service_response_ros_ns=q['response_ns'],physical_service_ros_ns=int(z['receipt_ros_ns']),physical_target_s=float(z['target_internal_s']),physical_frame=int(z['frame']),physical_frame_internal_s=float(z['frame_internal_s']),physical_next_frame_internal_s=float(z['next_frame_internal_s']),wind_index=int(z['wind_index']),sensor_frame=r['frame'],sensor_x=q['x'][0],sensor_y=q['y'][0],sensor_z=q['z'][0],robot_map_x=float(e[4]),robot_map_y=float(e[5]),observed_pid_ppm=val,observed_block_mean_ppm=y,observed_event=int(y>.1),block_wind_speed=float(e[2]),block_wind_direction_to=float(e[3]),consumer_row=x['index']+2,raw_cdr_line=r['cdr_line'],raw_cdr_sha256=r['cdr_sha256'],gas_type=';'.join(q['gas_types']),float_aggregate_exact_match=f32(val)==y)
            full.append(rec)
        # This is an explicitly provisional canonical choice. Not silently qualified.
        canon.append(full[-len(possible)])
    write_csv('FROZEN_RECEPTOR_SCHEDULE_ALL_MEMBERSHIP_BRANCHES.csv',full)
    write_csv('FROZEN_RECEPTOR_SCHEDULE_PROVISIONAL_EARLIER_BOUNDARY.csv',canon)
    write_csv('MAP_REPLAY_EVENT_COVARIATES.csv',[dict(block_id=i,stop_id=int(e[6]),update_ros_ns=int(e[0]),x=float(e[4]),y=float(e[5]),wind_speed=float(e[2]),wind_direction_to=float(e[3]),observed_event=int(float(e[1])>.1)) for i,e in enumerate(ev)])
    result=dict(verdict='49_BLOCKS_EXACT_CHAIN_PASS_ONE_BOUNDARY_MEMBERSHIP_HOLD',accepted_blocks=50,unique_membership_blocks=49,ambiguous_blocks=ambiguities,total_branch_rows=len(full),accepted_gas_count_all_blocks=1,all_float_block_aggregates_exact=True,PID=dict(model=30,correction_factors=False,raw_units=3,response='float sum of gas concentrations; no MOX dynamics'),window_durations=collections.Counter(str(d) for a,b,d in durations),query_sensor_z_range=[min(x['sensor_z'] for x in full),max(x['sensor_z'] for x in full)],physical_target_range=[min(x['physical_target_s'] for x in full),max(x['physical_target_s'] for x in full)],physical_frame_range=[min(x['physical_frame'] for x in full),max(x['physical_frame'] for x in full)],boundary_protocol='Use both predeclared membership alternatives for block40; do not count it twice. Primary source ranking only qualified if alternatives agree; otherwise HOLD.',input_sha256={str(p.relative_to(B4)):sha(p) for p in [runtime/'consumer_messages.csv',runtime/'measurement_events.csv',runtime/'raw_ros_cdr.jsonl.gz',runtime/'service_queries.jsonl.gz',runtime/'physical_clock_trace.csv',runtime/'launch.log']})
    (OUT/'FROZEN_RECEPTOR_SCHEDULE_RECOVERY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':run()
