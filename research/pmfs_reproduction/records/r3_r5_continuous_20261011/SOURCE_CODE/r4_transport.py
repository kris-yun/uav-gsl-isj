"""Auditable conservative periodic FV; batched last two dimensions are y,x."""
import numpy as np
def step(c, wind, D=.05, dt=.2, dx=.5):
    w=np.asarray(wind); u=w[...,0]; v=w[...,1]
    px=np.maximum(u,0)*dt/dx; nx=np.maximum(-u,0)*dt/dx
    py=np.maximum(v,0)*dt/dx; ny=np.maximum(-v,0)*dt/dx; l=D*dt/dx**2
    cfl=px+nx+py+ny+4*l
    if np.max(cfl)>1+1e-14:raise ValueError('CFL > 1')
    def a(x):return np.asarray(x)[...,None,None]
    return c*a(1-cfl)+(a(px)+l)*np.roll(c,1,axis=-1)+(a(nx)+l)*np.roll(c,-1,axis=-1)+(a(py)+l)*np.roll(c,1,axis=-2)+(a(ny)+l)*np.roll(c,-1,axis=-2)
def qualification():
    from importlib.util import spec_from_file_location,module_from_spec
    import pathlib,time
    b=pathlib.Path(__file__).resolve().parents[1]; s=spec_from_file_location('provided',b/'outputs/PMFS_R3_R5_CONTINUOUS_20261011/authorization/transport_reference.py'); m=module_from_spec(s);s.loader.exec_module(m)
    supplied=m.smoke_tests()
    rng=np.random.default_rng(919191); c=rng.random((24,24)); w=np.array([.6,-.3])
    scalar=m.finite_volume_step(c,w,.05,.2,.5,.5); batch=step(c,w)
    residual=float(abs(batch.sum()-c.sum())*.25)
    assert np.max(abs(batch-scalar))<1e-13 and residual<1e-12 and batch.min()>=0
    # Independently construct conservative nearest-neighbor transition matrix.
    n=24; A=np.zeros((n*n,n*n));u,v=w;l=.05*.2/.25;px=max(u,0)*.4;nx=max(-u,0)*.4;py=max(v,0)*.4;ny=max(-v,0)*.4
    for y in range(n):
        for x in range(n):
            j=y*n+x;A[j,j]=1-(abs(u)+abs(v))*.4-4*l
            for yy,xx,value in [(y,(x-1)%n,px+l),(y,(x+1)%n,nx+l),((y-1)%n,x,py+l),((y+1)%n,x,ny+l)]:A[j,yy*n+xx]+=value
    matrix=float(np.max(abs(A@c.ravel()-batch.ravel())));assert matrix<1e-13 and np.max(abs(A.sum(axis=0)-1))<1e-14
    fields=np.broadcast_to(c,(25,24,24,24)).copy();winds=np.broadcast_to(w,(25,24,2));t=time.perf_counter()
    for _ in range(100):fields=step(fields,winds)
    profile=time.perf_counter()-t
    return {'provided_smoke':supplied,'independent_transition_matrix_maxdiff':matrix,'constant_wind_mass_residual_mg':residual,'nonnegative':True,'maximum_registered_CFL':.96,'profile_100_steps_600_fields_s':profile,'estimated_4_methods_36_tasks_s':profile*5*4*36,'scope':'matched solver math; NOT steady solution qualification','state_RSS_estimate_bytes':fields.nbytes*10}
