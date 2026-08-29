#!/usr/bin/env python3
"""Single terminal offline qualification gate for PF-SNRE.

Consumes exactly three source-sweep, three historical, and three calibration
summaries. It does not tune thresholds and emits either
PF_SNRE_LOHO_OFFLINE_QUALIFIED or PF_SNRE_FINAL_OFFLINE_NO_GO.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np

HOUSES=("H01","H02","H03")


def load(path,contract):
    x=json.loads(Path(path).read_text(encoding="utf-8"))
    allowed=(contract,) if isinstance(contract,str) else tuple(contract)
    if x.get("contract") not in allowed:
        raise ValueError(f"{path}: expected one of {allowed}, got {x.get('contract')}")
    return x

def weighted_mean(items,key):
    n=sum(int(x["cases"]) for x in items);return sum(int(x["cases"])*float(x[key]) for x in items)/n

def pooled_case_column(paths,name):
    vals=[]
    for p in paths:
        c=Path(p).parent/("source_sweep_cases.csv" if "source_sweep" in Path(p).name else "calibration_cases.csv")
        with c.open(newline="",encoding="utf-8-sig") as f:vals.extend(float(r[name]) for r in csv.DictReader(f))
    return np.asarray(vals,dtype=np.float64)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source-sweeps",nargs=3,type=Path,required=True);ap.add_argument("--historical",nargs=3,type=Path,required=True);ap.add_argument("--calibration",nargs=3,type=Path,required=True);ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    sw=[load(p,"PF_SNRE_RESERVED_SOURCE_SWEEP_V2") for p in a.source_sweeps]
    hi=[load(p,("PF_SNRE_HISTORICAL_LOHO_V2",)) for p in a.historical]
    ca=[load(p,"PF_SNRE_Q0_CALIBRATION_V1") for p in a.calibration]
    for group in (sw,hi,ca):
        if {x["house"] for x in group}!=set(HOUSES):raise ValueError("every panel must contain exactly H01,H02,H03")
    sw={x["house"]:x for x in sw};hi={x["house"]:x for x in hi};ca={x["house"]:x for x in ca}
    swl=[sw[h] for h in HOUSES];hil=[hi[h] for h in HOUSES]
    pf=weighted_mean(swl,"mean_pf_error_m");q0=weighted_mean(swl,"mean_q0_error_m");comp=weighted_mean(swl,"mean_nonlearned_physics_error_m");nop=weighted_mean(swl,"mean_no_physics_error_m")
    improve_q0=(q0-pf)/q0;improve_comp=(comp-pf)/comp
    c1=improve_q0>=.20 and improve_comp>=.10
    c2=all(float(sw[h]["relative_improvement_vs_q0"])>=.10 for h in HOUSES)
    hpf=weighted_mean(hil,"mean_pf_error_m");hpmfs=weighted_mean(hil,"mean_pmfs_error_m");himprove=(hpmfs-hpf)/hpmfs
    c3=himprove>=.10 and all(float(hi[h]["relative_improvement_vs_pmfs"])>=-.05 for h in HOUSES)
    rank=pooled_case_column(a.source_sweeps,"normalized_density_rank");pooled_median=float(np.median(rank))
    if all("null_statistics" in sw[h]["source_label_permutation_test"] for h in HOUSES):
        obs=sum(sw[h]["cases"]*sw[h]["source_label_permutation_test"]["observed"] for h in HOUSES)/sum(sw[h]["cases"] for h in HOUSES)
        null=np.average(np.stack([sw[h]["source_label_permutation_test"]["null_statistics"] for h in HOUSES]),axis=0,weights=[sw[h]["cases"] for h in HOUSES])
        perm_p=float((1+np.sum(null<=obs))/(len(null)+1))
    else:
        obs=float("nan");perm_p=1.0
    c4=pooled_median<=.25 and all(float(sw[h]["median_normalized_density_rank"])<=.35 for h in HOUSES) and perm_p<.01
    cal_cases=sum(int(ca[h]["overall"]["cases"]) for h in HOUSES);coverage90=sum(int(ca[h]["overall"]["cases"])*float(ca[h]["overall"]["coverage90"]) for h in HOUSES)/cal_cases
    false_count=sum(int(ca[h]["overall"]["false_confident_count"]) for h in HOUSES);false_fraction=false_count/cal_cases
    c5=coverage90>=.80 and false_fraction<=.01
    pf_gain=q0-pf;no_gain=q0-nop;c6=pf_gain>0 and no_gain<=.5*pf_gain
    gates={"1_multisource_spatial_value":c1,"2_no_house_source_sweep_collapse":c2,"3_historical_cross_house_value":c3,"4_evidence_identifiability":c4,"5_calibration_safety":c5,"6_physics_dependence":c6}
    qualified=all(gates.values());status="PF_SNRE_LOHO_OFFLINE_QUALIFIED" if qualified else "PF_SNRE_FINAL_OFFLINE_NO_GO"
    result={"contract":"PF_SNRE_OFFLINE_GATE_V2","status":status,"gates":gates,"metrics":{"source_sweep_pooled":{"pf_error_m":pf,"q0_error_m":q0,"nonlearned_error_m":comp,"no_physics_error_m":nop,"improvement_vs_q0":improve_q0,"improvement_vs_nonlearned":improve_comp,"no_physics_gain_fraction_of_full":no_gain/pf_gain if pf_gain!=0 else None},"historical_pooled":{"pf_error_m":hpf,"pmfs_error_m":hpmfs,"improvement_vs_pmfs":himprove,"primary_metric":"native_PMFS_ExpectedValue_sourceProbability_0.05_top_cell_fraction","native_update_alignment":"authoritative archive update IDs required"},"identifiability":{"pooled_median_normalized_density_rank":pooled_median,"permutation_observed_mean_rank":obs,"pooled_permutation_p_one_sided":perm_p},"calibration":{"coverage90":coverage90,"false_confident_count":false_count,"cases":cal_cases,"false_confident_fraction":false_fraction}},"thresholds":{"source_sweep_vs_q0":.20,"source_sweep_vs_nonlearned":.10,"each_house_vs_q0":.10,"historical_vs_pmfs":.10,"house_max_degradation":.05,"pooled_median_normalized_rank":.25,"house_median_normalized_rank":.35,"permutation_p":.01,"coverage90":.80,"false_confident_fraction":.01,"max_no_physics_gain_fraction":.5}}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(status+" "+json.dumps(result["metrics"],sort_keys=True))
if __name__=="__main__":main()
