#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
import numpy as np

EXPECTED_OCC="9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
EXPECTED_BINARY="4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"
EXPECTED_EXTRACTOR="206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91"
EXPECTED_W1_ITER1="2fa27ec72a7f05fbaca58b99e4f9390a5c477ee379d7e247e6fde57bbde49846"
TIMES=(100,150,200,250,300,350,400,450,500,550)

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def parse_kv_tsv(path:Path)->dict[str,str]:
    out={}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        k,v=line.split("\t",1)
        out[k]=v
    return out

def read_occ_header(path:Path):
    lines=path.read_text(encoding="utf-8",errors="replace").splitlines()[:10]
    origin=[float(x) for x in next(x for x in lines if x.startswith("#env_min")).split()[1:]]
    dims=[int(x) for x in next(x for x in lines if x.startswith("#num_cells")).split()[1:]]
    cell=float(next(x for x in lines if x.startswith("#cell_size")).split()[1])
    return origin,dims,cell

def run(cmd, *, env=None, log:Path|None=None):
    if log:
        log.parent.mkdir(parents=True,exist_ok=True)
        with log.open("w",encoding="utf-8") as f:
            subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    else:
        subprocess.run(cmd,env=env,check=True)

def generate_one(binary:Path, extractor:Path, occ:Path, wind_dir:Path, out:Path,
                 source_xyz, seed:int, origin,dims, cell:float):
    cube=out/"concentration.npy"
    meta=out/"run_metadata.json"
    if cube.exists() and meta.exists():
        return json.loads(meta.read_text())
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"incomplete existing output: {out}")
    out.mkdir(parents=True,exist_ok=True)
    real=out/"realization"
    real.mkdir()
    sx,sy,sz=source_xyz
    opts={
      "verbose":"false","wait_preprocessing":"false","sim_time":"300.0","time_step":"0.1",
      "num_filaments_sec":"7","variable_rate":"true","filament_stop_steps":"0",
      "ppm_filament_center":"10.0","filament_initial_std":"10.0","filament_growth_gamma":"15.0",
      "filament_noise_std":"0.01","gas_type":"10","temperature":"298.0","pressure":"1.0",
      "concentration_unit_choice":"1","occupancy3D_data":str(occ),"fixed_frame":"map",
      "wind_data":str(wind_dir),"wind_time_step":"1.0","allow_looping":"true",
      "loop_from_step":"1","loop_to_step":"10","source_position_x":repr(float(sx)),
      "source_position_y":repr(float(sy)),"source_position_z":repr(float(sz)),
      "save_results":"1","results_time_step":"0.5","results_min_time":"0.0",
      "writeConcentrations":"false","results_location":str(real)
    }
    cmd=[str(binary),"--ros-args"]+[z for k,v in opts.items() for z in ("-p",f"{k}:={v}")]
    env=dict(os.environ,GADEN_RNG_SEED=str(seed))
    run(cmd,env=env,log=out/"generation.log")
    text=(out/"generation.log").read_text(errors="replace")
    if "Filament simulator finished correctly!" not in text:
        raise RuntimeError(f"GADEN failed: {out}")
    if len(list(real.glob("iteration_*"))) != 566:
        raise RuntimeError(f"iteration count drift: {out}")
    # The frozen extractor reads occupancy from its environment directory.
    # This is the same asset link used by export_c05_spatial_slices_remote.sh.
    shutil.copyfile(occ,real/"OccupancyGrid3D.csv")
    if sha256(real/"OccupancyGrid3D.csv") != sha256(occ):
        raise RuntimeError("extractor occupancy copy hash drift")
    extract=[
      str(extractor),str(real),str(real),str(cube),str(out/"spatial_metadata.json"),
      repr(origin[0]),repr(origin[1]),repr(cell),"1","0.20",
      str(dims[0]),str(dims[1]),*[str(x) for x in TIMES]
    ]
    run(extract,log=out/"extract.log")
    a=np.load(cube,allow_pickle=False)
    if a.shape!=(10,dims[0],dims[1]) or not np.isfinite(a).all() or (a<0).any():
        raise RuntimeError(f"cube QC fail {out}: {a.shape}")
    rec={
      "source_xyz":[float(x) for x in source_xyz],
      "seed":int(seed),
      "wind_dir":str(wind_dir),
      "wind0_sha256":sha256(wind_dir/"wind_iteration_0"),
      "cube_sha256":sha256(cube),
      "cube_shape":list(a.shape),
      "generation_log_sha256":sha256(out/"generation.log"),
      "extract_log_sha256":sha256(out/"extract.log")
    }
    meta.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    shutil.rmtree(real)
    return rec

