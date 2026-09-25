#!/usr/bin/env python3
"""Frozen zero-plume RPO-G0 physical-context prediction gate."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import balanced_accuracy_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
UP = ROOT / "evidence/source_probe_crossed_audit_v0"
RIA = ROOT / "evidence/relational_identifiability_a0"
E1 = ROOT / "evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv"
PANEL = ROOT / "evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv"
ASSET = Path(r"D:\ZYC\A-gas\_staging\SPX_G0_ASSETS_20260925")
RAW = Path(r"D:\ZYC\A-gas\_staging\RPO_G0_HOUSE02_W0_RAW_20260926")
WIND = RAW / "gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"
OUT = ROOT / "evidence/relational_physical_observability_v0"
CODE = Path(__file__).resolve()
PROTOCOLS = ("P_G1A", "P_E2")
FAMILIES = ("SOURCE_ONLY", "GEOM", "SIMPLE_WIND", "PHYS")
TARGETS = ("CNR", "ED")
ALPHAS = (1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100, 1000)
SEED = 2026092601


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def readcsv(path, delimiter=","):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def writecsv(path, rows):
    if not rows:
        raise ValueError("empty CSV")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def jwrite(path, value):
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def upstream_files():
    files = {"occupancy": RAW / "OccupancyGrid3D.csv",
             "central_panel": PANEL, "offstrip_panel": E1,
             "probe_g1a": ASSET / "gate1a_contract.json",
             "probe_e2": ASSET / "e1_probe_contracts.tsv",
             "pairs": UP / "SPX_G0_FROZEN_PAIRS.csv",
             "ria_reference": RIA / "RIA_A0_REFERENCE_IDENTIFIABILITY.csv",
             "ria_result": RIA / "RIA_A0_RESULT.json"}
    files.update({f"wind_{i}": WIND / f"wind_iteration_{i}" for i in range(11)})
    return files


def audit():
    spx = json.loads((UP / "SPX_G0_ASSET_AUDIT.json").read_text())
    if spx["asset_usability"] != "ASSET_READY_FOR_CROSSED_EXTRACTION":
        raise ValueError("SPX assets were not complete")
    req = spx["required_assets"]
    expected = {"occupancy": req["occupancy"]["sha256"],
                "central_panel": req["central_panel.tsv"]["sha256"],
                "offstrip_panel": req["e1_source_panels.tsv"]["sha256"],
                "probe_g1a": req["gate1a_contract.json"]["sha256"],
                "probe_e2": req["e1_probe_contracts.tsv"]["sha256"],
                **{f"wind_{i}": req["wind_sequence"][i]["sha256"] for i in range(11)}}
    pairsha = json.loads((UP / "SPX_G0_PRE_SCORE_LOCK.json").read_text())["pairs_sha256"]
    expected["pairs"] = pairsha
    assert json.loads((RIA / "RIA_A0_RESULT.json").read_text())["decision"] == "RIA_A0_PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED"
    report = {"decision": "RPO_G0_ASSETS_VERIFIED", "house": "House02", "wind": "3,5-1_slow",
              "files": {}, "zero_new_plume": True, "sealed_data_read": False}
    for name, file in upstream_files().items():
        if not file.is_file():
            raise FileNotFoundError(file)
        actual = sha(file)
        if name in expected and actual != expected[name]:
            raise ValueError(f"SHA mismatch: {name}")
        report["files"][name] = {"path": str(file), "bytes": file.stat().st_size, "sha256": actual}
    if len(readcsv(PANEL,"\t")) != 168 or len([r for r in readcsv(E1,"\t") if r["house"] == "House02"]) != 6:
        raise ValueError("source panel count mismatch")
    pairs = readcsv(UP / "SPX_G0_FROZEN_PAIRS.csv")
    if len([r for r in pairs if r["panel"] == "CENTRAL"]) != 84 or len([r for r in pairs if r["panel"] == "OFFSTRIP"]) != 3:
        raise ValueError("pair count mismatch")
    if len(readcsv(RIA / "RIA_A0_REFERENCE_IDENTIFIABILITY.csv")) != 168:
        raise ValueError("RIA target count mismatch")
    return report


def lock_stage():
    OUT.mkdir(parents=True, exist_ok=True)
    report = audit()
    lock = {"branch": "research/relational-physical-observability-g0-20260926",
            "code_sha256": sha(CODE),
            "charter_sha256": sha(ROOT / "research/relational_physical_observability_v0/RPO_G0_CHARTER_20260926.md"),
            "asset_check_sha256": None,
            "occupancy": "z=floor((0.20-env_min_z)/cell); voxel value 0 is free; 8-neighbor grid, diagonal allowed only if both orthogonal side voxels free; metric edge length; scipy Dijkstra; grid-center path length; disconnected geodesic sentinel 2*map diagonal, wind-path descriptors zero, travel sentinel geodesic/0.05, explicit disconnected flag",
            "position_to_voxel": "floor((world_coordinate-env_min)/cell), clipped only for interpolation, never for occupancy validation",
            "los": "line segment at <=0.05m spacing including both endpoints; all visited z=0.20 voxels free",
            "wind": "11 source files little-endian float64 (3,26,83,119); x/y components downwind map-frame; bilinear at z slice on voxel-center coordinates, edge midpoints; border-clipped interpolation; path statistics weighted by edge metric length; zero wind direction cosine=0",
            "travel_floor_mps": .05,
            "geometric_path": "source/probe grid-cell center to grid-cell center; same-cell path uses exact source-probe direct segment",
            "pair_aggregation": "for each scalar h: mean abs difference, RMS difference, max abs difference, median abs difference, cosine similarity (zero-norm=0); protocol input is E2 minus G1A aggregation; SOURCE_ONLY is static pair geometry",
            "simple_wind": "source-local wind unit direction dotted with direct source-probe unit vector, local speed, Euclidean distance; mean and RMS signed source-pair differences across 30 probes x 11 winds; E2 minus G1A",
            "x_bands": "CENTRAL pair min(pmfs_i) 1..6,7..12,13..18,19..24; 21 pairs each",
            "ridge": "StandardScaler on training bands only; Ridge with intercept; alpha grid fixed; inner leave-one-training-band-out pooled MSE; ties smallest alpha; no Y scaling",
            "alpha_grid": ALPHAS, "bootstrap_seed": SEED, "bootstrap_draws": 10000,
            "sign_ties": "exclude |Y|<1e-10; predicted sign is >0, exact prediction zero is negative",
            "offstrip": "descriptive only after CENTRAL result file committed"}
    jwrite(OUT / "RPO_G0_ASSET_CHECK.json", report)
    lock["asset_check_sha256"] = sha(OUT / "RPO_G0_ASSET_CHECK.json")
    jwrite(OUT / "RPO_G0_PRE_RUN_LOCK.json", lock)
    print("RPO_A0_ASSET_LOCK", lock["asset_check_sha256"])


class World:
    def __init__(self):
        self.header, full = self._read_occupancy(RAW / "OccupancyGrid3D.csv")
        self.cell = self.header["cell_size(m)"][0]
        self.origin = np.array(self.header["env_min(m)"][:2], dtype=float)
        self.zindex = math.floor((.2-self.header["env_min(m)"][2])/self.cell)
        self.free = full[self.zindex] == 0
        if self.zindex != 12 or self.free.shape != (83,119):
            raise ValueError("occupancy geometry drift")
        self.nx,self.ny = self.free.shape
        self.diagonal = float(np.linalg.norm(np.array([self.nx,self.ny])*self.cell))
        self.wind = np.stack([np.fromfile(WIND/f"wind_iteration_{i}",dtype="<f8").reshape(3,26,83,119)[:2,self.zindex]
                              for i in range(11)])
        if not np.isfinite(self.wind).all():
            raise ValueError("nonfinite wind")
        self.graph = self._graph()
        self.cache = {}

    @staticmethod
    def _read_occupancy(path):
        header={};payload=[]
        with open(path,encoding="utf-8") as f:
            for line in f:
                if line.startswith("#"):
                    key,*numbers=line[1:].split()
                    header[key]=[float(v) for v in numbers]
                elif line.strip()!=";":
                    payload.extend(int(v) for v in line.split())
        nx,ny,nz=map(int,header["num_cells"])
        values=np.asarray(payload,dtype=np.int8)
        if values.size!=nx*ny*nz:
            raise ValueError("occupancy payload size mismatch")
        return header,values.reshape(nz,nx,ny)

    def cell_index(self, xy):
        v = np.floor((np.asarray(xy)-self.origin)/self.cell).astype(int)
        if not (0 <= v[0] < self.nx and 0 <= v[1] < self.ny and self.free[tuple(v)]):
            raise ValueError(f"source/probe not a free voxel: {xy}, {v}")
        return tuple(v)

    def _graph(self):
        ii,jj,weights=[],[],[]
        neighbors=((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
        for x,y in np.argwhere(self.free):
            u=int(x)*self.ny+int(y)
            for dx,dy in neighbors:
                xx,yy=int(x)+dx,int(y)+dy
                if not (0<=xx<self.nx and 0<=yy<self.ny and self.free[xx,yy]):
                    continue
                if dx and dy and not (self.free[int(x)+dx,int(y)] and self.free[int(x),int(y)+dy]):
                    continue
                ii.append(u); jj.append(xx*self.ny+yy); weights.append(self.cell*math.hypot(dx,dy))
        return coo_matrix((weights,(ii,jj)),shape=(self.nx*self.ny,)*2).tocsr()

    def xy_center(self, index):
        return self.origin+(np.asarray(index,dtype=float)+.5)*self.cell

    def interp(self, points):
        q=(np.asarray(points)-self.origin)/self.cell-.5
        q[:,0]=np.clip(q[:,0],0,self.nx-1)
        q[:,1]=np.clip(q[:,1],0,self.ny-1)
        i=np.floor(q[:,0]).astype(int); j=np.floor(q[:,1]).astype(int)
        i1=np.minimum(i+1,self.nx-1);j1=np.minimum(j+1,self.ny-1)
        fx=(q[:,0]-i)[None,None,:];fy=(q[:,1]-j)[None,None,:]
        w=self.wind
        return ((1-fx)*(1-fy)*w[:,:,i,j]+fx*(1-fy)*w[:,:,i1,j]+(1-fx)*fy*w[:,:,i,j1]+fx*fy*w[:,:,i1,j1]).transpose(0,2,1)

    def los(self,a,b):
        count=max(1,int(math.ceil(np.linalg.norm(b-a)/.05)))
        for point in a[None,:]+np.linspace(0,1,count+1)[:,None]*(b-a)[None,:]:
            idx=np.floor((point-self.origin)/self.cell).astype(int)
            if not (0<=idx[0]<self.nx and 0<=idx[1]<self.ny and self.free[tuple(idx)]):
                return 0.0
        return 1.0

    def paths_from_sources(self,sources,probes):
        source_nodes=[self.cell_index(s)[0]*self.ny+self.cell_index(s)[1] for s in sources]
        unique_nodes=sorted(set(source_nodes))
        lengths, predecessors=dijkstra(self.graph,directed=True,indices=unique_nodes,return_predecessors=True)
        node_to_row={node:k for k,node in enumerate(unique_nodes)}
        for si,s in enumerate(sources):
            row=node_to_row[source_nodes[si]]
            for pi,p in enumerate(probes):
                endpoint=self.cell_index(p)
                target=endpoint[0]*self.ny+endpoint[1]
                dist=float(lengths[row,target])
                if not math.isfinite(dist):
                    self.cache[si,pi]=(None,2*self.diagonal,1)
                    continue
                chain=[target]
                while chain[-1]!=source_nodes[si]:
                    prev=int(predecessors[row,chain[-1]])
                    if prev<0 or len(chain)>self.nx*self.ny:
                        raise ValueError("invalid shortest path predecessor")
                    chain.append(prev)
                chain.reverse()
                points=np.array([self.xy_center((node//self.ny,node%self.ny)) for node in chain])
                if len(points)==1:
                    points=np.array([s,p],dtype=float)
                self.cache[si,pi]=(points,dist,0)

    def path_desc(self,source,probe,si,pi):
        s,p=np.asarray(source),np.asarray(probe)
        direct=float(np.linalg.norm(p-s))
        points,geod,disc=self.cache[si,pi]
        base={"euclidean":direct,"geodesic":geod,"los":self.los(s,p),"disconnected":float(disc),
              "source_x":float(s[0]),"source_y":float(s[1]),"probe_x":float(p[0]),"probe_y":float(p[1])}
        names=("wind_speed","along_signed","along_positive","adverse_fraction","crosswind_rms",
               "along_std","travel_time","source_speed","probe_speed","local_cosine")
        if disc:
            base.update({f"{name}_{stat}": (geod/.05 if name=="travel_time" and stat=="mean" else 0.0)
                         for name in names for stat in ("mean","std")})
            return base
        steps=np.diff(points,axis=0)
        ds=np.linalg.norm(steps,axis=1)
        tangent=steps/ds[:,None]
        v=self.interp((points[:-1]+points[1:])/2)
        along=np.einsum("wpi,pi->wp",v,tangent)
        cross=np.abs(v[:,:,0]*tangent[None,:,1]-v[:,:,1]*tangent[None,:,0])
        weights=ds/ds.sum()
        wmean=lambda values: np.sum(values*weights[None,:],axis=1)
        source_w=self.interp(s[None,:])[:,0,:]
        probe_w=self.interp(p[None,:])[:,0,:]
        ss=np.linalg.norm(source_w,axis=1)
        ps=np.linalg.norm(probe_w,axis=1)
        cosine=np.divide(np.sum(source_w*probe_w,axis=1),ss*ps,out=np.zeros(11),where=ss*ps>1e-12)
        ma=wmean(along)
        each={"wind_speed":wmean(np.linalg.norm(v,axis=2)),"along_signed":ma,
              "along_positive":wmean(np.maximum(along,0)),"adverse_fraction":wmean((along<0).astype(float)),
              "crosswind_rms":np.sqrt(wmean(cross**2)),
              "along_std":np.sqrt(wmean((along-ma[:,None])**2)),
              "travel_time":np.sum(ds[None,:]/np.maximum(np.maximum(along,0),.05),axis=1),
              "source_speed":ss,"probe_speed":ps,"local_cosine":cosine}
        for name, values in each.items():
            base[f"{name}_mean"]=float(np.mean(values))
            base[f"{name}_std"]=float(np.std(values))
        return base


def source_panels():
    central=readcsv(PANEL,"\t")
    offstrip=[r for r in readcsv(E1,"\t") if r["house"]=="House02"]
    return {"CENTRAL":central,"OFFSTRIP":offstrip}


def probes():
    gate=json.loads((ASSET/"gate1a_contract.json").read_text())
    g1a=gate["probe_points"]
    e2=sorted((r for r in readcsv(ASSET/"e1_probe_contracts.tsv","\t") if r["house"]=="House02"),key=lambda r:int(r["probe_rank"]))
    return {"P_G1A":np.array([[float(r["center_x_m"]),float(r["center_y_m"])] for r in g1a]),
            "P_E2":np.array([[float(r["center_x_m"]),float(r["center_y_m"])] for r in e2])}


def pair_band(pair,panel):
    a=panel[int(pair["source0_index"])]
    b=panel[int(pair["source1_index"])]
    if pair["panel"]!="CENTRAL":
        return "OFFSTRIP"
    ix=min(int(a["pmfs_i"]),int(b["pmfs_i"]))
    return (ix-1)//6


def aggregate(a,b):
    keys=list(a[0])
    result={}
    for key in keys:
        va=np.array([r[key] for r in a],dtype=float)
        vb=np.array([r[key] for r in b],dtype=float)
        diff=va-vb
        ad=np.abs(diff)
        den=float(np.linalg.norm(va)*np.linalg.norm(vb))
        result.update({f"{key}_mean_abs":float(ad.mean()),f"{key}_rms":float(np.sqrt(np.mean(diff**2))),
                       f"{key}_max_abs":float(ad.max()),f"{key}_median_abs":float(np.median(ad)),
                       f"{key}_cosine":float(np.dot(va,vb)/den) if den>1e-12 else 0.0})
    return result


def make_pair_features(pair,panel,pp,descs,world):
    ai,bi=int(pair["source0_index"]),int(pair["source1_index"])
    a=panel[ai];b=panel[bi]
    s=np.array([float(a["x_m"]),float(a["y_m"])]);t=np.array([float(b["x_m"]),float(b["y_m"])])
    xy=(s+t)/2
    orient=math.atan2(t[1]-s[1],t[0]-s[0])
    source_only={"mid_x":float(xy[0]),"mid_y":float(xy[1]),"orientation":orient,
                 "orientation_cos":math.cos(orient),"orientation_sin":math.sin(orient),
                 "source0_x":float(s[0]),"source0_y":float(s[1]),"source1_x":float(t[0]),"source1_y":float(t[1]),
                 "separation":float(np.linalg.norm(t-s))}
    protocol={}
    for name, probeset in pp.items():
        aa=[descs[ai,name,j] for j in range(30)]
        bb=[descs[bi,name,j] for j in range(30)]
        geom_keys=("source_x","source_y","probe_x","probe_y","euclidean","geodesic","los","disconnected")
        g=aggregate([{k:r[k] for k in geom_keys} for r in aa],[{k:r[k] for k in geom_keys} for r in bb])
        full=aggregate(aa,bb)
        extras={"probe_centroid_x":float(probeset[:,0].mean()),"probe_centroid_y":float(probeset[:,1].mean()),
                "probe_spread_x":float(probeset[:,0].std()),"probe_spread_y":float(probeset[:,1].std()),
                "los_disagreement_fraction":float(np.mean([abs(x["los"]-y["los"]) for x,y in zip(aa,bb)]))}
        g.update(extras);full.update(extras)
        # Low-capacity local wind rule, evaluated at source and direct source-to-probe vector.
        simple=[]
        for src in (s,t):
            local=world.interp(src[None,:])[:,0,:]
            speed=np.linalg.norm(local,axis=1)
            direction=np.divide(local,speed[:,None],out=np.zeros_like(local),where=speed[:,None]>1e-12)
            direct=probeset-src[None,:]
            dist=np.linalg.norm(direct,axis=1)
            unit=np.divide(direct,dist[:,None],out=np.zeros_like(direct),where=dist[:,None]>1e-12)
            align=np.einsum("wi,pi->wp",direction,unit)
            simple.append({"alignment":align,"source_speed":np.repeat(speed[:,None],30,axis=1),
                           "euclidean":np.repeat(dist[None,:],11,axis=0)})
        local_feature={}
        for key in ("alignment","source_speed","euclidean"):
            diff=simple[0][key]-simple[1][key]
            local_feature[f"{key}_mean_diff"]=float(diff.mean())
            local_feature[f"{key}_rms_diff"]=float(np.sqrt(np.mean(diff**2)))
        protocol[name]=(g,local_feature,full)
    out={"SOURCE_ONLY":source_only}
    for family,pos in (("GEOM",0),("SIMPLE_WIND",1),("PHYS",2)):
        one=protocol["P_G1A"][pos];two=protocol["P_E2"][pos]
        assert list(one)==list(two)
        out[family]={k:two[k]-one[k] for k in one}
    return out


def feature_stage():
    lock=json.loads((OUT/"RPO_G0_PRE_RUN_LOCK.json").read_text())
    assert sha(CODE)==lock["code_sha256"]
    audit()
    for family in FAMILIES:
        if (OUT/f"RPO_G0_{family}_FEATURES.csv").exists():
            raise FileExistsError(family)
    world=World();panel=source_panels();pp=probes()
    panelxy={k:[np.array([float(r["x_m"]),float(r["y_m"])]) for r in rows] for k,rows in panel.items()}
    all_probes=np.concatenate([pp[p] for p in PROTOCOLS])
    all_rows={family:[] for family in FAMILIES}
    connected={}
    for group in ("CENTRAL","OFFSTRIP"):
        desc={}
        world.paths_from_sources(panelxy[group],all_probes)
        for si,src in enumerate(panelxy[group]):
            for k,name in enumerate(PROTOCOLS):
                for j,probe in enumerate(pp[name]):
                    desc[si,name,j]=world.path_desc(src,probe,si,k*30+j)
        connected[group]=sum(v[2] for v in world.cache.values())
        for pair in [r for r in readcsv(UP/"SPX_G0_FROZEN_PAIRS.csv") if r["panel"]==group]:
            values=make_pair_features(pair,panel[group],pp,desc,world)
            for family,feats in values.items():
                all_rows[family].append({"panel":group,"pair_index":int(pair["pair_index"]),
                                         "x_band":pair_band(pair,panel[group]),**feats})
        world.cache.clear()
        print("FEATURES_PANEL",group,"pairs",len([r for r in all_rows["PHYS"] if r["panel"]==group]),flush=True)
    hashes={}
    for family,rows in all_rows.items():
        if not np.isfinite(np.array([[float(v) for k,v in r.items() if k not in ("panel","pair_index","x_band")] for r in rows])).all():
            raise ValueError(f"nonfinite feature: {family}")
        file=OUT/f"RPO_G0_{family}_FEATURES.csv"
        writecsv(file,rows);hashes[family]=sha(file)
    jwrite(OUT/"RPO_G0_FEATURE_FREEZE.json",{"feature_sha256":hashes,"feature_rows":87,
           "feature_inputs_are_physical_only":True,"target_imported":False,"disconnected_source_probe_paths":connected})
    print("FEATURE_FREEZE",hashes)


def check_feature_freeze():
    lock=json.loads((OUT/"RPO_G0_PRE_RUN_LOCK.json").read_text())
    assert sha(CODE)==lock["code_sha256"]
    frozen=json.loads((OUT/"RPO_G0_FEATURE_FREEZE.json").read_text())
    for family in FAMILIES:
        assert sha(OUT/f"RPO_G0_{family}_FEATURES.csv")==frozen["feature_sha256"][family]
    return frozen


def target_values(panel):
    if panel=="OFFSTRIP":
        rr=sorted(readcsv(RIA/"RIA_A0_OFFSTRIP_STRESS.csv"),key=lambda r:int(r["pair_index"]))
        assert len(rr)==3
        return np.array([[float(r["Delta_CNR"]),float(r["Delta_ED"])] for r in rr])
    rr=[r for r in readcsv(RIA/"RIA_A0_REFERENCE_IDENTIFIABILITY.csv") if r["panel"]==panel]
    lookup={(int(r["pair_index"]),r["protocol"]):r for r in rr}
    return np.array([[float(lookup[i,"P_E2"][f"D_{name}"])-float(lookup[i,"P_G1A"][f"D_{name}"])
                      for name in TARGETS] for i in range(84 if panel=="CENTRAL" else 3)])


def train_predict(x,y,bands,train,test):
    best=None
    for alpha in ALPHAS:
        errors=[]
        for inner_band in sorted(set(bands[train])):
            fit=train[bands[train]!=inner_band]
            val=train[bands[train]==inner_band]
            scaler=StandardScaler().fit(x[fit])
            model=Ridge(alpha=alpha).fit(scaler.transform(x[fit]),y[fit])
            errors.extend((y[val]-model.predict(scaler.transform(x[val])))**2)
        mse=float(np.mean(errors))
        if best is None or mse<best[0]:
            best=(mse,alpha)
    scaler=StandardScaler().fit(x[train])
    model=Ridge(alpha=best[1]).fit(scaler.transform(x[train]),y[train])
    return model.predict(scaler.transform(x[test])),best[1]


def matrices(panel):
    result={}
    for family in FAMILIES:
        rr=[r for r in readcsv(OUT/f"RPO_G0_{family}_FEATURES.csv") if r["panel"]==panel]
        rr=sorted(rr,key=lambda r:int(r["pair_index"]))
        assert len(rr)==(84 if panel=="CENTRAL" else 3)
        names=[k for k in rr[0] if k not in ("panel","pair_index","x_band")]
        result[family]=np.array([[float(r[n]) for n in names] for r in rr])
    return result


def spearman_boot(x,y,draws):
    xx=rankdata(x[draws],axis=1)
    yy=rankdata(y[draws],axis=1)
    xx-=xx.mean(axis=1,keepdims=True);yy-=yy.mean(axis=1,keepdims=True)
    den=np.sqrt(np.sum(xx**2,axis=1)*np.sum(yy**2,axis=1))
    values=np.divide(np.sum(xx*yy,axis=1),den,out=np.zeros(len(draws)),where=den>0)
    return values


def balacc(y,pred):
    keep=np.abs(y)>=1e-10
    if len(np.unique(y[keep]>0))<2:
        return None
    return float(balanced_accuracy_score(y[keep]>0,pred[keep]>0))


def predict_stage():
    check_feature_freeze()
    mats=matrices("CENTRAL")
    pair=[r for r in readcsv(UP/"SPX_G0_FROZEN_PAIRS.csv") if r["panel"]=="CENTRAL"]
    bands=np.array([pair_band(p,source_panels()["CENTRAL"]) for p in pair])
    assert np.bincount(bands,minlength=4).tolist()==[21]*4
    y=target_values("CENTRAL")
    predictions=np.full((84,2,4),np.nan)
    alpha_rows=[]
    for k,target in enumerate(TARGETS):
        for f,family in enumerate(FAMILIES):
            for band in range(4):
                train=np.flatnonzero(bands!=band);test=np.flatnonzero(bands==band)
                pred,alpha=train_predict(mats[family],y[:,k],bands,train,test)
                predictions[test,k,f]=pred
                alpha_rows.append({"target":target,"family":family,"heldout_band":band,"alpha":alpha})
    assert np.isfinite(predictions).all()
    writecsv(OUT/"RPO_G0_HELDOUT_PREDICTIONS.csv",
             [{"pair_index":i,"x_band":int(bands[i]),"target":target,"y":float(y[i,k]),
               **{family:float(predictions[i,k,f]) for f,family in enumerate(FAMILIES)}}
              for i in range(84) for k,target in enumerate(TARGETS)])
    writecsv(OUT/"RPO_G0_NESTED_ALPHA.csv",alpha_rows)
    rng=np.random.default_rng(SEED)
    draws=rng.integers(0,84,(10000,84),dtype=np.int32)
    bs_arrays={}
    summaries={};band_rows=[]
    for k,target in enumerate(TARGETS):
        z=y[:,k];phys=predictions[:,k,3]
        rank=spearmanr(z,phys).statistic
        rho_bs=spearman_boot(z,phys,draws)
        bs_arrays[f"{target}_rho"]=rho_bs
        t={"PHYS_spearman":float(rank),"PHYS_spearman_CI95":np.quantile(rho_bs,[.025,.975]).tolist(),
           "sign_balanced_accuracy":{family:balacc(z,predictions[:,k,f]) for f,family in enumerate(FAMILIES)}}
        errors={family:(z-predictions[:,k,f])**2 for f,family in enumerate(FAMILIES)}
        t["MSE"]={family:float(np.mean(err)) for family,err in errors.items()}
        t["advantages"]={}
        for baseline in ("GEOM","SIMPLE_WIND"):
            gain=errors[baseline]-errors["PHYS"]
            values=gain[draws].mean(axis=1)
            bs_arrays[f"{target}_advantage_{baseline}"]=values
            t["advantages"][baseline]={"mean":float(gain.mean()),"CI95":np.quantile(values,[.025,.975]).tolist(),
                                         "positive_bands":int(sum(np.mean(gain[bands==b])>0 for b in range(4)))}
            for band in range(4):
                band_rows.append({"target":target,"baseline":baseline,"x_band":band,
                                  "mean_squared_error_advantage":float(np.mean(gain[bands==band])),
                                  "PHYS_spearman":float(spearmanr(z[bands==band],phys[bands==band]).statistic),
                                  "n_pairs":int(sum(bands==band))})
        pass_g1=t["PHYS_spearman"]>=.30 and t["PHYS_spearman_CI95"][0]>0
        pass_g2=t["advantages"]["GEOM"]["mean"]>0 and t["advantages"]["GEOM"]["CI95"][0]>0
        pass_g3=t["advantages"]["SIMPLE_WIND"]["mean"]>0 and t["advantages"]["SIMPLE_WIND"]["CI95"][0]>0
        acc=t["sign_balanced_accuracy"]
        pass_g4=acc["PHYS"] is not None and acc["PHYS"]>=.60 and acc["PHYS"]>=acc["GEOM"] and acc["PHYS"]>=acc["SIMPLE_WIND"]
        pass_g5=all(t["advantages"][base]["positive_bands"]>=3 for base in ("GEOM","SIMPLE_WIND"))
        t["gates"]={"G0_1":bool(pass_g1),"G0_2":bool(pass_g2),"G0_3":bool(pass_g3),"G0_4":bool(pass_g4),"G0_5":bool(pass_g5)}
        summaries[target]=t
    writecsv(OUT/"RPO_G0_BAND_SUMMARY.csv",band_rows)
    np.savez_compressed(OUT/"RPO_G0_BOOTSTRAP_10000.npz",pair_draws=draws,**bs_arrays)
    decision=("RPO_G0_PASS_PHYSICAL_RELATIONAL_CONTEXT_PREDICTS_IDENTIFIABILITY" if
              all(all(t["gates"].values()) for t in summaries.values()) else
              "RPO_G0_STOP_PHYSICAL_CONTEXT_NOT_PREDICTIVE_BEYOND_BASELINES")
    result={"decision":decision,"house":"House02","wind":"3,5-1_slow","central_pairs":84,
            "new_plume":0,"offstrip_read_before_decision":False,"targets":summaries,
            "feature_freeze_sha256":sha(OUT/"RPO_G0_FEATURE_FREEZE.json"),
            "predictions_sha256":sha(OUT/"RPO_G0_HELDOUT_PREDICTIONS.csv")}
    jwrite(OUT/"RPO_G0_RESULT.json",result)
    print("RPO_CENTRAL_DECISION",decision)


def stress_stage():
    result=OUT/"RPO_G0_RESULT.json"
    if not result.exists():
        raise FileNotFoundError("CENTRAL decision must be frozen first")
    before=sha(result)
    check_feature_freeze()
    central=matrices("CENTRAL")["PHYS"]
    off=matrices("OFFSTRIP")["PHYS"]
    yc=target_values("CENTRAL");yo=target_values("OFFSTRIP")
    rows=[]
    for k,name in enumerate(TARGETS):
        scaler=StandardScaler().fit(central)
        # Full-CENTRAL alpha is selected by four-band CV; OFFSTRIP is never used in this selection.
        bands=np.array([pair_band(p,source_panels()["CENTRAL"]) for p in readcsv(UP/"SPX_G0_FROZEN_PAIRS.csv") if p["panel"]=="CENTRAL"])
        best=None
        for alpha in ALPHAS:
            losses=[]
            for band in range(4):
                train=bands!=band;test=bands==band
                ss=StandardScaler().fit(central[train])
                mm=Ridge(alpha=alpha).fit(ss.transform(central[train]),yc[train,k])
                losses.extend((yc[test,k]-mm.predict(ss.transform(central[test])))**2)
            mse=float(np.mean(losses))
            if best is None or mse<best[0]:best=(mse,alpha)
        model=Ridge(alpha=best[1]).fit(scaler.transform(central),yc[:,k])
        pred=model.predict(scaler.transform(off))
        for i in range(3):
            rows.append({"pair_index":i,"target":name,"observed":float(yo[i,k]),"predicted":float(pred[i]),
                         "observed_sign":int(np.sign(yo[i,k])),"predicted_sign":int(np.sign(pred[i])),
                         "alpha_CENTRAL_only":best[1]})
    writecsv(OUT/"RPO_G0_OFFSTRIP_STRESS.csv",rows)
    assert sha(result)==before
    print("OFFSTRIP_DESCRIPTIVE_ONLY",len(rows))


def main():
    ap=argparse.ArgumentParser();ap.add_argument("stage",choices=("lock","features","predict","stress"))
    args=ap.parse_args()
    {"lock":lock_stage,"features":feature_stage,"predict":predict_stage,"stress":stress_stage}[args.stage]()

if __name__=="__main__":main()
