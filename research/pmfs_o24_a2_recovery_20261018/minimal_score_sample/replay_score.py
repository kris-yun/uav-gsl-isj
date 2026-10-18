from pathlib import Path
import csv,json,math
import numpy as np
R=Path(__file__).resolve().parent
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8')))
g=json.loads((R/'geometry_and_identity.json').read_text());m=rows(R/'measurement_and_posterior.csv');c=rows(R/'candidates.csv');data=(R/'candidate_maps.f32').read_bytes();nx,ny=g['nx'],g['ny'];idx=np.array([int(x['col'])+nx*int(x['row'])for x in m]);lo=np.array([float(x['hit_log_odds'])for x in m]);alpha=np.array([float(x['hit_confidence'])for x in m]);observed=1-1/(1+np.exp(lo));grid=np.zeros(nx*ny);errs=[]
for row in sorted(c,key=lambda x:-int(x['size_x'])*int(x['size_y'])):
 h=np.frombuffer(data,dtype='<f4',count=int(row['count']),offset=int(row['offset_bytes']));v=1+((1-np.abs(observed-h[idx])*g['D'])-1)*alpha;s=float(np.prod(v));native=float(row['score']);errs.append(abs(s-native)/max(abs(native),1e-280));x,y,sx,sy=[int(row[k])for k in ['origin_x','origin_y','size_x','size_y']];grid.reshape(ny,nx)[y:y+sy,x:x+sx]=s
p=grid[idx];p/=p.sum();saved=np.array([float(x['source_probability'])for x in m]);error=float(np.max(np.abs(p-saved)));assert max(errs)<1e-10 and error<1e-10
out=dict(status='PASS_SAVED_NATIVE_SCORE_AND_POSTERIOR_REPLAY',role=g['role'],update=g['update'],candidate_maps=len(c),source_cells=len(m),max_score_relative_error=max(errs),posterior_max_abs_error=error,new_forward_calls=0,new_ROS_goals=0)
(R/'REPLAY_RESULT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
