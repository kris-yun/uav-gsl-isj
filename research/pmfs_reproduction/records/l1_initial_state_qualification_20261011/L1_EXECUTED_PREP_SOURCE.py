"""Geometry-only mass-consistent prior, past-wind conditional proposals. No gas."""
from pathlib import Path
import json,hashlib,time,csv,math
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import cg
from scipy.sparse.csgraph import connected_components
from scipy.special import logsumexp,log_ndtr

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'outputs/PMFS_L1_INITIAL_STATE_QUALIFICATION_20261011'
SHARE=Path('D:/ZYC/A-gas/workspace/PMFS_L1_INITIAL_STATE_QUALIFICATION_20261011')
def dump(n,o):(OUT/n).write_text(json.dumps(o,indent=2)+'\n',encoding='utf8')
def normal_logpdf(x,mean,sd):return -.5*((x-mean)/sd)**2-np.log(sd)-.5*np.log(2*np.pi)

def main():
    start=time.monotonic();contract=json.loads((OUT/'L1_PROSPECTIVE_MODEL_CONTRACT_REV1.json').read_text())
    p=SHARE/'OccupancyGrid3D.csv';lines=p.read_text().splitlines()
    lo=np.array(list(map(float,lines[0].split()[1:])));hi=np.array(list(map(float,lines[1].split()[1:])))
    nx,ny,nz=map(int,lines[2].split()[1:]);h=float(lines[3].split()[1])
    flat=[]
    for line in lines[4:]:
        if line!=';':flat.extend(map(int,line.split()))
    states=np.asarray(flat,np.uint8).reshape(nz,nx,ny).transpose(0,2,1).copy().ravel()
    assert states.size==nx*ny*nz and set(np.unique(states)).issubset({0,1,2})
    (SHARE/'geometry_states.u8').write_bytes(states.tobytes())
    free_cells=np.flatnonzero(states==0);N=len(free_cells);node=np.full(states.size,-1,np.int32);node[free_cells]=np.arange(N)
    x=free_cells%nx;y=(free_cells//nx)%ny;z=free_cells//(nx*ny);coords=np.column_stack([x,y,z]);world=lo+h*(coords+.5)
    mask=np.array(list(map(int,(SHARE/'native_mask.txt').read_text().split())));ids=np.flatnonzero(mask)
    sources=[];bad=[]
    for idx in ids:
        i,j=divmod(int(idx),45);xy=np.array([-7.55+(i+.5)*.25,-7.88+(j+.5)*.25]);ix,iy=np.floor((xy-lo[:2])/h).astype(int)
        heights=[float(lo[2]+(k+.5)*h) for k in range(nz) if 0<=ix<nx and 0<=iy<ny and states[k*nx*ny+iy*nx+ix]==0]
        if not heights:bad.append(int(idx))
        sources.append({'flat_id':int(idx),'xy':xy.tolist(),'legal_heights':heights})
    geo={'dims':[nx,ny,nz],'min':lo.tolist(),'max':hi.tolist(),'h':h,'Nfree':N,'native447':len(ids),'bad_no_free_height_ids':bad,'geometrySHA':hashlib.sha256(p.read_bytes()).hexdigest(),'statesSHA':hashlib.sha256(states.tobytes()).hexdigest(),'source_height_is_marginal_nuisance':True}
    dump('L1_GEOMETRY_SUPPORT_AUDIT.json',geo)
    (SHARE/'L1_GEOMETRY_META.json').write_text(json.dumps(geo,indent=2)+'\n')
    if bad:raise RuntimeError('ALL447_SUPPORT_STOP:'+str(bad))
    source_by_id={s['flat_id']:s for s in sources}
    # Directed internal edges plus true geometric outlet and open OOB faces.
    a=[];b=[];axis=[];sign=[];startside=[];endside=[];steps=[1,nx,nx*ny]
    for d in range(3):
        inside=coords[:,d]<np.array([nx,ny,nz])[d]-1
        ncell=free_cells[inside]+steps[d];origin=np.flatnonzero(inside)
        kinds=states[ncell];ff=kinds==0
        a.extend(origin[ff]);b.extend(node[ncell[ff]]);axis.extend([d]*sum(ff));sign.extend([1]*sum(ff));startside.extend([2*d+1]*sum(ff));endside.extend([2*d]*sum(ff))
        out=kinds==2
        a.extend(origin[out]);b.extend([-1]*sum(out));axis.extend([d]*sum(out));sign.extend([1]*sum(out));startside.extend([2*d+1]*sum(out));endside.extend([-1]*sum(out))
        boundary=np.flatnonzero(~inside)
        a.extend(boundary);b.extend([-1]*len(boundary));axis.extend([d]*len(boundary));sign.extend([1]*len(boundary));startside.extend([2*d+1]*len(boundary));endside.extend([-1]*len(boundary))
        # negative-direction outlet or OOB; internal ff already represented above.
        low=coords[:,d]==0;neg=np.flatnonzero(~low);ns=states[free_cells[neg]-steps[d]]
        negative=np.concatenate([np.flatnonzero(low),neg[ns==2]])
        a.extend(negative);b.extend([-1]*len(negative));axis.extend([d]*len(negative));sign.extend([-1]*len(negative));startside.extend([2*d]*len(negative));endside.extend([-1]*len(negative))
    a=np.asarray(a,np.int32);b=np.asarray(b,np.int32);axis=np.asarray(axis,np.int32);sign=np.asarray(sign,np.int32);ss=np.asarray(startside,np.int32);es=np.asarray(endside,np.int32);E=len(a)
    interior=b>=0;edge=np.arange(E);D=sparse.csr_matrix((np.concatenate([np.ones(E),-np.ones(sum(interior))]),(np.concatenate([a,b[interior]]),np.concatenate([edge,edge[interior]]))),shape=(N,E))
    L=(D@D.T).tocsr();adj=sparse.csr_matrix((np.ones(2*sum(interior)),(np.concatenate([a[interior],b[interior]]),np.concatenate([b[interior],a[interior]]))),shape=(N,N))
    nc,labels=connected_components(adj,directed=False);open_components=set(labels[a[~interior]])
    closed=[int(np.flatnonzero(labels==c)[0]) for c in range(nc) if c not in open_components]
    if closed:L=L+sparse.csr_matrix((np.ones(len(closed)),(closed,closed)),shape=(N,N))
    Mpre=sparse.diags(1/L.diagonal());basis=[];residuals=[];rng=np.random.default_rng(contract['RNG']['basis_seed'])
    waves=[(1,1,1),(2,1,1),(1,2,1),(1,1,2),(2,2,1),(2,1,2),(1,2,2)]
    edgepos=world[a].copy();edgepos[np.arange(E),axis]+=sign*h*.5
    patterns=[None]+waves
    for mode in range(24):
        group,d=divmod(mode,3);raw=np.zeros(E)
        match=axis==d
        if group==0:raw[match]=sign[match]
        else:
            phase=rng.uniform(0,2*np.pi);wave=np.array(patterns[group]);s=((edgepos-lo)/(hi-lo))@wave
            raw[match]=np.cos(2*np.pi*s[match]+phase)*sign[match]
        rhs=D@raw;sol,info=cg(L,rhs,M=Mpre,rtol=1e-10,atol=1e-11,maxiter=4000)
        if info!=0:raise RuntimeError('CG_PROJECTION_NOT_CONVERGED_'+str(info))
        velocity=raw-D.T@sol
        faces=np.zeros((N,6));faces[a,ss]=sign*velocity
        faces[b[interior],es[interior]]=velocity[interior]
        center=.5*(faces[:,1::2]+faces[:,::2]);rms=np.sqrt(np.mean(np.sum(center**2,axis=1)))
        if rms<1e-8:raise RuntimeError('PRIOR_MODE_DEGENERATE_'+str(mode))
        faces/=rms;div=np.sum(faces[:,1::2]-faces[:,::2],axis=1)/h
        maxdiv=float(np.max(np.abs(div)));residuals.append(maxdiv)
        if maxdiv>1e-5:raise RuntimeError('FLOW_DIVERGENCE_FAIL')
        basis.append(faces.astype('<f4'))
        print('basis',mode,'divergence',maxdiv,flush=True)
    B=np.array(basis);B.tofile(SHARE/'flow_faces.f32');node.astype('<i4').tofile(SHARE/'free_node_index.i32')
    # Piecewise-linear normal face interpolation preserves voxel divergence.
    receptor=np.array([-.9,.15,-.2]);rc=np.floor((receptor-lo)/h).astype(int);cell=rc[0]+nx*rc[1]+nx*ny*rc[2];rn=int(node[cell]);assert rn>=0
    frac=(receptor-(lo+rc*h))/h
    H=np.stack([(1-frac[d])*B[:,rn,2*d]+frac[d]*B[:,rn,2*d+1] for d in [0,1]])
    obs=[]
    with (SHARE/'C1B_PAST_LOCAL_WIND.csv').open(newline='',encoding='utf8') as f:
        for r in csv.DictReader(f):
            if r['physical_epoch_bound']=='True' and r['TF_at_initialization_cutoff']=='PASS_PAST_STAMP':
                ts=float(r['physical_stamp_s']);s=float(r['speed_m_s']);phi=float(r['cutoff_TO_rad_map']);obs.append((ts,s,phi))
    assert len(obs)==184
    end=contract['time']['profile_end_target_s'];T=np.unique(np.r_[np.arange(0,end+.2,.1),[t[0] for t in obs]])
    omap={int(np.searchsorted(T,t)): (speed,phi) for t,speed,phi in obs}
    ref_meta=[];refs=[]
    for ref,seed in enumerate(contract['RNG']['wind_reference_seeds']):
        rg=np.random.default_rng(seed);amp=abs(rg.normal());tau=np.exp(rg.uniform(0,np.log(267.307098389)));v=amp*amp/24
        means=[];covs=[];pred_means=[];pred_covs=[];m=np.zeros(24);P=np.eye(24)*v;logZ=0.;R_by_obs={};a_theta=np.exp(-.3**2/2);HH=a_theta*H
        for ti,(speed,phi) in omap.items():
            # Data-adapted Gaussian proposal ONLY. Exact target corrected below.
            c2=(1+np.exp(-2*.3**2))/2;s2=1-c2
            parallel=(speed**2+.03**2)*c2-speed**2*a_theta**2
            perpendicular=(speed**2+.03**2)*s2
            rot=np.array([[np.cos(phi),-np.sin(phi)],[np.sin(phi),np.cos(phi)]])
            R_by_obs[ti]=rot@np.diag([max(parallel,1e-10),max(perpendicular,1e-10)])@rot.T
        for ti,t in enumerate(T):
            rho=np.exp(-(t-T[ti-1])/tau) if ti else 1.
            if ti:m=rho*m;P=rho*rho*P+(1-rho*rho)*np.eye(24)*v
            pred_means.append(m.copy());pred_covs.append(P.copy())
            if ti in omap:
                speed,phi=omap[ti];yobs=speed*np.array([np.cos(phi),np.sin(phi)])
                R=R_by_obs[ti];S=HH@P@HH.T+R;delta=yobs-HH@m;K=np.linalg.solve(S,HH@P).T
                logZ+=-.5*(delta@np.linalg.solve(S,delta)+np.linalg.slogdet(S)[1]+2*np.log(2*np.pi))
                m=m+K@delta;P=P-K@HH@P;P=(P+P.T)/2
            means.append(m.copy());covs.append(P.copy())
        C=np.empty((len(T),24));C[-1]=rg.multivariate_normal(means[-1],covs[-1])
        for ti in range(len(T)-2,-1,-1):
            rho=np.exp(-(T[ti+1]-T[ti])/tau);J=np.linalg.solve(pred_covs[ti+1],rho*covs[ti]).T
            mu=means[ti]+J@(C[ti+1]-pred_means[ti+1]);V=covs[ti]-J@pred_covs[ti+1]@J.T;V=(V+V.T)/2
            ev,Q=np.linalg.eigh(V);V=Q@np.diag(np.maximum(ev,0))@Q.T
            C[ti]=rg.multivariate_normal(mu,V)
        log_exact=0.;log_aux=0.
        for ti,(speed,phi) in omap.items():
            w=H@C[ti];r=np.linalg.norm(w);theta=np.arctan2(w[1],w[0]);delta=np.arctan2(np.sin(phi-theta),np.cos(phi-theta))
            logtheta=logsumexp(normal_logpdf(delta+np.arange(-2,3)*2*np.pi,0,.3))
            log_exact+=logtheta+(normal_logpdf(speed,r,.03) if speed>0 else log_ndtr(-r/.03))
            yc=speed*np.array([np.cos(phi),np.sin(phi)]);dd=yc-a_theta*w;R=R_by_obs[ti]
            log_aux+=-.5*(dd@np.linalg.solve(R,dd)+np.linalg.slogdet(R)[1]+2*np.log(2*np.pi))
        logweight=logZ+log_exact-log_aux
        C.astype('<f8').tofile(SHARE/f'wind_coeff_ref{ref}.f64');T.astype('<f8').tofile(SHARE/'wind_times.f64')
        row={'ref':ref,'seed':seed,'tau_s':tau,'amplitude_m_s':amp,'log_exact_wind_likelihood':float(log_exact),'log_aux_potential':float(log_aux),'log_aux_path_normalizer':float(logZ),'not_physical_evidence':True,'log_importance_weight':float(logweight),'height_and_transport_separate_RNG':True};ref_meta.append(row);refs.append(C)
    lw=np.array([r['log_importance_weight'] for r in ref_meta]);weight=np.exp(lw-logsumexp(lw));ess=1/np.sum(weight**2)
    pilots=[]
    for si,s in enumerate(contract['support']['pilot_native_flat_ids']):
        src=source_by_id[s]
        for r in range(2):
            rngh=np.random.default_rng(contract['RNG']['height_seeds'][si][r]);heights=src['legal_heights'];height=heights[int(rngh.integers(len(heights)))]
            pilots.append({'native_id':s,'ref':r,'source_xyz':[src['xy'][0],src['xy'][1],height],'transport_seed':contract['RNG']['transport_seeds'][si][r]})
    config={'geometry':geo,'basis_count':24,'time_count':len(T),'target_s':end,'gas':contract['gas_operator']['physical_fields'],'pilots':pilots,'sensor_xyz':receptor.tolist(),'wind_refs':ref_meta,'ESS_K2':float(ess),'wind_weights':weight.tolist(),'projection_maxdiv':max(residuals),'face_interpolation':'normalcomponent linear interpolation inside voxel; mixedderivatives absent so discreteface divergence equalscontinuousvoxel divergence','no_actual_source_label':True,'no_actual_test_gas':True,'no_true_CFD':True,'past_wind_conditioning_only':True}
    (SHARE/'L1_EXECUTION_CONFIG.json').write_text(json.dumps(config,indent=2)+'\n')
    dump('L1_WIND_AND_GEOMETRY_QUALIFICATION.json',config)
    dump('L1_PREPARATION_RECEIPT.json',{'active_wall_s':time.monotonic()-start,'field_bytes':B.nbytes,'prior_coeff_path_bytes':sum(C.nbytes for C in refs),'new_gas_forward_calls':0,'proper_importance_correction':True,'wind_ESS_gate_pass':ess/2>=.8,'finiteK2_scientific_qualification':False,'geometry_support_pass':True,'field_projection_pass':max(residuals)<1e-5})
    print('DONE',json.dumps({'active_s':time.monotonic()-start,'Nfree':N,'dims':[nx,ny,nz],'field_bytes':B.nbytes,'ESS':ess,'sixpilots':len(pilots)}),flush=True)

if __name__=='__main__':main()
