"""Read-only posthoc envelope; never a scoring operator or LOS bypass."""
import math,struct
import numpy as np
from analyze import O,OLD,load,rows,table

def main():
    points=rows(O/'inputs/E3_UNIQUE_POINTS.csv');physical=rows(OLD/'PHYSICAL_WINDOWS.csv');constant=load(O/'inputs/E3_CONSTANTS.json');result=[]
    target=[next(r for r in physical if r['group']=='historical' and int(r['stop'])==s) for s in range(8,14)]
    xyz=np.array([[float(points[int(r['point_id'])][k]) for k in ['x','y','z']] for r in target])
    for source in ['true','rival']:
        for pred in load(O/'PREREGISTERED_HISTORY_CONTRACT.json')['prediction_streams']:
            series=[]
            with (O/'runs'/f'{source_placeholder(source,pred)}.particles.bin').open('rb') as stream:
                while raw:=stream.read(8):
                    step,n=struct.unpack('<2I',raw);a=np.frombuffer(stream.read(n*16),dtype='<f4').reshape(n,4).astype(float)
                    d2=(np.sum((a[:,None,:2]-xyz[None,:,:2])**2,axis=2)+(.7-xyz[None,:,2])**2)*10000
                    center=1e6*constant['moles_per_filament']/(math.sqrt(8*math.pi**3)*a[:,2]**3*constant['air_moles_per_cm3'])*a[:,3]
                    series.append(np.sum(center[:,None]*np.exp(-d2/(2*a[:,2,None]**2)),axis=0))
            v=np.array(series)
            for j,r in enumerate(target):
                for count in [3,4,5]:
                    q=v[:200//count*count,j].reshape(-1,count).mean(1)
                    result.append(dict(source=source,prediction=pred['id'],history='long220',stop=r['stop'],samples_per_window=count,max_no_LOS_untruncated_upper_ppm=float(q.max()),upper_below_threshold=bool(q.max()<.1),posthoc_diagnostic_only=True,used_for_score_or_rescue=False))
    table(O/'LONG_HISTORY_READONLY_UPPER_ENVELOPE.csv',result)
    print([r for r in result if r['source']=='true' and r['samples_per_window']==4])

def source_placeholder(source,pred):return f'E3_{source}_{pred["id"]}_long220'

if __name__=='__main__':main()
