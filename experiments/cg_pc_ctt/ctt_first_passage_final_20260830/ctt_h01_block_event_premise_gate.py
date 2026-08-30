#!/usr/bin/env python3
"""H01 offline causal block-event premise gate for the final CTT temporal representation.

Purpose
-------
This is a *model-premise* test on the existing H01 predictive8 native physical
concentration bank.  It does not use historical H01 source truth, localization
error, PMFS posterior, planner outcomes, or any learned source classifier.

For each held-out transport member, the other seven members define candidate-
conditioned event models after the frozen run-persistent sensor operator and the
native 10-sample / 0.1 ppm completed-block HIT rule.  Each full physical stop
contributes exactly eight completed blocks; extra stationary samples are not
invented as a ninth block, but they remain in the persistent sensor trajectory.

The reference implements the discrete factorisation used to decide whether it
is scientifically justified to proceed to the neural first-passage M1:
  A1: independent time-varying Bernoulli field, conditioned on hit count;
  A2: first-order Markov phase association, conditioned on the same hit count;
  A3: A2 conditional order + exact Markov count/survival = full Markov sequence.

Mandatory controls preserve the hit count and destroy only event order, or
preserve count evidence while destroying candidate/temporal association.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.special import logsumexp
from scipy.stats import binomtest

MAGIC = b"PFV3STR1"
UINT32 = struct.Struct("<I")
DT_S = 0.2
BLOCK_SAMPLES = 10
BLOCKS_PER_STOP = 8
STATIONARY_SAMPLES_PER_COMPLETE_STOP = BLOCK_SAMPLES * BLOCKS_PER_STOP
THRESHOLD_GAS_PPM = 0.1
JEFFREYS = 0.5
TEST_SOURCE_COUNT = 32

SENSOR = {
    "tau_s": 1.2,
    "dead_time_s": 0.4,
    "initial": 0.0,
}

ALL_SEQ = np.asarray(
    [[(code >> (BLOCKS_PER_STOP - 1 - i)) & 1 for i in range(BLOCKS_PER_STOP)]
     for code in range(2 ** BLOCKS_PER_STOP)],
    dtype=np.int8,
)
SEQ_COUNT = ALL_SEQ.sum(axis=1).astype(np.int8)
SEQ_INDEX = {tuple(row.tolist()): i for i, row in enumerate(ALL_SEQ)}
LOG_COMB = np.asarray(
    [math.log(math.comb(BLOCKS_PER_STOP, m)) for m in range(BLOCKS_PER_STOP + 1)],
    dtype=np.float64,
)


def read_multistream(path: Path) -> list[np.ndarray]:
    raw = path.read_bytes()
    if raw[: len(MAGIC)] != MAGIC:
        raise ValueError(f"bad stream magic: {path}")
    off = len(MAGIC)
    (count,) = UINT32.unpack_from(raw, off); off += UINT32.size
    lengths = struct.unpack_from(f"<{count}I", raw, off); off += count * UINT32.size
    flat = np.frombuffer(raw, dtype="<f4", offset=off)
    if flat.size != sum(lengths):
        raise ValueError(f"stream size mismatch: {path}")
    out, start = [], 0
    for n in lengths:
        out.append(flat[start:start+n].copy()); start += n
    return out


def forward_sensor_batch(physical: np.ndarray) -> np.ndarray:
    x = np.asarray(physical, dtype=np.float64)
    if x.ndim != 2 or not np.isfinite(x).all() or (x < 0).any():
        raise ValueError("invalid physical batch")
    delay = int(round(SENSOR["dead_time_s"] / DT_S))
    alpha = math.exp(-DT_S / SENSOR["tau_s"])
    state = np.full(x.shape[0], SENSOR["initial"], dtype=np.float64)
    y = np.empty_like(x)
    for t in range(x.shape[1]):
        target = x[:, t-delay] if t >= delay else SENSOR["initial"]
        state = alpha * state + (1.0 - alpha) * target
        y[:, t] = state
    return y


@dataclass(frozen=True)
class Carrier:
    index: int
    carrier_id: str
    x: float
    y: float


def load_carriers(support: Path) -> list[Carrier]:
    grouped: dict[int, list[dict[str,str]]] = {}
    with support.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["house"] == "H01":
                grouped.setdefault(int(row["carrier_index"]), []).append(row)
    carriers = []
    for idx in sorted(grouped):
        rows = grouped[idx]
        carriers.append(Carrier(
            idx, rows[0]["carrier_id"],
            float(np.mean([float(r["pmfs_x"]) for r in rows])),
            float(np.mean([float(r["pmfs_y"]) for r in rows])),
        ))
    if len(carriers) != 210 or [c.index for c in carriers] != list(range(210)):
        raise ValueError(f"carrier contract mismatch: {len(carriers)}")
    return carriers


def stable_digest(text: str) -> bytes:
    return hashlib.sha256(text.encode("utf-8")).digest()


def select_coverage_carriers(carriers: list[Carrier], count: int = TEST_SOURCE_COUNT) -> list[int]:
    x = np.asarray([c.x for c in carriers]); y = np.asarray([c.y for c in carriers])
    xy = np.column_stack(((x-x.min())/max(float(np.ptp(x)),1e-12),
                          (y-y.min())/max(float(np.ptp(y)),1e-12)))
    tie = [stable_digest(f"CTT-FINAL-EVENT-PREMISE|{c.carrier_id}") for c in carriers]
    selected = [min(range(len(carriers)), key=lambda i: tie[i])]
    remaining = set(range(len(carriers))) - set(selected)
    while len(selected) < count:
        def key(i: int):
            d = min(float(np.sum((xy[i]-xy[j])**2)) for j in selected)
            return (-d, tie[i])
        q = min(remaining, key=key); selected.append(q); remaining.remove(q)
    return selected


def read_full_stop_indices(schedule_path: Path) -> list[np.ndarray]:
    with schedule_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    moving = np.asarray([int(r["is_moving"]) for r in rows], dtype=np.int8)
    stop_id = np.asarray([int(r["stop_id"]) for r in rows], dtype=np.int32)
    stops: list[np.ndarray] = []
    for sid in np.unique(stop_id):
        idx = np.flatnonzero(stop_id == sid)
        local_moving = moving[idx]
        first_move = next((i for i,v in enumerate(local_moving) if v == 1), len(idx))
        if first_move >= STATIONARY_SAMPLES_PER_COMPLETE_STOP:
            stops.append(idx[:STATIONARY_SAMPLES_PER_COMPLETE_STOP])
    if len(stops) < 5:
        raise ValueError(f"too few full stops: {schedule_path} -> {len(stops)}")
    return stops


def load_hit_tapes(bank: Path, carriers: list[Carrier], trajectory: int,
                   stop_indices: list[np.ndarray]) -> np.ndarray:
    # [source, member, full_stop, eight completed PMFS block HIT bits]
    first = read_multistream(bank / "member_00" / f"{carriers[0].carrier_id}.bin")[trajectory]
    T = first.size
    physical = np.empty((len(carriers)*8, T), dtype=np.float32)
    row = 0
    for c in carriers:
        for k in range(8):
            a = read_multistream(bank / f"member_{k:02d}" / f"{c.carrier_id}.bin")[trajectory]
            if a.size != T: raise ValueError("trajectory length mismatch")
            physical[row] = a; row += 1
    measured = forward_sensor_batch(physical).reshape(len(carriers), 8, T)
    tapes = np.empty((len(carriers), 8, len(stop_indices), BLOCKS_PER_STOP), dtype=np.int8)
    for j, idx in enumerate(stop_indices):
        # Only the first 80 stationary samples are consumed as 8 completed blocks.
        block_mean = measured[:,:,idx].reshape(len(carriers),8,BLOCKS_PER_STOP,BLOCK_SAMPLES).mean(axis=3)
        tapes[:,:,j,:] = (block_mean > THRESHOLD_GAS_PPM).astype(np.int8)
    return tapes


def log_markov_sequences(p1: np.ndarray, alpha: np.ndarray, beta: np.ndarray) -> np.ndarray:
    """Return log P(sequence) for all 256 sequences.

    p1/alpha/beta shape [S,J]; output [S,J,256].
    """
    eps = 1e-300
    p1 = np.clip(p1, eps, 1-eps); alpha=np.clip(alpha,eps,1-eps); beta=np.clip(beta,eps,1-eps)
    out = np.empty((*p1.shape, ALL_SEQ.shape[0]), dtype=np.float64)
    for q, seq in enumerate(ALL_SEQ):
        lp = np.where(seq[0] == 1, np.log(p1), np.log1p(-p1))
        for a,b in zip(seq[:-1], seq[1:]):
            if a == 0 and b == 0: lp = lp + np.log1p(-alpha)
            elif a == 0 and b == 1: lp = lp + np.log(alpha)
            elif a == 1 and b == 0: lp = lp + np.log(beta)
            else: lp = lp + np.log1p(-beta)
        out[...,q] = lp
    return out


def markov_model(pred: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    # pred [S,K,J,8].  Jeffreys priors are fixed and not outcome-tuned.
    K = pred.shape[1]
    p1 = (pred[...,0].sum(axis=1) + JEFFREYS) / (K + 2*JEFFREYS)
    left, right = pred[...,:-1], pred[...,1:]
    n00 = ((left==0)&(right==0)).sum(axis=(1,3))
    n01 = ((left==0)&(right==1)).sum(axis=(1,3))
    n10 = ((left==1)&(right==0)).sum(axis=(1,3))
    n11 = ((left==1)&(right==1)).sum(axis=(1,3))
    alpha = (n01 + JEFFREYS)/(n00+n01+2*JEFFREYS)
    beta  = (n10 + JEFFREYS)/(n10+n11+2*JEFFREYS)
    logs = log_markov_sequences(p1, alpha, beta)
    logZ = np.empty((*p1.shape, BLOCKS_PER_STOP+1), dtype=np.float64)
    for m in range(BLOCKS_PER_STOP+1):
        logZ[...,m] = logsumexp(logs[...,SEQ_COUNT==m], axis=-1)
    return logs, logZ


def iid_model(pred: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    # time-varying marginal p_n at each stop from the same seven predictive members.
    K = pred.shape[1]
    p = (pred.sum(axis=1) + JEFFREYS) / (K + 2*JEFFREYS)  # [S,J,8]
    p = np.clip(p,1e-300,1-1e-15)
    logs = np.empty((pred.shape[0],pred.shape[2],ALL_SEQ.shape[0]),dtype=np.float64)
    for q,seq in enumerate(ALL_SEQ):
        logs[...,q] = (seq[None,None,:]*np.log(p) + (1-seq)[None,None,:]*np.log1p(-p)).sum(axis=-1)
    logC = np.empty((pred.shape[0],pred.shape[2],BLOCKS_PER_STOP+1),dtype=np.float64)
    for m in range(BLOCKS_PER_STOP+1):
        logC[...,m]=logsumexp(logs[...,SEQ_COUNT==m],axis=-1)
    return logs,logC


def score_observation(obs: np.ndarray, iid_logs: np.ndarray, iid_logC: np.ndarray,
                      m_logs: np.ndarray, m_logC: np.ndarray) -> dict[str,np.ndarray]:
    S,J,_ = iid_logs.shape
    seq_idx = np.asarray([SEQ_INDEX[tuple(row.tolist())] for row in obs],dtype=np.int64)
    counts = obs.sum(axis=1).astype(np.int64)
    jj = np.arange(J)
    # Candidate x stop values.
    l1 = iid_logs[:,jj,seq_idx]
    c1 = iid_logC[:,jj,counts]
    l2 = m_logs[:,jj,seq_idx]
    c2 = m_logC[:,jj,counts]
    j1=(l1-c1).sum(axis=1)
    j2=(l2-c2).sum(axis=1)
    j3=c2.sum(axis=1)
    a3=l2.sum(axis=1)
    return {"J1":j1,"J2":j2,"J3":j3,"A3":a3}


def permute_tapes(obs: np.ndarray, key: str) -> np.ndarray:
    out=obs.copy()
    for j in range(len(out)):
        seed=int.from_bytes(stable_digest(f"CTT-ORDER-DESTROY|{key}|{j}")[:8],"big")
        rng=np.random.default_rng(seed)
        out[j]=out[j,rng.permutation(BLOCKS_PER_STOP)]
    if not np.array_equal(out.sum(axis=1),obs.sum(axis=1)):
        raise AssertionError("count not preserved")
    return out


def rank_desc(score: np.ndarray, truth: int) -> float:
    target=score[truth]; greater=np.count_nonzero(score>target); equal=np.count_nonzero(score==target)-1
    return float(1+greater+0.5*equal)


def paired_sign(a: np.ndarray,b: np.ndarray) -> dict:
    # lower rank is better; H1 a<b.
    wins=int(np.sum(a<b)); losses=int(np.sum(a>b)); ties=int(np.sum(a==b)); n=wins+losses
    p=float(binomtest(wins,n,0.5,alternative="greater").pvalue) if n else 1.0
    return {"wins":wins,"losses":losses,"ties":ties,"p_greater":p}


def summarize(rows: list[dict], key: str, ncarriers: int) -> dict:
    ranks=np.asarray([r[key] for r in rows],dtype=np.float64)
    nr=(ranks-1)/(ncarriers-1)
    return {"top1":float(np.mean(ranks<=1)),"top5":float(np.mean(ranks<=5)),"top10":float(np.mean(ranks<=10)),
            "median_rank":float(np.median(ranks)),"mean_normalized_rank":float(nr.mean())}


def selftest() -> None:
    rng=np.random.default_rng(1)
    # Exact count factorisation / normalization tests.
    p1=np.asarray([[0.31]]); alpha=np.asarray([[0.22]]); beta=np.asarray([[0.44]])
    logs=log_markov_sequences(p1,alpha,beta)
    z=np.asarray([logsumexp(logs[...,SEQ_COUNT==m],axis=-1)[0,0] for m in range(9)])
    assert abs(float(np.exp(logsumexp(z)))-1.0)<1e-12
    seq=ALL_SEQ[73]; idx=SEQ_INDEX[tuple(seq.tolist())]; m=int(seq.sum())
    j2=logs[0,0,idx]-z[m]; j3=z[m]
    assert abs((j2+j3)-logs[0,0,idx])<1e-12
    # Count-preserving destruction.
    for _ in range(100):
        x=rng.integers(0,2,size=(5,8),dtype=np.int8); y=permute_tapes(x,str(rng.integers(1<<32)))
        assert np.array_equal(x.sum(1),y.sum(1))
    print("CTT_H01_BLOCK_EVENT_PREMISE_SELFTEST PASS")


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--predictive-bank",type=Path,required=True)
    ap.add_argument("--support",type=Path,required=True)
    ap.add_argument("--schedule-root",type=Path,required=True)
    ap.add_argument("--output-root",type=Path,required=True)
    args=ap.parse_args()
    selftest()
    if args.output_root.exists():
        raise SystemExit(f"refuse overwrite: {args.output_root}")
    args.output_root.mkdir(parents=True)
    carriers=load_carriers(args.support); selected=select_coverage_carriers(carriers)
    rows=[]
    for tr in range(5):
        schedule=args.schedule_root/f"trajectory_seed_{4001+tr}.csv"
        stops=read_full_stop_indices(schedule)
        tapes=load_hit_tapes(args.predictive_bank,carriers,tr,stops)
        print(f"trajectory {4001+tr}: full_stops={len(stops)} hit_rate={tapes.mean():.6f}",flush=True)
        for held in range(8):
            keep=[k for k in range(8) if k!=held]
            pred=tapes[:,keep]
            iid_logs,iid_logC=iid_model(pred)
            m_logs,m_logC=markov_model(pred)
            # deterministic candidate-label permutation for temporal conditional term only.
            seed=int.from_bytes(stable_digest(f"CTT-CANDIDATE-TEMP-LABEL|{4001+tr}|{held}")[:8],"big")
            cand_perm=np.random.default_rng(seed).permutation(len(carriers))
            for truth in selected:
                obs=tapes[truth,held]
                sc=score_observation(obs,iid_logs,iid_logC,m_logs,m_logC)
                perm_obs=permute_tapes(obs,f"{4001+tr}|{held}|{carriers[truth].carrier_id}")
                sp=score_observation(perm_obs,iid_logs,iid_logC,m_logs,m_logC)
                # Candidate temporal association destruction: preserve J3 at candidate s,
                # replace J2 by another candidate's J2.
                a3_label=sc["J2"][cand_perm]+sc["J3"]
                rows.append({
                    "trajectory_seed":4001+tr,"heldout_member":held,"true_index":truth,
                    "true_id":carriers[truth].carrier_id,"full_stops":len(stops),
                    "rank_J1":rank_desc(sc["J1"],truth),
                    "rank_J2":rank_desc(sc["J2"],truth),
                    "rank_J3":rank_desc(sc["J3"],truth),
                    "rank_A3":rank_desc(sc["A3"],truth),
                    "rank_A3_time_permute":rank_desc(sp["A3"],truth),
                    "rank_A3_temporal_label_shuffle":rank_desc(a3_label,truth),
                    "truth_J1":float(sc["J1"][truth]),"truth_J2":float(sc["J2"][truth]),
                    "truth_J3":float(sc["J3"][truth]),"truth_A3":float(sc["A3"][truth]),
                })
    expected=5*8*TEST_SOURCE_COUNT
    if len(rows)!=expected: raise SystemExit(f"case count {len(rows)} != {expected}")
    cases=args.output_root/"H01_block_event_premise_cases.csv"
    with cases.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    n=len(carriers)
    summary={k:summarize(rows,k,n) for k in ["rank_J1","rank_J2","rank_J3","rank_A3","rank_A3_time_permute","rank_A3_temporal_label_shuffle"]}
    arrays={k:np.asarray([r[k] for r in rows]) for k in summary}
    comparisons={
        "M2_J2_vs_J1":paired_sign(arrays["rank_J2"],arrays["rank_J1"]),
        "FULL_A3_vs_COUNT_J3":paired_sign(arrays["rank_A3"],arrays["rank_J3"]),
        "FULL_A3_vs_TIME_PERMUTE":paired_sign(arrays["rank_A3"],arrays["rank_A3_time_permute"]),
        "FULL_A3_vs_TEMPORAL_LABEL_SHUFFLE":paired_sign(arrays["rank_A3"],arrays["rank_A3_temporal_label_shuffle"]),
        "M3_A3_vs_J2":paired_sign(arrays["rank_A3"],arrays["rank_J2"]),
    }
    # Preregistered premise gate. No result-dependent threshold or blend is allowed.
    gate={
        "m2_phase_increment": summary["rank_J2"]["mean_normalized_rank"] < summary["rank_J1"]["mean_normalized_rank"] and comparisons["M2_J2_vs_J1"]["p_greater"]<=0.01,
        "full_beats_count": summary["rank_A3"]["mean_normalized_rank"] < summary["rank_J3"]["mean_normalized_rank"] and comparisons["FULL_A3_vs_COUNT_J3"]["p_greater"]<=0.01,
        "full_top10_non_degrade_vs_count": summary["rank_A3"]["top10"] >= summary["rank_J3"]["top10"],
        "time_order_load_bearing": summary["rank_A3"]["mean_normalized_rank"] < summary["rank_A3_time_permute"]["mean_normalized_rank"] and comparisons["FULL_A3_vs_TIME_PERMUTE"]["p_greater"]<=0.01,
        "candidate_temporal_association_load_bearing": summary["rank_A3"]["mean_normalized_rank"] < summary["rank_A3_temporal_label_shuffle"]["mean_normalized_rank"] and comparisons["FULL_A3_vs_TEMPORAL_LABEL_SHUFFLE"]["p_greater"]<=0.01,
        "m3_count_survival_increment": summary["rank_A3"]["mean_normalized_rank"] < summary["rank_J2"]["mean_normalized_rank"] and comparisons["M3_A3_vs_J2"]["p_greater"]<=0.01,
    }
    passed=all(gate.values())
    report={
        "contract":"CTT_H01_BLOCK_EVENT_FACTORISATION_PREMISE_V1",
        "scientific_status":"PREDICTIVE8_LEAVE_ONE_TRANSPORT_MEMBER_OUT_MODEL_PREMISE_ONLY",
        "source_truth_used":"synthetic_source_is_generator_input_only",
        "historical_h01_truth_used":False,
        "case_count":len(rows),"carrier_count":n,"coverage_sources":TEST_SOURCE_COUNT,
        "trajectory_seeds":[4001,4002,4003,4004,4005],"transport_members":8,
        "block_samples":BLOCK_SAMPLES,"blocks_per_full_stop":BLOCKS_PER_STOP,
        "threshold_gas_ppm":THRESHOLD_GAS_PPM,"jeffreys_prior":JEFFREYS,
        "summary":summary,"comparisons":comparisons,"gate":gate,
        "verdict":"CTT_H01_EVENT_PREMISE_PASS_PROMOTE_NEURAL_M1" if passed else "CTT_H01_EVENT_PREMISE_NO_GO",
    }
    (args.output_root/"H01_block_event_premise_summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (args.output_root/"VERDICT.txt").write_text(report["verdict"]+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
