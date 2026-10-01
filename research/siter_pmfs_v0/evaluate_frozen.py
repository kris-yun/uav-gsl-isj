"""Once-only outer test after all three LOHO models have been frozen."""
import argparse
import csv
import json
import subprocess
from pathlib import Path

import numpy as np

from fit_loho import transform, truth_owner
from prepare_features import read_csv, sha, write_json


def tsv(path, records):
    assert records
    with Path(path).open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]),delimiter="\t",lineterminator="\n")
        writer.writeheader();writer.writerows(records)


def rank_and_margin(score, truth):
    wrong=np.delete(score,truth)
    ahead=int(np.sum(wrong>score[truth]));ties=int(np.sum(wrong==score[truth]))
    return {"truth_midrank":1+ahead+0.5*ties,"truth_pessimistic_rank":1+ahead+ties,
            "truth_ties":ties,"truth_log_score":float(score[truth]),"truth_margin":float(score[truth]-wrong.max())}


def endpoint(binary, csv_path, metadata, truth):
    keys=("width","height","cell_size","origin_x","origin_y")
    return json.loads(subprocess.check_output([str(binary),str(csv_path)]+[str(metadata[k]) for k in keys]+[str(v) for v in truth],text=True))


def validate_endpoint(root,binary):
    records=[]
    for h in ("House01","House02","House03"):
        for seed in (0,1):
            p=root/"native"/f"{h}_seed{seed}_off_off"
            saved=json.loads((p/"tnqc_fixed_trajectory_evaluation.json").read_text())
            for arm,filename in (("native_exported","native_exported.csv"),("tnqc_fused","tnqc_fused.csv"),("tnqc_only","tnqc_only.csv")):
                result=endpoint(binary,p/"tnqc_endpoint_posteriors"/filename,saved["endpoint_evaluator"]["grid_metadata"],saved["truth"])
                differences={k:abs(result[k]-saved[arm][k]) for k in ("pmfs_top5_x","pmfs_top5_y","pmfs_top5_error_m")}
                assert max(differences.values())<=1e-10,(h,seed,arm,differences)
                records.append({"case":f"{h}_seed{seed}","arm":arm,"input_sha256":sha(p/"tnqc_endpoint_posteriors"/filename),"max_abs_difference":max(differences.values())})
    return {"pass":True,"tolerance":1e-10,"validation_count":len(records),"records":records,"binary_sha256":sha(binary)}


def posterior_csv(path, indices,ij,xy,probability):
    with path.open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["cell_index","grid_i","grid_j","x","y","source_probability"])
        for pos in np.lexsort((ij[:,0],ij[:,1])):
            w.writerow([int(indices[pos]),int(ij[pos,0]),int(ij[pos,1]),xy[pos,0],xy[pos,1],probability[pos]])


def decision(cases):
    rank_improvement=np.array([c["rank_improvement"] for c in cases])
    endpoint_improvement=np.array([c["endpoint_improvement_m"] for c in cases])
    baseline_mean=float(np.mean([c["native_error_m"] for c in cases]))
    method_mean=float(np.mean([c["full_error_m"] for c in cases]))
    rank_gate={"rank_improves_4_of_6":int(np.sum(rank_improvement>0))>=4,
               "median_rank_improvement_positive":float(np.median(rank_improvement))>0,
               "no_rank_worsens_over_10":bool(np.all(rank_improvement>=-10))}
    endpoint_gate={"endpoint_improves_4_of_6":int(np.sum(endpoint_improvement>0))>=4,
                   "mean_endpoint_improvement_5_percent":(baseline_mean-method_mean)/baseline_mean>=0.05}
    safety={"no_new_false_confident_collapse":not any(c["new_false_confident_collapse"] for c in cases),
            "every_house_improving_seed":all(any(c["house"]==h and c["rank_improvement"]>0 and c["endpoint_improvement_m"]>0 for c in cases) for h in ("House01","House02","House03"))}
    rp=all(rank_gate.values());ep=all(endpoint_gate.values())
    if rp and ep and all(safety.values()): label="SITER_V0_CROSS_HOUSE_SIGNAL"
    elif rp and not ep: label="SITER_V0_HOLD_RANK_ONLY"
    elif ep and not(rp and all(safety.values())): label="SITER_V0_HOLD_NONTRANSFERABLE"
    else: label="SITER_V0_NO_GO_STOP"
    return {"decision":label,"rank_gates":rank_gate,"endpoint_gates":endpoint_gate,"safety_gates":safety,
            "rank_improving_runs":int(np.sum(rank_improvement>0)),"median_rank_improvement":float(np.median(rank_improvement)),
            "endpoint_improving_runs":int(np.sum(endpoint_improvement>0)),"mean_native_error_m":baseline_mean,
            "mean_full_error_m":method_mean,"mean_endpoint_improvement_fraction":(baseline_mean-method_mean)/baseline_mean}


