#!/usr/bin/env python3
"""Isolate the two OPEN House02 domains from the frozen E2 tensors."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
E2=ROOT/"evidence/jtd_e2_20260925"
OUT=ROOT/"evidence/solicm_v0/g0"
UP=ROOT/"research/solicm_v0/vendor/LCA/TSClassif"

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def table(path):
    with open(path,encoding="utf-8",newline="") as f:return list(csv.DictReader(f,delimiter="\t"))

def write(path,obj):
    path.write_bytes((json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n").encode())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    initial=json.loads((E2/"JTD_E2_INITIAL_LOCK.json").read_text())
    groups={e:sorted([g for g in initial["source_groups"] if g["environment_index"]==e],key=lambda g:g["source_index"]) for e in (1,2)}
    assert len(groups[1])==len(groups[2])==6
    assert [(g["source_index"],g["source_id"],g["source_xyz"]) for g in groups[1]]==[(g["source_index"],g["source_id"],g["source_xyz"]) for g in groups[2]]
    assert initial["probe_contract_sha256"]=="364c7a2f0333c95845cfb7a10dbb96ee8c5f30a47282e508e3961d4eec575812"
    ref=E2/"JTD_E2_REFERENCE_12x10x30.npy";target=E2/"JTD_E2_FRESH_TARGET_10x30.npy"
    assert sha(ref)=="dc990f9b20381e5a3014af6578a24815a7e5f4178f87624917a7cfbefdad78c7"
    assert sha(target)=="98d38da69cd97f152baf96290999fb6f2a3751dcf24f5c48ab2519a8f3c4bc07"
    a=np.load(ref,mmap_mode="r",allow_pickle=False);b=np.load(target,mmap_mode="r",allow_pickle=False)
    assert a.shape==(3,6,12,10,30) and b.shape==(3,6,4,10,30)
    # Only materialize environment indices 1 and 2. Index 0 (House01 OPEN) is never copied.
    bank=np.concatenate([np.asarray(a[[1,2]]),np.asarray(b[[1,2]])],axis=2)
    assert bank.shape==(2,6,16,10,30) and bank.dtype==np.float32 and np.isfinite(bank).all()
    ref_manifest=table(E2/"JTD_E2_REFERENCE_12_MANIFEST.tsv")
    target_manifest=table(E2/"JTD_E2_FRESH_TARGET_MANIFEST.tsv")
    for e,wind in ((1,"3,5-1_slow"),(2,"4,5-3_slow")):
        r=[v for v in ref_manifest if int(v["environment_index"])==e]
        t=[v for v in target_manifest if int(v["environment_index"])==e]
        assert len(r)==72 and len(t)==24
        for source in range(6):
            sid=groups[e][source]["source_id"]
            rr=[v for v in r if int(v["source_index"])==source]
            tt=[v for v in t if int(v["source_index"])==source]
            assert len(rr)==12 and len(tt)==4
            assert sorted(int(v["reference_index"]) for v in rr)==list(range(12))
            assert sorted(int(v["new_index"]) for v in tt)==list(range(4))
            assert all(v["house"]=="House02" and v["wind"]==wind and v["source_id"]==sid for v in rr+tt)
    bankfile=OUT/"SOLICM_G0_H02_W0_W2_16x10x30.npy"
    if bankfile.exists():
        assert np.array_equal(np.load(bankfile),bank)
    else:np.save(bankfile,bank,allow_pickle=False)
    files=sorted(UP.rglob("*.py"))
    manifest={p.relative_to(UP).as_posix():sha(p) for p in files}
    write(OUT/"SOLICM_G0_UPSTREAM_CODE_MANIFEST.json",{"repository":"DMIRLAB-Group/LCA",
          "commit":"45c091fca909ac13675c6ddac7e0464f0a186355","tracked_python_files":manifest})
    write(OUT/"SOLICM_G0_DATA_AUDIT.json",{"decision":"SOLICM_G0_DATA_READY","house":"House02",
          "domains":["3,5-1_slow","4,5-3_slow"],"source_ids":[g["source_id"] for g in groups[1]],
          "source_xyz":[g["source_xyz"] for g in groups[1]],"tensor_shape":list(bank.shape),
          "reference_indices":list(range(12)),"former_target_indices":list(range(12,16)),
          "all_16_reps_are_open_historical_data":True,"target_label_used_for_training":False,
          "probe_contract_sha256":initial["probe_contract_sha256"],"time_indices":initial["simulation_parameters"]["extract_times"],
          "input_source_sha256":{"reference":sha(ref),"former_target":sha(target)},
          "isolated_bank_sha256":sha(bankfile),"new_plume":0,"sealed_data_read":False})
    print("SOLICM_DATA_READY",sha(bankfile))

if __name__=="__main__":main()
