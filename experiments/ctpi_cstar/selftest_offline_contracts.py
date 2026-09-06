from __future__ import annotations
import csv, json, tempfile, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from common.trace_io import load_manifest,load_episode
from m1_picr.offline import candidate_grid
from m2_cpo.offline import samples_from_episode

def write(path,header,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)

def make_episode(root,source=(100.,100.)):
    write(root/'sensor_trace.csv',['sim_time','gas_ppm'],[(0.2,0.0),(0.4,0.2),(0.6,0.0),(0.8,0.3)]+[(1.0+i*.2,0.2 if i==5 else 0.0) for i in range(40)])
    write(root/'sim_pose_trace.csv',['sim_time','pose_x','pose_y'],[(0.0,1,2),(0.4,9,9)]+[(.8+i*.2,1+i*.05,2) for i in range(42)])
    write(root/'wind_trace.csv',['sim_time','wind_u','wind_v'],[(0.0,1,0),(0.4,2,0)]+[(.8+i*.2,1,0) for i in range(42)])
    m={'episodes':[{'episode_id':'e','house':'H','source_xy':list(source),'sensor_trace':str(root/'sensor_trace.csv'),'pose_trace':str(root/'sim_pose_trace.csv'),'wind_trace':str(root/'wind_trace.csv')}]};(root/'m.json').write_text(json.dumps(m));return load_episode(load_manifest(root/'m.json')[0])

def main():
    with tempfile.TemporaryDirectory() as td:
        r=Path(td);ep=make_episode(r)
        assert ep.pose_x[0]==1 and ep.pose_y[0]==2, (ep.pose_x[0],ep.pose_y[0])
        assert ep.wind_u[0]==1,ep.wind_u[0]
        g1=candidate_grid(ep);ep2=make_episode(r,source=(-999.,777.));g2=candidate_grid(ep2);assert g1==g2
        rows=samples_from_episode(ep,horizon=8,stride=1000);assert rows
        first=rows[0]
        for i in range(11,len(ep.wind_u)): ep.wind_u[i]=123.;ep.wind_v[i]=-77.
        second=samples_from_episode(ep,horizon=8,stride=1000)[0]
        assert first[0]==second[0] and first[1]==second[1] and first[2]==second[2]
    print('CSTAR_OFFLINE_CAUSAL_CONTRACT_SELFTEST PASS')
if __name__=='__main__':main()
