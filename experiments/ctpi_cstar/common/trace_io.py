from __future__ import annotations

from dataclasses import dataclass
import csv, json, math, bisect
from pathlib import Path
from typing import Iterable

TIME_ALIASES = ("sim_time","time_s","time","t","elapsed_s","stamp_s","timestamp_s","stamp")
GAS_ALIASES = ("measured_ppm","gas_ppm","ppm","concentration_ppm","concentration","gas","value")
X_ALIASES = ("pose_x","position_x","x","robot_x")
Y_ALIASES = ("pose_y","position_y","y","robot_y")
U_ALIASES = ("wind_u","u_mps","u","wind_x","vx")
V_ALIASES = ("wind_v","v_mps","v","wind_y","vy")
MEASURE_ALIASES = ("in_measurement_block","measuring","is_measuring","measurement")
TIME_TOL = 1.0e-9


@dataclass(frozen=True)
class EpisodeSpec:
    episode_id: str
    house: str
    source_xy: tuple[float,float]
    sensor_trace: Path
    pose_trace: Path
    wind_trace: Path
    arm: str = ""
    seed: int = -1


@dataclass
class Episode:
    spec: EpisodeSpec
    time: list[float]
    gas: list[float]
    gas_ema_aux: list[float]
    wind_u: list[float]
    wind_v: list[float]
    pose_x: list[float]
    pose_y: list[float]
    measuring: list[float]
    sensor_aux_kind: str


def _pick(header: Iterable[str], aliases: tuple[str,...], kind: str, required=True):
    lower = {h.strip().lower():h for h in header if h is not None}
    for a in aliases:
        if a in lower:
            return lower[a]
    if required:
        raise ValueError(f"CSTAR_TRACE_MISSING_{kind}: header={sorted(lower)}")
    return None


def _read_rows(path: Path, value_aliases: dict[str,tuple[str,...]], optional=()):
    """Read a trace without silently repairing malformed temporal evidence.

    Formal causal replay must not sort out-of-order rows, keep the last duplicate,
    or silently skip malformed/non-finite records. Those operations can change
    the causal history. We therefore reject such traces explicitly.
    """
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSTAR_TRACE_EMPTY_HEADER:{path}")
        cols = {"time": _pick(reader.fieldnames, TIME_ALIASES, "TIME")}
        for key,aliases in value_aliases.items():
            cols[key] = _pick(reader.fieldnames, aliases, key.upper(), required=key not in optional)
        out=[]
        last_t=None
        for line_no,row in enumerate(reader,start=2):
            try:
                t=float(row[cols["time"]])
                values={}
                for key,col in cols.items():
                    if key=="time":
                        continue
                    if col is None:
                        values[key]=None
                    else:
                        values[key]=float(row[col])
            except (KeyError,TypeError,ValueError) as exc:
                raise ValueError(f"CSTAR_TRACE_BAD_ROW:{path}:{line_no}") from exc
            if not math.isfinite(t):
                raise ValueError(f"CSTAR_TRACE_NONFINITE_TIME:{path}:{line_no}")
            if any(v is not None and not math.isfinite(v) for v in values.values()):
                raise ValueError(f"CSTAR_TRACE_NONFINITE_VALUE:{path}:{line_no}")
            if last_t is not None:
                if abs(t-last_t) <= TIME_TOL:
                    raise ValueError(f"CSTAR_TRACE_DUPLICATE_TIME:{path}:{line_no}:{t}")
                if t < last_t:
                    raise ValueError(f"CSTAR_TRACE_OUT_OF_ORDER:{path}:{line_no}:{t}:{last_t}")
            out.append((t,values))
            last_t=t
    if not out:
        raise ValueError(f"CSTAR_TRACE_NO_VALID_ROWS:{path}")
    return out


def _latest(rows, t: float):
    ts=[r[0] for r in rows]
    i=bisect.bisect_right(ts,t)-1
    return None if i<0 else rows[i]


