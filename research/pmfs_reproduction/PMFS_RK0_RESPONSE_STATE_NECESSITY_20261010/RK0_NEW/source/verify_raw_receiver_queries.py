"""Independent portable GADEN 3.0/ZLIB filament receiver-query verification.

Only saved snapshots, occupancy CSV, source time/hash tables, and native query
CSVs are read. No GADEN/ROS executable, physics generation, or candidate
forward is called. This supports this locked point-source/filament format;
other serialization layouts stop explicitly rather than being guessed.

Default is read-only JSON stdout. --out must be a new path for detailed CSV.
Requires NumPy for explicitly rounded float32 vector arithmetic.
"""
import sys
sys.dont_write_bytecode=True
import argparse,bisect,csv,hashlib,json,math,struct,time,zlib
from pathlib import Path
import numpy as np

F=np.float32
RTOL=5e-6
ATOL=3e-7
PI_CUBED=F(math.pi*math.pi*math.pi)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def csv_rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

class Reader:
    def __init__(self,data):self.data=data;self.offset=0
    def values(self,fmt):
        n=struct.calcsize('<'+fmt);out=struct.unpack_from('<'+fmt,self.data,self.offset);self.offset+=n;return out
    def string(self):
        n=self.values('Q')[0];assert n<1000
        out=self.data[self.offset:self.offset+n].decode('ascii');self.offset+=n;return out

def snapshot(path):
    b=path.read_bytes();assert b[:13]==b'GADEN_RESULT\x00', 'unsupported pre-3.0 snapshot'
    mode=b[13];expected_size=struct.unpack_from('<Q',b,14)[0]
    if mode==1:raw=zlib.decompress(b[22:])
    elif mode==0:raw=b[22:]
    else:raise AssertionError('unsupported compression mode; libBSC not independently decoded')
    assert len(raw)==expected_size
    r=Reader(raw);version=r.values('ii');assert version==(3,0),version
    dims=np.array(r.values('iii'),dtype=np.int64)
    minimum=np.array(r.values('fff'),dtype=np.float32);maximum=np.array(r.values('fff'),dtype=np.float32)
    cell=F(r.values('f')[0]);kind=r.string();assert kind=='point', 'unsupported source serialization'
    source=np.array(r.values('fff'),dtype=np.float32);gas=r.values('i')[0]
    moles,allgases=map(F,r.values('ff'));wind=r.values('i')[0]
    assert r.string()=='filaments', 'only filament playback supported'
    n=r.values('Q')[0];assert len(raw)-r.offset==16*n
    filaments=np.frombuffer(raw,dtype='<f4',offset=r.offset,count=4*n).reshape(n,4).copy()
    assert np.isfinite(filaments).all() and (filaments[:,3]>0).all()
    assert moles>0 and allgases>0
    return dict(dimensions=dims,minimum=minimum,maximum=maximum,cell_size=cell,source=source,
                gas_type=gas,total_moles=moles,all_gas_moles=allgases,wind_index=wind,filaments=filaments)

def occupancy(path):
    lines=path.read_text(encoding='utf-8').splitlines()
    minimum=np.array([float(x) for x in lines[0].split()[1:]],dtype=np.float32)
    maximum=np.array([float(x) for x in lines[1].split()[1:]],dtype=np.float32)
    dims=np.array([int(x) for x in lines[2].split()[1:]],dtype=np.int64);cell=F(lines[3].split()[1])
    data=np.full((dims[2],dims[0],dims[1]),255,dtype=np.uint8);x=z=0
    for line in lines[4:]:
        if line.strip()==';':z+=1;x=0
        else:
            a=[int(v) for v in line.split()];assert len(a)==dims[1]
            data[z,x,:]=a;x+=1
    assert z==dims[2] and not (data==255).any()
    return dict(dimensions=dims,minimum=minimum,maximum=maximum,cell_size=cell,data=data)

def cell_state(point,desc,occ):
    # Native glm float division followed by integer conversion truncates toward
    # zero. Using floor here would change the native environment predicate.
    index=np.trunc((point-desc['minimum'])/desc['cell_size']).astype(np.int64)
    if (index<0).any() or (index>=desc['dimensions']).any():return 3
    return int(occ['data'][index[2],index[0],index[1]])

def dot_sqr(v):
    # gaden::vmath::sqrlength explicitly accumulates x,y,z in float order.
    s=F(0)
    for x in v:s=F(s+F(x*x))
    return s
