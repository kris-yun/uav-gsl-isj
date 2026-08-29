#!/usr/bin/env python3
"""Export frozen PF-SNRE checkpoint to dependency-free C++ binary runtime format."""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
import torch
from pf_snre_final_core import ConditionedMomentSetDirectNRE

MAGIC=b"PFSNRE1\0"; FIXMAGIC=b"PFSFX01\0"
ORDER=("member_encoder.0.weight","member_encoder.0.bias","member_encoder.2.weight","member_encoder.2.bias",
       "block_encoder.0.weight","block_encoder.0.bias","block_encoder.2.weight","block_encoder.2.bias",
       "head.0.weight","head.0.bias","head.2.weight","head.2.bias","head.4.weight","head.4.bias")
EXPECTED_SHAPES=((32,40),(32,),(32,32),(32,),(64,143),(64,),(32,64),(32,),(64,134),(64,),(32,64),(32,),(1,32),(1,))

def sha(path):
 h=hashlib.sha256();
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--checkpoint",type=Path,required=True);ap.add_argument("--model-out",type=Path,required=True);ap.add_argument("--fixture-out",type=Path,required=True);ap.add_argument("--meta-out",type=Path,required=True);a=ap.parse_args()
 ck=torch.load(a.checkpoint,map_location="cpu",weights_only=False)
 if ck.get("seed")!=3301 or ck.get("architecture")!="conditioned_moment_set_direct_nre_v2_exact_topology":raise ValueError("only primary frozen seed3301 checkpoint may be exported")
 m=ConditionedMomentSetDirectNRE(int(ck["candidate_dim"]),int(ck["block_context_dim"]),int(ck["hidden"]));m.load_state_dict(ck["model_state"]);m.eval();sd=m.state_dict()
 a.model_out.parent.mkdir(parents=True,exist_ok=True)
 with a.model_out.open("wb") as f:
  f.write(MAGIC);f.write(struct.pack("<6I",1,5,6,32,len(ORDER),3301))
  for name,shape in zip(ORDER,EXPECTED_SHAPES):
   x=sd[name].detach().cpu().numpy().astype("<f4",copy=False)
   if x.shape!=shape:raise ValueError(f"{name}: shape {x.shape} != {shape}")
   f.write(struct.pack("<I",x.ndim));f.write(struct.pack("<"+"I"*x.ndim,*x.shape));f.write(x.tobytes(order="C"))
 # Deterministic arithmetic fixture; actual measured-domain fixture is generated separately after materialization.
 rng=np.random.default_rng(2026082902);B=17;M=8
 obs=rng.normal(size=(1,B,10)).astype(np.float32);pred=rng.normal(size=(1,B,M,10)).astype(np.float32);ctx=rng.normal(size=(1,B,6)).astype(np.float32);cand=rng.normal(size=(1,5)).astype(np.float32);bm=np.ones((1,B),dtype=np.bool_);mm=np.ones((1,M),dtype=np.bool_)
 with torch.no_grad():expected=float(m(torch.from_numpy(obs),torch.from_numpy(pred),torch.from_numpy(ctx),torch.from_numpy(cand),torch.from_numpy(bm),torch.from_numpy(mm))[0])
 with a.fixture_out.open("wb") as f:
  f.write(FIXMAGIC);f.write(struct.pack("<2I",B,M));f.write(obs.tobytes());f.write(pred.tobytes());f.write(ctx.tobytes());f.write(cand.tobytes());f.write(struct.pack("<f",expected))
 meta={"contract":"PF_SNRE_RUNTIME_EXPORT_V1","checkpoint_sha256":sha(a.checkpoint),"model_sha256":sha(a.model_out),"fixture_sha256":sha(a.fixture_out),"expected_fixture_logit":expected,"architecture":"conditioned_moment_set_direct_nre_v2_exact_topology","seed":3301,"binary_format_version":1,"tensor_order":list(ORDER)}
 a.meta_out.write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8");print("PF_SNRE_RUNTIME_EXPORT_PASS "+json.dumps(meta,sort_keys=True))
if __name__=="__main__":main()