def profile(cube:np.ndarray, free:np.ndarray)->np.ndarray:
    x=np.asarray(cube,dtype=np.float64).mean(axis=0)
    v=np.where(free,x,0.0).reshape(-1)
    s=v.sum()
    if not s>0:
        raise ValueError("zero compositional profile")
    return v/s

def affinity(p:np.ndarray,q:np.ndarray)->float:
    return float(np.sqrt(np.maximum(p,0)*np.maximum(q,0)).sum())

def evaluate(full_bank:Path, projected_root:Path):
    g=full_bank/"geometry"
    obs=np.load(g/"obstacle_mask_z0p20.npy",allow_pickle=False)
    free=(obs==0)
    if free.shape!=(83,119):
        raise ValueError(f"free shape drift {free.shape}")
    cubes={}
    for arm in ("full3d","projected2d"):
      for sid in ("S1","S2"):
        for rep in ("A","B"):
          p=(full_bank/"realizations"/f"{sid}_W1_{rep}"/"concentration.npy"
             if arm=="full3d" else projected_root/f"{sid}_{rep}"/"concentration.npy")
          a=np.load(p,allow_pickle=False)
          if a.shape!=(10,83,119):
              raise ValueError(f"{p} shape {a.shape}")
          cubes[(arm,sid,rep)]=profile(a,free)
    rows=[]
    other={"S1":"S2","S2":"S1"}
    opp={"A":"B","B":"A"}
    for sid in ("S1","S2"):
      for rep in ("A","B"):
        tr=opp[rep]
        target=cubes[("full3d",sid,rep)]
        row={"target_source":sid,"target_rep":rep,"template_rep":tr}
        for arm in ("full3d","projected2d"):
          st=affinity(target,cubes[(arm,sid,tr)])
          sf=affinity(target,cubes[(arm,other[sid],tr)])
          row[f"{arm}_truth_affinity"]=st
          row[f"{arm}_false_affinity"]=sf
          row[f"{arm}_margin"]=st-sf
          row[f"{arm}_correct"]=bool(st>sf)
        row["delta_margin_3d_minus_projected"]=row["full3d_margin"]-row["projected2d_margin"]
        rows.append(row)
    full_correct=sum(r["full3d_correct"] for r in rows)
    proj_correct=sum(r["projected2d_correct"] for r in rows)
    deltas=np.asarray([r["delta_margin_3d_minus_projected"] for r in rows])
    improved=int((deltas>0).sum())
    med=float(np.median(deltas))
    if full_correct<4:
        decision="PMFS3D_O0_REFERENCE_3D_NOT_STABLE"
    elif improved>=3 and med>0 and (proj_correct<=2 or med>=0.05):
        decision="PMFS3D_O0_VERTICAL_INFORMATION_STRONG"
    elif improved>=3 and med>0:
        decision="PMFS3D_O0_VERTICAL_INFORMATION_PROMISING"
    else:
        decision="PMFS3D_O0_NO_VERTICAL_INFORMATION_GAIN"
    return {
      "decision":decision,
      "metric":"compositional_static_profile_hellinger_affinity",
      "targets":rows,
      "summary":{
        "full3d_correct":full_correct,
        "projected2d_correct":proj_correct,
        "improved_margin_count":improved,
        "median_delta_margin":med
      }
    }