def length(v):return F(math.sqrt(float(dot_sqr(v))))

def los(start,end,desc,occ):
    if cell_state(start,desc,occ)!=0 or cell_state(end,desc,occ)!=0:return False
    vector=end-start;distance=length(vector);steps=int(F(distance/desc['cell_size']))
    # Native computes a float division by zero for steps=0 but has no loop
    # iterations. The endpoint checks already determine its true result.
    if steps<=1:return True
    vector=vector/distance;increment=F(distance/F(steps))
    for i in range(1,steps):
        point=start+vector*F(increment*F(i))
        if cell_state(point,desc,occ)!=0:return False
    return True

def concentration(point,desc,occ):
    point=np.array(point,dtype=np.float32)
    if cell_state(point,desc,occ)==3:return F(0),dict(eligible=0,LOS_blocked=0,contributors=0)
    total=F(0);eligible=blocked=contributors=0
    for filament in desc['filaments']:
        delta=filament[:3]-point;sigma=filament[3]
        distance_sqr=dot_sqr(delta)
        limit=F(F(sigma*F(3))/F(100))
        if not distance_sqr<F(limit*limit):continue
        eligible+=1
        if not los(point,filament[:3],desc,occ):blocked+=1;continue
        distance_cm=F(F(100)*length(delta))
        exponent=F(-F(distance_cm*distance_cm)/F(F(F(2)*sigma)*sigma))
        # sqrt/exp are unqualified C math functions returning double in the
        # locked source header environment. Their argument arithmetic is float.
        denominator=math.sqrt(float(F(F(8)*PI_CUBED)))*float(sigma)*float(sigma)*float(sigma)
        num_moles_cm3=F(float(desc['total_moles'])/denominator)
        center=F(1e6*float(num_moles_cm3)/float(desc['all_gas_moles']))
        contribution=F(float(center)*math.exp(float(exponent)))
        total=F(total+contribution);contributors+=1
    return total,dict(eligible=eligible,LOS_blocked=blocked,contributors=contributors)

def ULP_gap(a,b):
    assert a>=0 and b>=0
    return abs(struct.unpack('<I',struct.pack('<f',a))[0]-struct.unpack('<I',struct.pack('<f',b))[0])

