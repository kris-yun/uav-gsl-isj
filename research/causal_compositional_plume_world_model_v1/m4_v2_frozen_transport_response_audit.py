#!/usr/bin/env python3
"""Kill-only transport-response audit for the frozen M4-v2 House02 checkpoints.

No training, no checkpoint mutation, no new plume seed, and no architecture change.
This audit can kill M4-v2 as a transport mechanism; it cannot promote it to ADVANCE.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank"
MODEL_ROOT = ROOT / "evidence/causal_compositional_plume_world_model_v1/m4_c05_local_compare_20260923_frozen_v2"
MODEL_SCRIPT = ROOT / "research/causal_compositional_plume_world_model_v1/c05_frozen_local_comparison_v2.py"
OUT = ROOT / "evidence/causal_compositional_plume_world_model_v1/M4_V2_FROZEN_TRANSPORT_RESPONSE_AUDIT_20260923.json"
TIMES = (100,150,200,250,300,350,400,450,500,550)
TRAIN_SEEDS = (1729,2718)

# Predeclared kill-only boundaries. Crossing one can reject a reusable-transport
# interpretation, but not crossing them cannot establish ADVANCE.
MIN_WIND_AMPLITUDE_RATIO = 0.10
MIN_WIND_DELTA_COSINE = 0.0
MAX_NONPOSITIVE_COSINE_COMPARISONS = 1
MIN_RELATIVE_WIND_TO_SOURCE_RATIO = 0.25


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("m4v2_frozen", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_context():
    geo = BANK / "geometry"
    return {
        "source": {
            "S1": np.load(geo / "source_map_S1.npy", allow_pickle=False).astype(np.float32),
            "S2": np.load(geo / "source_map_S2.npy", allow_pickle=False).astype(np.float32),
        },
        "wind": {
            "W1": np.load(geo / "wind_W1_z0p20.npy", allow_pickle=False).astype(np.float32),
            "W2": np.load(geo / "wind_W2_z0p20.npy", allow_pickle=False).astype(np.float32),
        },
        "mask": (np.load(geo / "obstacle_mask_z0p20.npy", allow_pickle=False) > 0).astype(np.float32),
    }


def model_inputs(ctx, source_id: str, wind_id: str) -> torch.Tensor:
    source = ctx["source"][source_id]
    wind = ctx["wind"][wind_id]
    mask = ctx["mask"]
    xs = []
    for t in TIMES:
        time = np.full_like(source, t / 550.0)
        xs.append(np.concatenate((source[None], wind.transpose(2,0,1), mask[None], time[None])))
    x = torch.from_numpy(np.stack(xs))
    return torch.cat((
        F.max_pool2d(x[:,0:1], 2, ceil_mode=True),
        F.avg_pool2d(x[:,1:4], 2, ceil_mode=True),
        F.max_pool2d(x[:,4:5], 2, ceil_mode=True),
        F.avg_pool2d(x[:,5:6], 2, ceil_mode=True),
    ), dim=1)


def target(source: str, wind: str, plume_seed: str) -> torch.Tensor:
    p = BANK / "realizations" / f"{source}_{wind}_{plume_seed}" / "concentration.npy"
    a = np.load(p, allow_pickle=False)
    if a.shape != (10,83,119):
        raise ValueError(f"shape drift: {p}: {a.shape}")
    return F.avg_pool2d(torch.from_numpy(np.log1p(a[:,None]).astype(np.float32)), 2, ceil_mode=True)


def free_mask(ctx) -> torch.Tensor:
    m = torch.from_numpy(ctx["mask"][None,None])
    return (1.0 - F.max_pool2d(m, 2, ceil_mode=True))[0,0] > 0.5


def flatten_free(x: torch.Tensor, free: torch.Tensor) -> torch.Tensor:
    return x[:,0][:,free].reshape(-1).double()


def delta_metrics(pred_delta: torch.Tensor, true_delta: torch.Tensor, free: torch.Tensor):
    p = flatten_free(pred_delta, free)
    y = flatten_free(true_delta, free)
    pn = float(torch.linalg.vector_norm(p))
    yn = float(torch.linalg.vector_norm(y))
    dot = float(torch.dot(p,y))
    cosine = dot / (pn*yn) if pn > 0 and yn > 0 else float("nan")
    relerr = float(torch.linalg.vector_norm(p-y)) / yn if yn > 0 else float("nan")
    return {
        "pred_norm": pn,
        "true_norm": yn,
        "amplitude_ratio_pred_over_true": pn/yn if yn > 0 else float("nan"),
        "delta_cosine": cosine,
        "relative_delta_error": relerr,
    }


def centroid_series(field: torch.Tensor, free: torch.Tensor):
    a = field[:,0].clamp_min(0).double()
    a = a * free.double()[None]
    rr, cc = torch.meshgrid(
        torch.arange(a.shape[1], dtype=torch.double),
        torch.arange(a.shape[2], dtype=torch.double),
        indexing="ij",
    )
    out = []
    for t in range(a.shape[0]):
        mass = float(a[t].sum())
        if mass <= 1e-12:
            out.append([float("nan"),float("nan")])
        else:
            out.append([
                float((a[t]*rr).sum()/mass),
                float((a[t]*cc).sum()/mass),
            ])
    return np.asarray(out, dtype=np.float64)


def centroid_shift_metrics(f1: torch.Tensor, f2: torch.Tensor, free: torch.Tensor):
    c1 = centroid_series(f1, free)
    c2 = centroid_series(f2, free)
    d = c2-c1
    valid = np.isfinite(d).all(axis=1)
    if not valid.any():
        return {"mean_shift":[float("nan"),float("nan")],"mean_shift_norm":float("nan")}
    mean = d[valid].mean(axis=0)
    return {"mean_shift":mean.tolist(),"mean_shift_norm":float(np.linalg.norm(mean))}


def vector_alignment(a, b):
    a=np.asarray(a,dtype=float); b=np.asarray(b,dtype=float)
    an=np.linalg.norm(a); bn=np.linalg.norm(b)
    return float(np.dot(a,b)/(an*bn)) if an>0 and bn>0 else float("nan")


def main():
    torch.set_num_threads(4)
    module = load_module(MODEL_SCRIPT)
    ctx = load_context()
    free = free_mask(ctx)

    x_s2_w1 = model_inputs(ctx,"S2","W1")
    x_s2_w2 = model_inputs(ctx,"S2","W2")
    x_s1_w2 = model_inputs(ctx,"S1","W2")

    manifest = json.loads((MODEL_ROOT/"train_manifest.json").read_text())
    result = {
        "status":"KILL_ONLY_AUDIT",
        "frozen_parent_commit":"0f322a5561f4a1ba05c19544f3094f8b09e12665",
        "rules":{
            "min_wind_amplitude_ratio":MIN_WIND_AMPLITUDE_RATIO,
            "max_nonpositive_cosine_comparisons":MAX_NONPOSITIVE_COSINE_COMPARISONS,
            "min_relative_wind_to_source_ratio":MIN_RELATIVE_WIND_TO_SOURCE_RATIO,
            "note":"Failing a rule can kill reusable transport; surviving cannot establish ADVANCE."
        },
        "checkpoint_hashes":{},
        "comparisons":{},
        "summary":{},
    }

    # True effects are paired by the same GADEN plume RNG seed across intervention cells.
    true_by_seed={}
    for ps in ("A","B"):
        y_s2_w1=target("S2","W1",ps)
        y_s2_w2=target("S2","W2",ps)
        y_s1_w2=target("S1","W2",ps)
        dw=y_s2_w2-y_s2_w1
        ds=y_s2_w2-y_s1_w2
        true_by_seed[ps]=(y_s2_w1,y_s2_w2,y_s1_w2,dw,ds)

    nonpositive=0
    operator_seed_summaries={}
    with torch.no_grad():
        for kind, ctor in (("monolithic",module.MonolithicModel),("operator",module.OperatorModel)):
            for train_seed in TRAIN_SEEDS:
                key=f"{kind}_seed{train_seed}"
                cp=MODEL_ROOT/f"{key}.pt"
                digest=sha256(cp)
                expected=manifest["fits"][key]["checkpoint_sha256"]
                if digest != expected:
                    raise RuntimeError(f"checkpoint hash drift {key}: {digest} != {expected}")
                result["checkpoint_hashes"][key]=digest
                model=ctor()
                model.load_state_dict(torch.load(cp,map_location="cpu",weights_only=True))
                model.eval()
                p_w1=model(x_s2_w1)
                p_w2=model(x_s2_w2)
                p_s1=model(x_s1_w2)
                pdw=p_w2-p_w1
                pds=p_w2-p_s1
                pred_wind_norm=float(torch.linalg.vector_norm(flatten_free(pdw,free)))
                pred_source_norm=float(torch.linalg.vector_norm(flatten_free(pds,free)))
                per_seed={}
                for ps,(y_w1,y_w2,y_s1,dw,ds) in true_by_seed.items():
                    wm=delta_metrics(pdw,dw,free)
                    sm=delta_metrics(pds,ds,free)
                    true_wind_norm=wm["true_norm"]
                    true_source_norm=sm["true_norm"]
                    true_ws=true_wind_norm/true_source_norm if true_source_norm>0 else float("nan")
                    pred_ws=pred_wind_norm/pred_source_norm if pred_source_norm>0 else float("nan")
                    relative_ws=pred_ws/true_ws if true_ws>0 else float("nan")
                    tc=centroid_shift_metrics(y_w1,y_w2,free)
                    pc=centroid_shift_metrics(p_w1,p_w2,free)
                    per_seed[ps]={
                        "wind_delta":wm,
                        "source_delta":sm,
                        "wind_to_source_ratio_true":true_ws,
                        "wind_to_source_ratio_pred":pred_ws,
                        "relative_wind_to_source_ratio":relative_ws,
                        "true_wind_centroid_shift":tc,
                        "pred_wind_centroid_shift":pc,
                        "centroid_shift_cosine":vector_alignment(tc["mean_shift"],pc["mean_shift"]),
                    }
                    if kind=="operator" and (not math.isfinite(wm["delta_cosine"]) or wm["delta_cosine"] <= MIN_WIND_DELTA_COSINE):
                        nonpositive += 1
                result["comparisons"][key]=per_seed

    for train_seed in TRAIN_SEEDS:
        vals=[result["comparisons"][f"operator_seed{train_seed}"][ps] for ps in ("A","B")]
        operator_seed_summaries[str(train_seed)]={
            "max_wind_amplitude_ratio":max(v["wind_delta"]["amplitude_ratio_pred_over_true"] for v in vals),
            "min_relative_wind_to_source_ratio":min(v["relative_wind_to_source_ratio"] for v in vals),
            "wind_delta_cosines":[v["wind_delta"]["delta_cosine"] for v in vals],
        }

    k1=all(v["max_wind_amplitude_ratio"] < MIN_WIND_AMPLITUDE_RATIO for v in operator_seed_summaries.values())
    k2=nonpositive > MAX_NONPOSITIVE_COSINE_COMPARISONS
    k3=all(v["min_relative_wind_to_source_ratio"] < MIN_RELATIVE_WIND_TO_SOURCE_RATIO for v in operator_seed_summaries.values())
    killed=bool(k1 or k2 or k3)
    result["summary"]={
        "operator_training_seed_summary":operator_seed_summaries,
        "nonpositive_wind_delta_cosine_comparisons":nonpositive,
        "kill_rules":{"K1_low_wind_amplitude":k1,"K2_wrong_wind_pattern":k2,"K3_wind_suppressed_vs_source":k3},
        "decision":"NO_GO_REUSABLE_TRANSPORT_MECHANISM" if killed else "SURVIVES_KILL_ONLY_AUDIT_NO_ADVANCE",
        "next_step":"STOP_M4_V2_AS_MAIN" if killed else "DENSE_MULTI_CANDIDATE_INVERSE_RANKING",
    }
    OUT.write_text(json.dumps(result,indent=2,allow_nan=True)+"\n")
    print("===M4_V2_AUDIT_JSON===")
    print(json.dumps(result,indent=2,allow_nan=True))
    print("===M4_V2_AUDIT_DECISION===")
    print(result["summary"]["decision"])
    print(json.dumps(result["summary"],indent=2,allow_nan=True))

if __name__=="__main__":
    main()