def self_test():
    free=np.ones((2,2),dtype=bool)
    a=np.array([[[4,0],[0,0]],[[2,0],[0,0]]],dtype=float)
    b=np.array([[[0,4],[0,0]],[[0,2],[0,0]]],dtype=float)
    pa,pb=profile(a,free),profile(b,free)
    assert abs(affinity(pa,pa)-1)<1e-12 and affinity(pa,pb)==0
    print("PMFS3D_O0_GATE_SELF_TEST_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path)
    ap.add_argument("--canonical-root",type=Path,default=Path("/mnt/hgfs/workspace/GADEN_files/scenarios"))
    ap.add_argument("--binary",type=Path,default=Path("/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"))
    ap.add_argument("--extractor",type=Path,default=Path("/home/zyc/rmfe_filament_extractor_omp"))
    ap.add_argument("--work-root",type=Path,default=Path("/home/zyc/PMFS3D_O0_PROJECTED2D_20261001"))
    ap.add_argument("--result-json",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        self_test()
        return
    repo=args.repo_root or Path(subprocess.check_output(["git","rev-parse","--show-toplevel"],text=True).strip())
    if sha256(args.binary)!=EXPECTED_BINARY:
        raise RuntimeError("GADEN binary hash drift")
    if sha256(args.extractor)!=EXPECTED_EXTRACTOR:
        raise RuntimeError("extractor hash drift")
    occ=args.canonical_root/"House02"/"OccupancyGrid3D.csv"
    if sha256(occ)!=EXPECTED_OCC:
        raise RuntimeError("House02 occupancy hash drift")
    wind_full=args.canonical_root/"House02"/"gas_simulations"/"3,5-1_fast"/"FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20"/"wind"
    if sha256(wind_full/"wind_iteration_1")!=EXPECTED_W1_ITER1:
        raise RuntimeError("W1 wind anchor drift")
    bank=repo/"evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
    meta=json.loads((bank/"geometry/context_metadata.json").read_text())
    contract=parse_kv_tsv(bank/"bank_contract.tsv")
    sources={sid:meta["source_maps"][sid]["xyz_m"] for sid in ("S1","S2")}
    if any(abs(float(v[2])-0.2)>1e-12 for v in sources.values()):
        raise RuntimeError("source z not fixed at 0.2")
    seeds={"A":int(contract["seed_A"]),"B":int(contract["seed_B"])}
    projected=args.work_root/"projected2d_wind"
    projector=repo/"research/pmfs3d_o0/project_wind_to_2d.py"
    if not projected.exists():
        run([sys.executable,str(projector),str(occ),str(wind_full),str(projected),"--sensor-z","0.20"])
    pmanifest=json.loads((projected/"projection_manifest.json").read_text())
    if not all(r["max_abs_w"]==0.0 and r["uv_source_slice_preserved"] for r in pmanifest["records"]):
        raise RuntimeError("projected wind contract fail")
    origin,dims,cell=read_occ_header(occ)
    run_root=args.work_root/"projected2d_runs"
    generation=[]
    for sid in ("S1","S2"):
      for rep in ("A","B"):
        generation.append(generate_one(
          args.binary,args.extractor,occ,projected,run_root/f"{sid}_{rep}",
          sources[sid],seeds[rep],origin,dims,cell))
    result=evaluate(bank,run_root)
    result["scope"]="House02 W1 DEVELOPMENT ONLY; fixed source z=0.2; target fields are full-3D GADEN; projected arm uses sensor-height u,v extruded over z and w=0"
    result["source_xyz"]=sources
    result["seeds"]=seeds
    result["provenance"]={
      "occupancy_sha256":sha256(occ),
      "wind_iteration1_sha256":sha256(wind_full/"wind_iteration_1"),
      "binary_sha256":sha256(args.binary),
      "extractor_sha256":sha256(args.extractor),
      "projection_manifest_sha256":sha256(projected/"projection_manifest.json")
    }
    result["generated_projected_runs"]=generation
    out=args.result_json or (repo/"evidence/pmfs3d_o0_projected2d_20261001/O0_RESULT.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
