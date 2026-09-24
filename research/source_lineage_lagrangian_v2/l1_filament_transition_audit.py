#!/usr/bin/env python3
"""L1 source-lineage transition audit for House02.

No deep network. Tests whether a single source-agnostic 3-D lineage transition
can transfer to held-out S2-W2 better than a matched 2-D particle baseline.

Training: S1-W1 A/B, S2-W1 A/B, S1-W2 A/B.
Held out: S2-W2 A/B.

The learned part is only a multi-output ridge residual on top of a deterministic
3-D advection/obstacle rollout. Source ID/coordinates are never features.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

TRAIN=["S1_W1_A","S1_W1_B","S2_W1_A","S2_W1_B","S1_W2_A","S1_W2_B"]
HOLD=["S2_W2_A","S2_W2_B"]
ALPHAS=(0.0,1e-5,1e-4,1e-3,1e-2,1e-1,1.0,10.0)
RNG_SEED=20260924


def read_occ(path:Path):
    lines=path.read_text().splitlines()
    def vals(i,cast=float): return [cast(x) for x in lines[i].split()[1:]]
    mn=np.asarray(vals(0),np.float64); mx=np.asarray(vals(1),np.float64)
    dims=tuple(vals(2,int)); cell=float(vals(3)[0])
    nx,ny,nz=dims
    occ=np.ones((nz,nx,ny),dtype=np.int8)
    z=x=0
    for line in lines[4:]:
        if line.strip()==";":
            z+=1; x=0; continue
        if z>=nz: break
        a=np.fromstring(line,sep=" ",dtype=np.int8)
        if len(a):
            if len(a)!=ny: raise ValueError(f"occupancy row y-size {len(a)} != {ny}")
            occ[z,x,:]=a
            x+=1
    return {"min":mn,"max":mx,"dims":dims,"cell":cell,"occ":occ}


def idx_of(pos,env):
    # Match glm float->ivec conversion used by GADEN: truncate toward zero.
    q=np.trunc((pos-env["min"])/env["cell"]).astype(np.int64)
    return q  # x,y,z


def state_at(pos,env):
    q=idx_of(pos,env); nx,ny,nz=env["dims"]
    if q[0]<0 or q[0]>=nx or q[1]<0 or q[1]>=ny or q[2]<0 or q[2]>=nz:
        return 3
    return int(env["occ"][q[2],q[0],q[1]])


def step_towards(pos,end,env,depth=0):
    """Port of GADEN StepTowards. Returns position,state,contacts."""
    if depth>8: return pos.copy(),1,1
    si=idx_of(pos,env); ei=idx_of(end,env)
    if np.array_equal(si,ei):
        return end.copy(),state_at(end,env),0
    d=end-pos; dist=float(np.linalg.norm(d))
    if dist<=1e-12: return pos.copy(),state_at(pos,env),0
    direction=d/dist
    steps=max(1,int(math.ceil(dist/env["cell"])))
    inc=dist/steps
    p=pos.copy(); contacts=0
    for _ in range(steps):
        prev=p.copy(); p=p+direction*inc
        st=state_at(p,env)
        if st in (1,3):
            contacts+=1
            prev_cell=idx_of(prev,env).astype(np.float64)
            cur_cell=idx_of(p,env).astype(np.float64)
            normal=prev_cell-cur_cell
            p=prev
            rem=end-p
            nn=float(np.linalg.norm(normal))
            if nn<=1e-12: return p,st,contacts
            # Match gaden vmath::project: dot(a,b) * normalize(b)
            rejected=rem-float(np.dot(rem,normal))*(normal/nn)
            q,st2,c2=step_towards(p,p+rejected,env,depth+1)
            return q,st2,contacts+c2
        if st==2:
            return p,st,contacts
    return p,0,contacts


def wind_schedule(nsteps,dt=.1,wind_dt=1.0,loop_from=1,loop_to=10):
    current=np.float32(0); last=np.float32(0)
    d=np.float32(dt); wd=np.float32(wind_dt)
    idx=0; out=np.empty(nsteps,dtype=np.int16)
    for k in range(nsteps):
        out[k]=idx
        if current > np.float32(last+wd):
            idx+=1
            if idx>loop_to: idx=loop_from
            last=current
        current=np.float32(current+d)
    return out


def sample_wind(wseq,wind_idx,pos,env,z_override=None):
    p=pos.copy()
    if z_override is not None: p[2]=z_override
    q=idx_of(p,env); nx,ny,nz=env["dims"]
    if q[0]<0 or q[0]>=nx or q[1]<0 or q[1]>=ny or q[2]<0 or q[2]>=nz:
        return np.zeros(3,np.float64)
    return wseq[int(wind_idx),q[2],q[0],q[1]].astype(np.float64)


def rollout(pos,start_step,end_step,wseq,wsched,env,dt=.1,two_d=False,sensor_z=.2):
    p=pos.astype(np.float64).copy()
    if two_d: p[2]=sensor_z
    contacts=0; winds=[]; z0=float(p[2])
    for step in range(int(start_step)+1,int(end_step)+1):
        w=sample_wind(wseq,wsched[step],p,env,sensor_z if two_d else None)
        if two_d: w[2]=0
        winds.append(w.copy())
        end=p+w*dt
        if two_d: end[2]=sensor_z
        p,st,c=step_towards(p,end,env); contacts+=c
        if st==2:
            # Keep last position as an explicit wrong-exit prediction.
            break
    wa=np.asarray(winds) if winds else np.zeros((1,3))
    return p,{"contacts":contacts,"mean_wind":wa.mean(0),"std_wind":wa.std(0),
              "vertical_excursion":abs(float(p[2])-z0)}


def obstacle_fraction(pos,env,r):
    q=idx_of(pos,env); nx,ny,nz=env["dims"]
    x0=max(0,q[0]-r); x1=min(nx,q[0]+r+1)
    y0=max(0,q[1]-r); y1=min(ny,q[1]+r+1)
    z0=max(0,q[2]-r); z1=min(nz,q[2]+r+1)
    a=env["occ"][z0:z1,x0:x1,y0:y1]
    return float(np.mean(a!=0)) if a.size else 1.0


def local_grad(wseq,wi,pos,env):
    q=idx_of(pos,env); nx,ny,nz=env["dims"]; c=env["cell"]
    out=np.zeros((3,3),np.float64)
    for axis,n in enumerate((nx,ny,nz)):
        qm=q.copy(); qp=q.copy()
        qm[axis]=max(0,q[axis]-1); qp[axis]=min(n-1,q[axis]+1)
        def get(qq):
            return wseq[int(wi),qq[2],qq[0],qq[1]].astype(np.float64)
        den=max(1,qp[axis]-qm[axis])*c
        out[:,axis]=(get(qp)-get(qm))/den
    return out


def load_cell(root:Path,cell:str):
    z=np.load(root/cell/"filaments.npz",allow_pickle=False)
    l=np.load(root/cell/"lineage.npz",allow_pickle=False)
    return {k:z[k] for k in z.files}|{"lineage_id":l["lineage_id"],"age_steps":l["age_steps"]}


def collect_pairs(root,cell,max_pairs,rng):
    d=load_cell(root,cell)
    fil=d["filaments"]; off=d["offsets"]; ids=d["lineage_id"]
    steps=d["simulation_steps"]; times=d["times_s"]; ages=d["age_steps"]
    chunks=[]
    for k in range(len(steps)-1):
        s0,e0=int(off[k]),int(off[k+1]); s1,e1=int(off[k+1]),int(off[k+2])
        common,ia,ib=np.intersect1d(ids[s0:e0],ids[s1:e1],return_indices=True)
        if not len(common): continue
        a=s0+ia; b=s1+ib
        chunks.append({
          "start":fil[a,:3],"end":fil[b,:3],"sigma":fil[a,3],
          "age":ages[a],"start_step":np.full(len(a),steps[k],np.int32),
          "end_step":np.full(len(a),steps[k+1],np.int32),
          "transition":np.full(len(a),k,np.int32),
        })
    out={k:np.concatenate([x[k] for x in chunks],axis=0) for k in chunks[0]}
    n=len(out["sigma"])
    if n>max_pairs:
        pick=np.sort(rng.choice(n,size=max_pairs,replace=False))
        out={k:v[pick] for k,v in out.items()}
    return out


def build_xy(pairs,wseq,wsched,env,sensor_z):
    n=len(pairs["sigma"])
    X=[]; target=np.empty((n,3)); pred2=np.empty((n,3)); pred3=np.empty((n,3))
    trans=pairs["transition"].copy()
    for i in range(n):
        p0=pairs["start"][i].astype(np.float64); p1=pairs["end"][i].astype(np.float64)
        s=int(pairs["start_step"][i]); e=int(pairs["end_step"][i])
        q2,st2=rollout(p0,s,e,wseq,wsched,env,two_d=True,sensor_z=sensor_z)
        q3,st3=rollout(p0,s,e,wseq,wsched,env,two_d=False,sensor_z=sensor_z)
        wi=int(wsched[min(s+1,len(wsched)-1)])
        w0=sample_wind(wseq,wi,p0,env)
        grad=local_grad(wseq,wi,p0,env).reshape(-1)
        span=np.maximum(env["max"]-env["min"],env["cell"])
        posn=(p0-env["min"])/span
        dt=(e-s)*.1
        f=np.concatenate([
          posn,
          [pairs["sigma"][i]/70.0,pairs["age"][i]/3000.0,dt],
          w0,[np.linalg.norm(w0)],
          (q3-p0),st3["mean_wind"],st3["std_wind"],
          [st3["contacts"]/10.0,st3["vertical_excursion"],
           obstacle_fraction(p0,env,1),obstacle_fraction(p0,env,2)],
          grad/5.0,
        ])
        X.append(f); target[i]=p1-p0; pred2[i]=q2-p0; pred3[i]=q3-p0
    return np.asarray(X),target,pred2,pred3,trans


def standardize_fit(X):
    mu=X.mean(0); sd=X.std(0); sd[sd<1e-9]=1
    return mu,sd


def ridge_fit(X,Y,alpha):
    if alpha==0:
        return np.linalg.lstsq(X,Y,rcond=None)[0]
    A=X.T@X
    reg=np.eye(A.shape[0])*alpha
    reg[-1,-1]=0
    return np.linalg.solve(A+reg,X.T@Y)


def augment(X,mu,sd):
    z=(X-mu)/sd
    return np.column_stack((z,np.ones(len(z))))


def rmse(a,b,axes=(0,1,2)):
    d=(a-b)[:,list(axes)]
    return float(np.sqrt(np.mean(d*d)))


def flat_cos(a,b):
    aa=a.reshape(-1); bb=b.reshape(-1)
    den=np.linalg.norm(aa)*np.linalg.norm(bb)
    return float(np.dot(aa,bb)/den) if den>0 else float("nan")


def centroid_error(start,target,pred,transition):
    vals=[]
    for t in np.unique(transition):
        m=transition==t
        true_next=(start[m]+target[m]).mean(0)
        pred_next=(start[m]+pred[m]).mean(0)
        vals.append(np.linalg.norm((pred_next-true_next)[:2]))
    return float(np.mean(vals)) if vals else float("nan")


def combo(cell): return "_".join(cell.split("_")[:2])
def wind_id(cell): return cell.split("_")[1]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--lineage-root",type=Path,required=True)
    ap.add_argument("--wind-root",type=Path,required=True)
    ap.add_argument("--occupancy",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--max-pairs-per-cell",type=int,default=8000)
    ap.add_argument("--sensor-z",type=float,default=.2)
    args=ap.parse_args()

    env=read_occ(args.occupancy)
    w1=np.load(args.wind_root/"wind_W1_sequence_3d.npy",allow_pickle=False)
    w2=np.load(args.wind_root/"wind_W2_sequence_3d.npy",allow_pickle=False)
    ws=wind_schedule(4000)
    rng=np.random.default_rng(RNG_SEED)

    data={}
    for cell in TRAIN+HOLD:
        pairs=collect_pairs(args.lineage_root,cell,args.max_pairs_per_cell,rng)
        w=w1 if wind_id(cell)=="W1" else w2
        X,Y,P2,P3,T=build_xy(pairs,w,ws,env,args.sensor_z)
        data[cell]={"pairs":pairs,"X":X,"Y":Y,"P2":P2,"P3":P3,"T":T}

    Xtr=np.concatenate([data[c]["X"] for c in TRAIN])
    Ytr=np.concatenate([data[c]["Y"]-data[c]["P3"] for c in TRAIN])
    groups=np.concatenate([np.full(len(data[c]["X"]),combo(c),object) for c in TRAIN])
    mu,sd=standardize_fit(Xtr)

    cv={}
    for a in ALPHAS:
        errs=[]
        for g in sorted(set(groups)):
            m=groups!=g; v=~m
            mu_g,sd_g=standardize_fit(Xtr[m])
            Bcv=ridge_fit(augment(Xtr[m],mu_g,sd_g),Ytr[m],a)
            pred=augment(Xtr[v],mu_g,sd_g)@Bcv
            errs.append(float(np.sqrt(np.mean((pred-Ytr[v])**2))))
        cv[str(a)]=float(np.mean(errs))
    alpha=min(ALPHAS,key=lambda a:cv[str(a)])
    B=ridge_fit(augment(Xtr,mu,sd),Ytr,alpha)

    # lineage-destruction null: same inputs, residual successors permuted.
    perm=rng.permutation(len(Ytr))
    Bnull=ridge_fit(augment(Xtr,mu,sd),Ytr[perm],alpha)

    result={"mode":"SLL_V2_FILAMENT_L1","train_cells":TRAIN,"holdout_cells":HOLD,
            "pairs_per_cell":{c:int(len(data[c]["X"])) for c in data},
            "ridge_alpha":alpha,"cv":cv,"holdout":{}}
    passes=[]
    for cell in HOLD:
        d=data[cell]; residual=augment(d["X"],mu,sd)@B
        residual_null=augment(d["X"],mu,sd)@Bnull
        pred=d["P3"]+residual
        pnull=d["P3"]+residual_null
        y=d["Y"]; start=d["pairs"]["start"]; tr=d["T"]
        r2=rmse(d["P2"],y,(0,1)); r3=rmse(d["P3"],y,(0,1)); rr=rmse(pred,y,(0,1))
        rn=rmse(pnull,y,(0,1))
        c2=centroid_error(start,y,d["P2"],tr)
        c3=centroid_error(start,y,d["P3"],tr)
        cr=centroid_error(start,y,pred,tr)
        cn=centroid_error(start,y,pnull,tr)
        state_improve=(c2-c3)/c2 if c2>0 else float("nan")
        operator_improve=(c3-cr)/c3 if c3>0 else float("nan")
        operator_rmse_improve=(r3-rr)/r3 if r3>0 else float("nan")
        cos2=flat_cos(d["P2"][:,:2],y[:,:2])
        cos3=flat_cos(d["P3"][:,:2],y[:,:2])
        cos=flat_cos(pred[:,:2],y[:,:2])
        null_gap=(cn-cr)/cn if cn>0 else float("nan")
        state_gate={
          "3d_centroid_improvement_vs_2d_ge_25pct":state_improve>=.25,
          "3d_transport_direction_cosine_gt_0p5":cos3>.5,
        }
        operator_gate={
          "operator_centroid_improvement_vs_3d_ge_10pct":operator_improve>=.10,
          "operator_rmse_improvement_vs_3d_ge_10pct":operator_rmse_improve>=.10,
          "operator_transport_direction_cosine_gt_0p5":cos>.5,
          "lineage_null_worse_by_ge_10pct":null_gap>=.10,
        }
        passes.append((all(state_gate.values()),all(operator_gate.values())))
        result["holdout"][cell]={
          "xy_rmse_m":{"2d":r2,"3d_physics":r3,"lineage_residual":rr,"destroyed_lineage_null":rn},
          "mean_next_centroid_error_m":{"2d":c2,"3d_physics":c3,"lineage_residual":cr,"destroyed_lineage_null":cn},
          "centroid_improvement":{"3d_vs_2d":state_improve,"operator_vs_3d":operator_improve},
          "operator_rmse_improvement_vs_3d":operator_rmse_improve,
          "lineage_null_relative_gap":null_gap,
          "transport_direction_cosine":{"2d":cos2,"3d_physics":cos3,"lineage_residual":cos},
          "state_gates":state_gate,
          "operator_gates":operator_gate,
        }

    state_pass=all(x[0] for x in passes)
    operator_pass=all(x[1] for x in passes)
    if state_pass and operator_pass:
        decision="L1_OPERATOR_PASS_FREEZE_BEFORE_L2"
    elif state_pass:
        decision="L1_STATE_PASS_OPERATOR_NO_GO"
    else:
        decision="L1_FAIL_STOP_SOURCE_LINEAGE_MAINLINE"
    result["summary"]={"state_pass":state_pass,"operator_pass":operator_pass}
    result["decision"]=decision
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=True)+"\n")
    np.savez_compressed(args.out.with_suffix(".model.npz"),coef=B,mean=mu,std=sd,alpha=np.asarray(alpha))
    print(json.dumps(result,indent=2,allow_nan=True))

if __name__=="__main__":
    main()
