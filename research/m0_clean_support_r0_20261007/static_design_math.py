"""Only grid/field/trajectory algebra. No simulator, plume evolution or launcher."""
import hashlib
import struct
import numpy as np

SIM_LO=np.array([-16.,-20.,-8.])
SIM_HI=np.array([44.,20.,16.])
ROI_LO=np.array([-2.,-8.,1.])
ROI_HI=np.array([18.,8.,9.])
H=.25
U0=.08
SHEAR_AMPLITUDE=.04
Z0=5.
SHEAR_SCALE=1.5
W0=.005
ARMS=['U0','A_on','A_off','B_shear','B_speed']

def bump(q):
    q=np.asarray(q,dtype=float);a=np.zeros_like(q);inside=np.abs(q)<1
    a[inside]=np.exp(1-1/(1-q[inside]**2));return a

def coordinates():
    return [np.arange(lo+h/2,hi,h) for lo,hi,h in zip(SIM_LO,SIM_HI,[H]*3)]

def region_mask(x,y,z,roi=False):
    if roi: lo,hi=ROI_LO,ROI_HI
    else: lo,hi=SIM_LO+H,SIM_HI-H
    return ((z[:,None,None]>=lo[2])&(z[:,None,None]<hi[2])&
            (y[None,:,None]>=lo[1])&(y[None,:,None]<hi[1])&
            (x[None,None,:]>=lo[0])&(x[None,None,:]<hi[0]))

def field_recipes():
    x,y,z=coordinates();shape=(len(z),len(y),len(x),3)
    base=np.empty(shape,dtype='<f4');base[...,0]=(U0+SHEAR_AMPLITUDE*np.tanh((z-Z0)/SHEAR_SCALE))[:,None,None]
    base[...,1]=0;base[...,2]=W0
    bx=bump((x-6)/6);dx=(bump((x+H-6)/6)-bump((x-H-6)/6))/(2*H)
    bz=bump((z-Z0)/3)
    by=bump(y/2);dy=(bump((y+H)/2)-bump((y-H)/2))/(2*H)
    unit_u=bz[:,None,None]*dy[None,:,None]*bx[None,None,:]
    unit_v=-bz[:,None,None]*by[None,:,None]*dx[None,None,:]
    gain=.04/float(np.sqrt(unit_u**2+unit_v**2).max())
    # Flatten the task-height shear smoothly; leave guard-height winds intact.
    shear_delta=-SHEAR_AMPLITUDE*np.tanh((z-Z0)/SHEAR_SCALE)*bz
    b1=(base[:,0,0,0].astype(float)+shear_delta).astype('<f4')
    target=np.sum((b1.astype(float)-base[:,0,0,0])**2)
    low,high=0.,.1
    for _ in range(80):
        mid=(low+high)/2
        actual=(base[:,0,0,0].astype(float)+mid*bz).astype('<f4')
        energy=np.sum((actual.astype(float)-base[:,0,0,0])**2)
        if energy<target:low=mid
        else:high=mid
    def mismatch(k):
        actual=(base[:,0,0,0].astype(float)+k*bz).astype('<f4')
        return abs(np.sum((actual.astype(float)-base[:,0,0,0])**2)-target)
    b_gain=min([low,high],key=mismatch)
    return base,gain,b_gain

def make_field(arm,base,a_gain,b_gain):
    x,y,z=coordinates();f=base.copy()
    if arm.startswith('A_'):
        cy=0. if arm=='A_on' else 5.5
        bx=bump((x-6)/6);dx=(bump((x+H-6)/6)-bump((x-H-6)/6))/(2*H)
        by=bump((y-cy)/2);dy=(bump((y+H-cy)/2)-bump((y-H-cy)/2))/(2*H)
        bz=bump((z-Z0)/3)
        f[...,0]=(base[...,0].astype(float)+a_gain*bz[:,None,None]*dy[None,:,None]*bx[None,None,:]).astype('<f4')
        f[...,1]=(-a_gain*bz[:,None,None]*by[None,:,None]*dx[None,None,:]).astype('<f4')
    elif arm=='B_shear':
        delta=-SHEAR_AMPLITUDE*np.tanh((z-Z0)/SHEAR_SCALE)*bump((z-Z0)/3)
        f[...,0]=(base[...,0].astype(float)+delta[:,None,None]).astype('<f4')
    elif arm=='B_speed':
        f[...,0]=(base[...,0].astype(float)+b_gain*bump((z-Z0)/3)[:,None,None]).astype('<f4')
    return f

def divergence(f):
    a=f.astype(float)
    return ((a[1:-1,1:-1,2:,0]-a[1:-1,1:-1,:-2,0])+
            (a[1:-1,2:,1:-1,1]-a[1:-1,:-2,1:-1,1])+
            (a[2:,1:-1,1:-1,2]-a[:-2,1:-1,1:-1,2]))/(2*H)