def evaluate(root,out,binary_dir):
    model_path=out/"FROZEN_LOHO_MODELS.json"
    models=json.loads(model_path.read_text());assert models["all_outer_models_frozen"] and not models["outer_evaluation_executed"]
    assert models["feature_data_sha256"]==sha(out/"SOURCE_BLIND_FEATURE_DATA.npz")
    data=np.load(out/"SOURCE_BLIND_FEATURE_DATA.npz",allow_pickle=False)
    updates=json.loads((out/"SOURCE_BLIND_UPDATES.json").read_text())
    validation=validate_endpoint(root,binary_dir/"tnqc_expected_value_native")
    write_json(out/"NATIVE_ENDPOINT_RECOVERY_PARITY.json",validation)
    cases=[];ablations=[];candidates=[];posteriors={}
    postdir=out/"terminal_posteriors";postdir.mkdir(exist_ok=True)
    for case in sorted(set(d["case"] for d in updates)):
        d=max((d for d in updates if d["case"]==case),key=lambda d:d["update"])
        key=d["key"];h=d["house"]
        run=root/"native"/f"{case}_off_off"
        saved=json.loads((run/"tnqc_fixed_trajectory_evaluation.json").read_text())
        truth=saved["truth"];true=truth_owner(data,d,truth)
        owner=data[f"{key}__owner"];scores=data[f"{key}__scores"]
        fold=models["folds"][h];assert h not in fold["training_houses"]
        measurements={}
        for arm in ("native","general","flow","full","signed"):
            if arm=="native":
                penalty=np.zeros(len(scores));probability=data[f"{key}__native_posterior"]
                path=run/"tnqc_endpoint_posteriors/native_exported.csv"
            else:
                model=fold["models"][arm]
                x=transform(data[f"{key}__X"],np.array(model["lo"]),np.array(model["hi"]))
                beta=np.array(model["beta"]);penalty=x@beta
                if arm!="signed":
                    assert beta.min()>=-1e-10 and abs(beta.sum()-1)<=1e-8
                    assert penalty.min()>=-1e-10 and penalty.max()<=1+1e-8
                cell_score=(scores-penalty)[owner]
                probability=np.exp(cell_score-cell_score.max());probability/=probability.sum()
                path=postdir/f"{case}_{arm}.csv"
                posterior_csv(path,data[f"{key}__idx"],data[f"{key}__ij"],data[f"{key}__xy"],probability)
            e=endpoint(binary_dir/"native_endpoint_with_variance",path,saved["endpoint_evaluator"]["grid_metadata"],truth)
            r=rank_and_margin(scores-penalty,true)
            nz=probability>0
            m={"case":case,"house":h,"seed":d["seed"],"arm":arm,"truth_owner":d["candidate_ids"][true],"active_leaves":len(scores),
               **r,"top5_x":e["pmfs_top5_x"],"top5_y":e["pmfs_top5_y"],"error_m":e["pmfs_top5_error_m"],"variance_m2":e["variance_m2"],
               "entropy_nats":float(-np.dot(probability[nz],np.log(probability[nz]))),"false_confident_collapse":e["variance_m2"]<1 and e["pmfs_top5_error_m"]>2,
               "geometric_success_0p5m":e["pmfs_top5_error_m"]<=0.5,"truth_penalty":float(penalty[true])}
            ablations.append(m);measurements[arm]=m;posteriors[f"{case}__{arm}"]=probability
            for k,cid in enumerate(d["candidate_ids"]):
                candidates.append({"case":case,"house":h,"seed":d["seed"],"update":d["update"],"arm":arm,"candidate_id":cid,"is_truth_owner":k==true,
                                   "native_log_score":float(scores[k]),"contradiction_energy":float(penalty[k]),"corrected_log_score":float(scores[k]-penalty[k]),
                                   "free_cell_measure":int(np.sum(owner==k))})
        n=measurements["native"];m=measurements["full"]
        cases.append({"case":case,"house":h,"seed":d["seed"],"terminal_time_s":float(d["timing"]["sim_time"]),"truth_x":truth[0],"truth_y":truth[1],"truth_owner":m["truth_owner"],"active_leaves":len(scores),
                      "native_rank":n["truth_midrank"],"full_rank":m["truth_midrank"],"rank_improvement":n["truth_midrank"]-m["truth_midrank"],
                      "native_margin":n["truth_margin"],"full_margin":m["truth_margin"],"margin_improvement":m["truth_margin"]-n["truth_margin"],
                      "native_error_m":n["error_m"],"full_error_m":m["error_m"],"endpoint_improvement_m":n["error_m"]-m["error_m"],
                      "native_false_confident_collapse":n["false_confident_collapse"],"full_false_confident_collapse":m["false_confident_collapse"],
                      "new_false_confident_collapse":m["false_confident_collapse"] and not n["false_confident_collapse"]})
    tsv(out/"SITER_V0_CANDIDATES.tsv",candidates);tsv(out/"SITER_V0_CASES.tsv",cases);tsv(out/"SITER_V0_ABLATIONS.tsv",ablations)
    np.savez_compressed(out/"TERMINAL_POSTERIORS.npz",**posteriors)
    result={**decision(cases),"cases":cases,"ablations":ablations,"frozen_models_sha256":sha(model_path),
            "endpoint_parity_pass":validation["pass"],"all_models_frozen_before_outer_evaluation":True,"no_new_plume_forward_or_closed_loop":True,
            "scope":"previously OPEN historical six trajectories; development LOHO, not untouched confirmation"}
    write_json(out/"SITER_V0_RESULT.json",result)
    print(json.dumps({k:result[k] for k in ("decision","rank_improving_runs","median_rank_improvement","endpoint_improving_runs","mean_native_error_m","mean_full_error_m")},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--binary-dir",type=Path,required=True)
    a=p.parse_args();evaluate(a.root,a.out,a.binary_dir)