def load_episode(spec: EpisodeSpec, max_context_age_s: float=5.0,
                 sensor_tau_s: float=1.2) -> Episode:
    sensor=_read_rows(
        spec.sensor_trace,{"gas":GAS_ALIASES,"measuring":MEASURE_ALIASES},
        optional=("measuring",)
    )
    pose=_read_rows(spec.pose_trace,{"x":X_ALIASES,"y":Y_ALIASES})
    wind=_read_rows(spec.wind_trace,{"u":U_ALIASES,"v":V_ALIASES})
    T=[];G=[];GA=[];U=[];V=[];X=[];Y=[];M=[]
    state=0.0; prev_t=None
    for t,sv in sensor:
        p=_latest(pose,t); w=_latest(wind,t)
        if p is None:
            raise ValueError(f"CSTAR_TRACE_POSE_CONTEXT_MISSING:{spec.episode_id}:{t}")
        if w is None:
            raise ValueError(f"CSTAR_TRACE_WIND_CONTEXT_MISSING:{spec.episode_id}:{t}")
        if t-p[0] > max_context_age_s:
            raise ValueError(f"CSTAR_TRACE_POSE_CONTEXT_STALE:{spec.episode_id}:{t-p[0]}")
        if t-w[0] > max_context_age_s:
            raise ValueError(f"CSTAR_TRACE_WIND_CONTEXT_STALE:{spec.episode_id}:{t-w[0]}")
        gas=max(0.0,float(sv["gas"]))
        dt=0.2 if prev_t is None else t-prev_t
        if dt <= 0.0:
            raise ValueError(f"CSTAR_TRACE_SENSOR_DT_NONPOSITIVE:{spec.episode_id}:{dt}")
        alpha=math.exp(-dt/sensor_tau_s)
        state=alpha*state+(1-alpha)*gas
        prev_t=t
        T.append(t);G.append(gas);GA.append(state)
        X.append(float(p[1]["x"]));Y.append(float(p[1]["y"]))
        U.append(float(w[1]["u"]));V.append(float(w[1]["v"]))
        M.append(float(sv["measuring"]) if sv.get("measuring") is not None else 1.0)
    if len(T)<4:
        raise ValueError(f"CSTAR_EPISODE_TOO_SHORT:{spec.episode_id}:{len(T)}")
    t0=T[0]
    T=[t-t0 for t in T]
    return Episode(
        spec,T,G,GA,U,V,X,Y,M,
        sensor_aux_kind=f"gas_ema_from_measured_ppm_tau_{sensor_tau_s:g}s_not_fopdt_state",
    )


def load_manifest(path: Path) -> list[EpisodeSpec]:
    data=json.loads(path.read_text(encoding="utf-8"))
    rows=data["episodes"] if isinstance(data,dict) else data
    base=path.parent
    out=[]
    for row in rows:
        sx,sy=map(float,row["source_xy"])
        def p(name):
            q=Path(row[name]); return q if q.is_absolute() else base/q
        out.append(EpisodeSpec(
            str(row["episode_id"]),str(row.get("house","")),(sx,sy),
            p("sensor_trace"),p("pose_trace"),p("wind_trace"),
            str(row.get("arm","")),int(row.get("seed",-1))
        ))
    return out


def discover_seed12_run_root(run_root: Path) -> dict:
    gt={"H01":(-0.40,-2.90),"H02":(0.0,-1.0),"H03":(-0.45,1.90)}
    eps=[]; missing=[]
    for house,source in gt.items():
        for arm in ("A0","F00","F01"):
            d=run_root/f"{house}_seed12_{arm}"
            paths={k:d/f for k,f in {
                "sensor_trace":"sensor_trace.csv",
                "pose_trace":"sim_pose_trace.csv",
                "wind_trace":"wind_trace.csv",
            }.items()}
            if all(p.is_file() for p in paths.values()):
                eps.append({
                    "episode_id":f"{house}_seed12_{arm}","house":house,
                    "source_xy":list(source),"arm":arm,"seed":12,
                    **{k:str(v) for k,v in paths.items()},
                })
            else:
                missing.append(str(d))
    return {
        "contract":"CSTAR_SPENT_EPISODE_MANIFEST_V1",
        "episodes":eps,"missing_run_dirs":missing,
        "trace_ingestion":"strict_no_sort_no_dedup_no_silent_bad_row_skip",
        "sensor_aux_semantics":"derived gas EMA only; not an audited FOPDT sensor state",
    }
