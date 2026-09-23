#!/usr/bin/env python3
"""M6 G0.5-B: load the official GeoPT checkpoint and run a real House02 forward.

No plume training. This is a strict compatibility/runtime gate.

Inputs:
- exact official GeoPT checkout;
- official Hugging Face checkpoint/config;
- one prebuilt House02 x[N,3], fx[N,11] NPZ.

Reports:
- checkpoint SHA256;
- checkpoint/model tensor counts;
- exact loaded/skipped tensors under the official fine-tune filter
  (exclude final ln_3/mlp2 only);
- parameter coverage;
- first projection shape;
- frozen House02 forward output shape/runtime/RSS.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch


EXPECTED_SHA256="c0b1b9c4e5d533dbc249190d3d1fbe8e6b066b36d325cf4377cc0d613c02d1c2"
EXCLUDE=("mlp2","ln_3")


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()


def numel_state(d):
    return int(sum(int(v.numel()) for v in d.values() if torch.is_tensor(v)))


def rss_mb():
    try:
        import resource
        # Linux ru_maxrss is KiB.
        return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/1024.0
    except Exception:
        return float("nan")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--geopt-root",type=Path,required=True)
    ap.add_argument("--checkpoint",type=Path,required=True)
    ap.add_argument("--config",type=Path,required=True)
    ap.add_argument("--house-npz",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()

    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)

    digest=sha256(args.checkpoint)
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"official checkpoint hash mismatch: {digest} != {EXPECTED_SHA256}")

    config=json.loads(args.config.read_text())
    sys.path.insert(0,str(args.geopt_root))
    Transolver=importlib.import_module("models.Transolver")

    # Exact released 8-layer pretraining architecture.
    # The public config/script contract is pos3 + fx11 => preprocess in_features=14.
    model_args=SimpleNamespace(
        fun_dim=11,
        space_dim=3,
        n_hidden=256,
        n_heads=8,
        n_layers=8,
        mlp_ratio=2,
        slice_num=32,
        out_dim=9,
        dropout=0.0,
        act="gelu",
        geotype="unstructured",
        shapelist=None,
        checkpoint=0,
        unified_pos=0,
    )
    torch.manual_seed(20260924)
    model=Transolver.Model(model_args).cpu()
    model_state=model.state_dict()

    raw=torch.load(args.checkpoint,map_location="cpu",weights_only=True)
    if not isinstance(raw,dict):
        raise RuntimeError(f"checkpoint is not state_dict-like: {type(raw)}")
    # Fail closed on nested wrappers; official loader expects a direct state dict.
    if raw and not all(torch.is_tensor(v) for v in raw.values()):
        raise RuntimeError("checkpoint is wrapped/nested; official direct-state loader contract drift")

    filtered={}
    skipped=[]
    for k,v in raw.items():
        reasons=[]
        if k not in model_state:
            reasons.append("missing_in_model")
        else:
            if tuple(model_state[k].shape)!=tuple(v.shape):
                reasons.append(f"shape:{tuple(v.shape)}!={tuple(model_state[k].shape)}")
        if any(ex in k for ex in EXCLUDE):
            reasons.append("official_excluded_head")
        if reasons:
            skipped.append({"key":k,"shape":list(v.shape),"reasons":reasons})
        else:
            filtered[k]=v

    missing_internal=[]
    for k,v in model_state.items():
        if any(ex in k for ex in EXCLUDE):
            continue
        if k not in filtered:
            missing_internal.append({"key":k,"shape":list(v.shape)})

    loaded_param_count=numel_state(filtered)
    checkpoint_param_count=numel_state(raw)
    model_param_count=numel_state(model_state)
    expected_head_param_count=sum(
        int(v.numel()) for k,v in model_state.items() if any(ex in k for ex in EXCLUDE)
    )

    st=model.state_dict()
    st.update(filtered)
    model.load_state_dict(st,strict=True)
    model.eval()

    data=np.load(args.house_npz,allow_pickle=False)
    x=torch.from_numpy(data["x"].astype(np.float32))[None]
    fx=torch.from_numpy(data["fx"].astype(np.float32))[None]
    if x.ndim!=3 or x.shape[-1]!=3:
        raise RuntimeError(f"House x contract drift: {tuple(x.shape)}")
    if fx.ndim!=3 or fx.shape[-1]!=11:
        raise RuntimeError(f"House fx contract drift: {tuple(fx.shape)}")
    if not torch.isfinite(x).all() or not torch.isfinite(fx).all():
        raise RuntimeError("nonfinite House features")

    # Warmup then measured CPU forward.
    with torch.no_grad():
        _=model(x,fx)
        t0=time.perf_counter()
        out=model(x,fx)
        dt=time.perf_counter()-t0

    result={
        "status":"G0_5_B_ACTUAL_CHECKPOINT_LOAD",
        "checkpoint":{
            "path":str(args.checkpoint),
            "sha256":digest,
            "expected_sha256":EXPECTED_SHA256,
            "bytes":args.checkpoint.stat().st_size,
            "tensor_count":len(raw),
            "parameter_count":checkpoint_param_count,
        },
        "official_config_json":config,
        "instantiated_args":vars(model_args),
        "model":{
            "tensor_count":len(model_state),
            "parameter_count":model_param_count,
            "preprocess_weight_shape":list(model_state["preprocess.linear_pre.0.weight"].shape),
            "expected_excluded_head_parameter_count":expected_head_param_count,
        },
        "load":{
            "loaded_tensor_count":len(filtered),
            "loaded_parameter_count":loaded_param_count,
            "loaded_fraction_of_model":loaded_param_count/model_param_count,
            "loaded_fraction_excluding_expected_head":(
                loaded_param_count/(model_param_count-expected_head_param_count)
                if model_param_count>expected_head_param_count else float("nan")
            ),
            "skipped_checkpoint_tensors":skipped,
            "missing_internal_model_tensors":missing_internal,
        },
        "house02_forward":{
            "token_count":int(x.shape[1]),
            "x_shape":list(x.shape),
            "fx_shape":list(fx.shape),
            "output_shape":list(out.shape),
            "output_finite":bool(torch.isfinite(out).all()),
            "cpu_threads":torch.get_num_threads(),
            "forward_seconds":dt,
            "peak_rss_mb":rss_mb(),
        },
    }

    # Frozen pass rule: every non-head model tensor must load, and the only
    # skipped checkpoint tensors may be the official excluded final head.
    only_expected_skips=all(
        item["reasons"]==["official_excluded_head"] for item in skipped
    )
    passed=(
        digest==EXPECTED_SHA256
        and not missing_internal
        and only_expected_skips
        and result["load"]["loaded_fraction_excluding_expected_head"]>0.999999
        and result["house02_forward"]["output_finite"]
        and tuple(out.shape)==(1,int(x.shape[1]),9)
        and tuple(model_state["preprocess.linear_pre.0.weight"].shape)==(512,14)
    )
    result["decision"]="G0_5_B_PASS" if passed else "G0_5_B_NO_GO"

    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=True)+"\n")
    print(json.dumps(result,indent=2,allow_nan=True))


if __name__=="__main__":
    main()
