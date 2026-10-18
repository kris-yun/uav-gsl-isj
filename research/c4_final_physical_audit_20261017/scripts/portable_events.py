"""NumPy saved-frame observation replay, independent of ROS and native libraries.

This observes existing 3D snapshots. It does not simulate transport or construct
a candidate-source reference bank. Native C++ bit parity is separately archived.
"""
from pathlib import Path
import csv,struct,zlib,json,sys,math,time
import numpy as np
R=Path(__file__).resolve().parents[1]
def rows(p):return list(csv.DictReader(p.open()))
def frame(f):
    b=(R/f'inputs/physical_frames/iteration_{f}').read_bytes();assert b[:13]==b'GADEN_RESULT\0' and b[13]==1
    a=zlib.decompress(b[22:]);assert len(a)==struct.unpack_from('<Q',b,14)[0]
    dims=np.array(struct.unpack_from('<3i',a,8));lo=np.array(struct.unpack_from('<3f',a,20),dtype='f4');step=np.float32(struct.unpack_from('<f',a,44)[0])
    L=struct.unpack_from('<Q',a,48)[0];off=56+L;assert a[56:off]==b'point'
    mass,air=struct.unpack_from('<2f',a,off+16)
    L=struct.unpack_from('<Q',a,off+28)[0];o=off+36+L;assert a[off+36:o]==b'filaments'
    N=struct.unpack_from('<Q',a,o)[0];o+=8;assert len(a)==o+N*16
    fs=np.frombuffer(a,'<f4',offset=o).reshape(N,4)
    return fs,dims,lo,step,np.float32(mass),np.float32(air)
def replay(out):
    start=time.monotonic();out=Path(out);assert not out.exists();out.mkdir(parents=True)
    grid=(R/'inputs/OccupancyGrid3D.csv').read_text().splitlines();dims=np.array([int(x) for x in grid[2].split()[1:]])
    cube=np.asarray([[int(x) for x in s.split()] for s in grid[4:] if s!=';'],dtype='u1').reshape(dims[2],dims[0],dims[1])
    meta=rows(R/'inputs/C4_update_1/metadata.csv')[0];ox,oy,gridstep=[np.float32(meta[k]) for k in ['origin_x','origin_y','cell_size']]
    old={int(x['serial']):x for x in rows(R/'results/PHYSICAL_EVENTS.csv')};result=[];cache={}
    for q in rows(R/'inputs/physical_queries.csv'):
        f=int(q['frame'])
        if f not in cache:cache={f:frame(f)}
        fs,dims,lo,step,mass,air=cache[f];xyz=fs[:,:3];sigma=fs[:,3];p=np.array([q['x'],q['y'],q['z']],dtype='f4')
        delta=xyz-p;d2=np.sum(delta*delta,axis=1,dtype='f4');limit=sigma*np.float32(3)/np.float32(100)
        ids=np.flatnonzero(d2<limit*limit);target=xyz[ids];s=sigma[ids];dist=np.sqrt(d2[ids]);steps=(dist/step).astype('i4')
        # Exact native LOS rule: free endpoints, then points at distance/steps.
        def free(points):
            ijk=np.trunc((points-lo)/step).astype('i4');inside=np.all((ijk>=0)&(ijk<dims),axis=1);v=np.zeros(len(points),bool)
            z=ijk[inside];v[inside]=cube[z[:,2],z[:,0],z[:,1]]==0;return v
        valid=free(target)&free(p[None,:])[0]
        with np.errstate(divide='ignore',invalid='ignore'):
            direction=(target-p)/dist[:,None];increment=dist/steps.astype('f4')
        for k in range(1,int(steps.max(initial=0))):
            use=np.flatnonzero(valid&(steps>k))
            if len(use):valid[use]&=free(p+direction[use]*(increment[use]*np.float32(k))[:,None])
        ids=ids[valid];s=s[valid]
        # ConcentrationAtCenter converts the per-filament gas quantity to ppm;
        # sigma and distance are cm, all gas amount constants are from the frame.
        denom=np.sqrt(8*float(np.float32(math.pi**3)))*s.astype('f8')**3
        center=(mass/denom).astype('f4');center=(np.float32(1e6)*center/air).astype('f4')
        distance_cm=np.float32(100)*np.sqrt(d2[ids]);exponent=-(distance_cm*distance_cm)/(np.float32(2)*s*s)
        v=(center*np.exp(exponent)).astype('f4')
        ppm=float(np.cumsum(v,dtype='f4')[-1]) if len(v) else 0.
        xy=np.trunc((xyz[:,:2]-np.array([ox,oy],dtype='f4'))/gridstep).astype('i4')
        pi=np.trunc((p[:2]-np.array([ox,oy],dtype='f4'))/gridstep).astype('i4');samexy=np.all(xy==pi,axis=1)
        samez=(xyz[:,2]>=p[2]-gridstep*np.float32(.5))&(xyz[:,2]<p[2]+gridstep*np.float32(.5))
        vox=np.all(np.trunc((xyz-lo)/step).astype('i4')==np.trunc((p-lo)/step).astype('i4'),axis=1)
        native=old[int(q['serial'])];error=abs(ppm-float(native['recorded_ppm']));assert error<=1e-5,(q['serial'],error)
        assert int(samexy.sum())==int(native['native_projected_centres'])
        assert int((samexy&samez).sum())==int(native['native_xy_sensor_slab_centres'])
        assert int(vox.sum())==int(native['physical_voxel_centres'])
        result.append(dict(serial=q['serial'],frame=f,ppm_numpy=ppm,ppm_historical=float(native['recorded_ppm']),absolute_error=error,projected_centres=int(samexy.sum()),slab_centres=int((samexy&samez).sum()),voxel_centres=int(vox.sum())))
    with (out/'REPLAY_EVENTS.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    receipt=dict(status='PASS_PORTABLE_SAVED_FRAME_OBSERVER',queries=len(result),max_abs_ppm_error=max(x['absolute_error'] for x in result),tolerance=1e-5,
      all_centre_counts_exact=True,worlds_generated=0,transport_advances=0,ROS_calls=0,wall_s=time.monotonic()-start,numpy=np.__version__)
    (out/'REPLAY_PASS.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
if __name__=='__main__':replay(sys.argv[1])
