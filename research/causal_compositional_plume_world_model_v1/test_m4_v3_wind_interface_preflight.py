#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"research/causal_compositional_plume_world_model_v1/m4_v3_wind_interface_preflight.py"
spec=importlib.util.spec_from_file_location("w0",P)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

x=m.historical_semantic_conflict()
assert x["pmfs_all_aligned"]
assert x["gmrf_subscriber_all_reversed"]
for c in x["cases"]:
    assert c["pmfs_cosine"] > 0.999999
    assert c["gmrf_subscriber_cosine"] < -0.999999

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"pairs.csv"
    p.write_text("in_u,in_v,out_u,out_v\n1,0,0.9,0.01\n0,1,0.01,1.1\n-1,0,-1.0,0.02\n0,-1,-0.01,-0.8\n")
    r=m.audit_observed_pairs(p,0.95,0.5,1.5)
    assert r["pass"]

print("M4_V3_W0_WIND_SEMANTIC_PREFLIGHT_PASS")