def verify(package):
    start=time.perf_counter()
    native=package/'native_reference_evidence';assert native.is_dir()
    geom=package/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv'
    if not geom.exists():raise AssertionError('portable occupancy input missing; pass a complete package')
    occ=occupancy(geom);records=[];banks=[];files_checked={str(geom.relative_to(package)):sha(geom)}
    maximum_abs=maximum_rel=0.;maximum_ulp=0;event_disagreements=0;used=0
    eligible=blocked=contributors=0
    for bank in sorted((native/'realizations').iterdir()):
        if not bank.is_dir():continue
        output=csv_rows(bank/'QUERY_OUTPUT.csv');receivers=[r for r in output if r['query_id'].startswith('receiver_')]
        assert len(receivers)==51 and len({r['query_id'] for r in receivers})==51
        query_input={r['query_id']:r for r in csv_rows(bank/'QUERIES.csv') if r['query_id'].startswith('receiver_')}
        frame_manifest={int(r['frame']):r for r in csv_rows(bank/'ALL_FRAME_SHA256_AND_TIME.csv')}
        lineage={('receiver_b'+r['block_id']+'_v'+r['membership_branch']):r for r in csv_rows(bank/'QUERY_PHYSICAL_LINEAGE.csv')}
        cache={};count_start=len(records)
        for row in receivers:
            frame=int(row['frame']);path=bank/'bank'/('iteration_'+str(frame))
            if frame not in cache:
                digest=sha(path);assert digest==frame_manifest[frame]['SHA256']
                files_checked[str(path.relative_to(package))]=digest
                cache[frame]=snapshot(path);used+=1
                d=cache[frame]
                assert np.array_equal(d['dimensions'],occ['dimensions'])
                assert np.array_equal(d['minimum'],occ['minimum']) and np.array_equal(d['maximum'],occ['maximum']) and d['cell_size']==occ['cell_size']
                assert d['wind_index']==10 and d['gas_type']==13
            desc=cache[frame];query=query_input[row['query_id']]
            point=np.array([F(float(row[k])) for k in ['x','y','z']],dtype=np.float32)
            assert np.array_equal(point,np.array([F(float(query[k])) for k in ['x','y','z']],dtype=np.float32))
            assert cell_state(point,desc,occ)==int(row['physical_free'])-1==0
            t=lineage[row['query_id']];assert int(t['selected_frame'])==frame
            assert float(t['selected_frame_physical_s'])==float(frame_manifest[frame]['physical_snapshot_time_s'])
            assert float(t['next_frame_physical_s'])==float(frame_manifest[frame+1]['physical_snapshot_time_s'])
            assert int(frame_manifest[frame]['filaments'])==len(desc['filaments'])
            assert int(frame_manifest[frame]['wind_index'])==desc['wind_index']
            assert float(t['selected_frame_physical_s'])<=float(t['target_physical_s'])<float(t['next_frame_physical_s'])
            value,counts=concentration(point,desc,occ);expected=F(float(row['ppm_float32']))
            absolute=abs(float(value)-float(expected));relative=absolute/max(abs(float(expected)),1e-30);ulp=ULP_gap(value,expected)
            passed=absolute<=ATOL+RTOL*abs(float(expected));assert passed,(bank.name,row['query_id'],value,expected,absolute,relative)
            native_hit=bool(expected>F(.1));verified_hit=bool(value>F(.1));event_disagreements+=native_hit!=verified_hit
            maximum_abs=max(maximum_abs,absolute);maximum_rel=max(maximum_rel,relative);maximum_ulp=max(maximum_ulp,ulp)
            eligible+=counts['eligible'];blocked+=counts['LOS_blocked'];contributors+=counts['contributors']
            records.append(dict(opaque_realization=bank.name,query_id=row['query_id'],frame=frame,native_ppm=float(expected),independent_float32_ppm=float(value),
              absolute_difference=absolute,relative_difference=relative,ULP_difference=ulp,native_event_at_0_1=int(native_hit),independent_event_at_0_1=int(verified_hit),
              threshold_margin=abs(float(expected)-float(F(.1))),**counts))
        banks.append(dict(opaque_realization=bank.name,receiver_queries=len(records)-count_start,used_snapshots=len(cache),all_queries_within_frozen_tolerance=True))
    assert len(banks)==8 and len(records)==408 and used==392 and event_disagreements==0
    result=dict(verdict='PASS_INDEPENDENT_RAW_FILAMENT_RECEIVER_CONCENTRATION_RECOMPUTATION',
      completed_queries=408,complete_realizations=8,used_snapshots_SHA256_passed=392,occupancy_sha256=sha(geom),
      maximum_absolute_ppm_difference=maximum_abs,maximum_relative_difference=maximum_rel,maximum_ULP_difference=maximum_ulp,
      receiver_threshold_event_disagreements=event_disagreements,minimum_native_distance_from_threshold=min(r['threshold_margin'] for r in records),
      cutoff_eligible_filament_query_pairs=eligible,LOS_blocked_pairs=blocked,contributing_pairs=contributors,
      fixed_tolerance=dict(relative=RTOL,absolute_ppm=ATOL),wall_seconds=time.perf_counter()-start,banks=banks,
      actual_execution='Python independent decode/arithmetic verification of saved data only; no native Simulation/ROS/forward calls',
      limitations=['Only GADEN3.0 point-source filament serialization with ZLIB or uncompressed payload is supported.',
                  'Cross-platform libm and float32 rounding tolerated; this is not an unqualified bitwise replay.',
                  'Only 51 receiver branches per realization are recomputed, not the 22,797 grid queries.',
                  'Numerical operator reproduction does not prove independent physical-model validity or source identifiability.'],
      source_math_conventions=['Strict distanceSqr < (3*sigma/100)^2 cutoff, source-file order float accumulation.',
                               'sigma/distance in cm conversion and header-stored mole constants retained.',
                               'LOS tests both endpoints then steps i=1..floor_float(distance/cellSize)-1 with float32 arithmetic.',
                               'Environment coordinate conversion uses float32 and truncation toward zero, not mathematical floor.',
                               'Unqualified sqrt/exp double returns verified separately with locked header environment.'],
      input_sha256=files_checked)
    return result,records

def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--out',type=Path)
    a=p.parse_args();result,rows=verify(a.package)
    if a.out:
        a.out.mkdir(exist_ok=False)
        (a.out/'RAW_RECEIVER_QUERY_VERIFY_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        with (a.out/'RAW_RECEIVER_QUERY_COMPARISON.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