def audit_fields():
    x,y,z=coordinates();base,ag,bg=field_recipes();global_mask=region_mask(x,y,z);roi_mask=region_mask(x,y,z,True)
    stats={};hashes={};supports={}
    for arm in ARMS:
        f=make_field(arm,base,ag,bg);error=f.astype(float)-base.astype(float);d=divergence(f)
        hashes[arm]=hashlib.sha256(struct.pack('<ii',3,0)+f.tobytes(order='C')).hexdigest()
        row={}
        for name,mask in [('simulation_free',global_mask),('analysis_roi',roi_mask)]:
            e=error[mask];b=base[mask].astype(float);a=f[mask].astype(float)
            an=np.linalg.norm(a,axis=1);bn=np.linalg.norm(b,axis=1)
            cs=np.clip(np.sum(a*b,axis=1)/(an*bn),-1,1)
            row[name]={'vector_rmse_m_s':float(np.sqrt(np.mean(np.sum(e**2,axis=1)))),'mean_cosine':float(cs.mean()),'speed_mae_m_s':float(np.mean(abs(an-bn))),'direction_mae_deg':float(np.degrees(np.arccos(cs)).mean())}
        row.update(max_vector_error_m_s=float(np.linalg.norm(error,axis=3).max()),min_u_m_s=float(f[...,0].min()),max_speed_m_s=float(np.linalg.norm(f,axis=3).max()),max_discrete_divergence_s_inv=float(abs(d).max()),rms_discrete_divergence_s_inv=float(np.sqrt(np.mean(d*d))))
        supports[arm]=int(np.any(error!=0,axis=3).sum());row['perturbed_voxel_count']=supports[arm];row['perturbed_volume_m3']=supports[arm]*H**3
        stats[arm]=row
        del f,error,d
    below=int(np.flatnonzero(z<Z0)[-1]);above=below+1
    base_shear=(float(base[above,0,0,0])-float(base[below,0,0,0]))/(z[above]-z[below])
    shear_ratios={}
    for arm in ['B_shear','B_speed']:
        f=make_field(arm,base,ag,bg)
        slope=(float(f[above,0,0,0])-float(f[below,0,0,0]))/(z[above]-z[below])
        shear_ratios[arm]=float(slope/base_shear)
    return {'a_streamfunction_gain_m2_s':ag,'b_speed_gain_m_s':bg,'expected_modern_wind_sha256':hashes,'statistics':stats,'task_height_base_shear_s_inv':float(base_shear),'task_height_shear_ratios':shear_ratios,'global_free_voxels':int(global_mask.sum()),'roi_voxels':int(roi_mask.sum()),'wind_files_written':0,'GADEN_runs':0,'OpenFOAM_runs':0,'PMFS_runs':0}

def route_points():
    # Function signature has no source location, plume, truth, or wind input.
    # ROI-only inset rectangle and centre altitude.
    xs=[float(ROI_LO[0]+4),float(ROI_HI[0]-4)]
    ys=np.arange(ROI_LO[1]+5,ROI_HI[1]-5+1e-9,1.)
    zs=float((ROI_LO[2]+ROI_HI[2])/2)
    vertices=[]
    for i,y in enumerate(ys):
        pair=xs if i%2==0 else xs[::-1]
        vertices.extend([[pair[0],float(y),zs],[pair[1],float(y),zs]])
    vertices=np.array(vertices);lengths=np.linalg.norm(np.diff(vertices,axis=0),axis=1)
    vmax,acc,dwell=1.2,1.,.4
    peaks=np.minimum(vmax,np.sqrt(acc*lengths))
    unscaled=lengths/peaks+peaks/acc
    stretch=(100-dwell*(len(lengths)-1))/unscaled.sum()
    assert stretch>=1
    schedule=[];cursor=20.
    for j,L in enumerate(lengths):
        duration=float(unscaled[j]*stretch)
        schedule.append({'segment':j,'start_s':float(cursor),'end_s':float(cursor+duration),'from_xyz_m':vertices[j].tolist(),'to_xyz_m':vertices[j+1].tolist(),'length_m':float(L),'ramp_s':float(peaks[j]/acc*stretch),'peak_speed_m_s':float(peaks[j]/stretch),'acceleration_m_s2':float(acc/stretch**2),'dwell_after_s':dwell if j<len(lengths)-1 else 0.})
        cursor+=duration+(dwell if j<len(lengths)-1 else 0.)
    assert abs(cursor-120)<1e-10
    out=[]
    for t in np.arange(20.,120.01,2.):
        p=vertices[-1].copy();v=np.zeros(3);a=np.zeros(3)
        for seg in schedule:
            if seg['start_s']<=t<seg['end_s']:
                local=t-seg['start_s'];duration=seg['end_s']-seg['start_s'];ramp=seg['ramp_s'];A=seg['acceleration_m_s2'];V=seg['peak_speed_m_s'];L=seg['length_m']
                if local<ramp: distance=.5*A*local**2;speed=A*local;ac=A
                elif local<=duration-ramp: distance=.5*A*ramp**2+V*(local-ramp);speed=V;ac=0.
                else: distance=L-.5*A*(duration-local)**2;speed=A*(duration-local);ac=-A
                p0=np.array(seg['from_xyz_m']);direction=(np.array(seg['to_xyz_m'])-p0)/L;p=p0+direction*distance;v=direction*speed;a=direction*ac;break
            if seg['end_s']<=t<seg['end_s']+seg['dwell_after_s']:
                p=np.array(seg['to_xyz_m']);break
        out.append({'time_s':float(t),'x_m':float(p[0]),'y_m':float(p[1]),'z_m':float(p[2]),'vx_m_s':float(v[0]),'vy_m_s':float(v[1]),'vz_m_s':float(v[2]),'ax_m_s2':float(a[0]),'ay_m_s2':float(a[1]),'az_m_s2':float(a[2])})
    return vertices.tolist(),out,float(lengths.sum()),schedule
