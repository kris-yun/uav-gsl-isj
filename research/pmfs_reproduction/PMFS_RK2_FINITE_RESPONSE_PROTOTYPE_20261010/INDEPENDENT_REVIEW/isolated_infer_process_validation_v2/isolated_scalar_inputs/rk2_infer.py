"""Separate, source-blind RK2 inference interface.

Only candidate reference response arrays and observed scalar gas series enter
infer. This module never imports simulator decoders, producer code, particle
state, per-particle phi, a generating-source map, or any historical bank path.
The directory loaders whitelist the exact scalar-response NPZ fields.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import math
import numpy as np

BLOCKS = 50
THRESHOLD = np.float32(0.1)
TEMPERATURE = 1.0

def _opaque(value, field):
    if not isinstance(value, str) or not value or '\x00' in value:
        raise ValueError(f'{field} must be a nonempty opaque string')
    return value

def _responses(value, ndim, field):
    x = np.array(value, dtype=np.float32, copy=True)
    if x.ndim != ndim or x.shape[-1] != BLOCKS or (ndim==2 and not x.shape[0]):
        raise ValueError(f'{field} requires {"(M,50), M>=1" if ndim==2 else "(50,)"}')
    if not np.isfinite(x).all() or (x < 0).any():
        raise ValueError(f'{field} must be finite nonnegative ppm')
    x.flags.writeable = False
    return x

@dataclass(frozen=True)
class ForecastCandidate:
    candidate_id: str
    reference_response_ppm: np.ndarray
    physical_source_xyz: tuple

    def __post_init__(self):
        object.__setattr__(self, 'candidate_id', _opaque(self.candidate_id, 'candidate_id'))
        object.__setattr__(self, 'reference_response_ppm', _responses(self.reference_response_ppm, 2, 'reference_response_ppm'))
        xyz = tuple(float(v) for v in self.physical_source_xyz)
        if len(xyz) != 3 or not all(math.isfinite(v) for v in xyz):
            raise ValueError('candidate physical_source_xyz must have three finite values')
        object.__setattr__(self, 'physical_source_xyz', xyz)

@dataclass(frozen=True)
class ForecastSet:
    model_id: str
    candidates: tuple

    def __post_init__(self):
        object.__setattr__(self, 'model_id', _opaque(self.model_id, 'model_id'))
        candidates = tuple(self.candidates)
        if not candidates or not all(type(v) is ForecastCandidate for v in candidates):
            raise ValueError('candidates must be ForecastCandidate objects')
        if len({v.candidate_id for v in candidates}) != len(candidates):
            raise ValueError('candidate ids must be unique')
        object.__setattr__(self, 'candidates', candidates)

@dataclass(frozen=True)
class ObservationSeries:
    observation_id: str
    observed_ppm: np.ndarray
    receiver_plan_id: str

    def __post_init__(self):
        object.__setattr__(self, 'observation_id', _opaque(self.observation_id, 'observation_id'))
        object.__setattr__(self, 'receiver_plan_id', _opaque(self.receiver_plan_id, 'receiver_plan_id'))
        object.__setattr__(self, 'observed_ppm', _responses(self.observed_ppm, 1, 'observed_ppm'))

def infer(forecasts: ForecastSet, observed: ObservationSeries):
    """Return predictions/scores without reading or writing any path.

    Mean marginal Bernoulli score is temperature-normalized at 1. The result is
    a composite-score source map, not a calibrated physical joint posterior.
    Every reference realization is thresholded before hit frequency averaging.
    """
    if type(forecasts) is not ForecastSet or type(observed) is not ObservationSeries:
        raise TypeError('infer accepts only ForecastSet and ObservationSeries')
    y = observed.observed_ppm > THRESHOLD
    candidates = []
    for c in forecasts.candidates:
        m = c.reference_response_ppm.shape[0]
        reference_events = c.reference_response_ppm > THRESHOLD
        counts = np.count_nonzero(reference_events, axis=0)
        probability = (counts.astype(np.float64) + 0.5) / (m + 1.0)
        log_terms = [math.log(float(p)) if hit else math.log1p(-float(p)) for hit, p in zip(y, probability)]
        brier_terms = [(int(hit) - float(p))**2 for hit, p in zip(y, probability)]
        candidates.append(dict(candidate_id=c.candidate_id, reference_realizations=m,
            physical_source_xyz=list(c.physical_source_xyz),
            reference_events=reference_events.astype(np.int8).tolist(),
            probability_by_block=probability.tolist(), observed_events=y.astype(np.int8).tolist(),
            mean_Bernoulli_log_score=math.fsum(log_terms)/BLOCKS,
            mean_Brier=math.fsum(brier_terms)/BLOCKS))
    maximum = max(c['mean_Bernoulli_log_score'] for c in candidates)
    exp_scores = [math.exp((c['mean_Bernoulli_log_score'] - maximum)/TEMPERATURE) for c in candidates]
    denominator = math.fsum(exp_scores)
    for c, exp_score in zip(candidates, exp_scores):
        c['source_probability'] = exp_score / denominator
    top1 = sorted(c['candidate_id'] for c in candidates if abs(c['mean_Bernoulli_log_score'] - maximum) <= 1e-15)
    return dict(model_id=forecasts.model_id, observation_id=observed.observation_id,
        receiver_plan_id=observed.receiver_plan_id, blocks=BLOCKS,
        threshold_float32_ppm=float(THRESHOLD), smoothing_alpha=0.5, smoothing_beta=0.5,
        normalization='softmax(mean marginal Bernoulli log score)', temperature=TEMPERATURE,
        probability_scope='Composite-score normalization; not calibrated physical joint posterior',
        top1_candidate_ids=top1, candidates=candidates)

def _read_manifest(directory, allowed):
    directory = Path(directory)
    obj = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    if type(obj) is not dict or set(obj) != set(allowed):
        raise ValueError('manifest contains missing or forbidden fields')
    return directory, obj

def _scalar_response_file(directory, name, allowed_key):
    if not isinstance(name, str) or Path(name).name != name or name in ('', '.', '..'):
        raise ValueError('response file must be a plain file name')
    with np.load(directory / name, allow_pickle=False) as z:
        if set(z.files) != {allowed_key}:
            raise ValueError('NPZ contains missing or forbidden state fields')
        return z[allowed_key].copy()

def load_forecasts(directory):
    """Load response-only candidates from a reference directory."""
    directory, obj = _read_manifest(directory, {'model_id','candidates'})
    if type(obj['candidates']) is not list:
        raise ValueError('candidate manifest must be a list')
    candidates = []
    for c in obj['candidates']:
        if type(c) is not dict or set(c) != {'candidate_id','reference_file','physical_source_xyz'}:
            raise ValueError('candidate manifest contains forbidden fields')
        response = _scalar_response_file(directory, c['reference_file'], 'reference_response_ppm')
        candidates.append(ForecastCandidate(c['candidate_id'], response, tuple(c['physical_source_xyz'])))
    return ForecastSet(obj['model_id'], tuple(candidates))

def load_observation(directory):
    """Load actual scalar gas observations; hidden state files are untouched."""
    directory, obj = _read_manifest(directory, {'observation_id','receiver_plan_id','response_file'})
    response = _scalar_response_file(directory, obj['response_file'], 'observed_ppm')
    return ObservationSeries(obj['observation_id'], response, obj['receiver_plan_id'])

def load_forecast_npz(path, model_id):
    """Load one model's full candidate forecasts; return (ForecastSet, plan_id).

    Candidate IDs are data-only Unicode strings; file names and IDs never
    select different inference logic. No unknown NPZ field is permitted.
    """
    with np.load(Path(path), allow_pickle=False) as z:
        required={'candidate_ids','source_xyz','reference_response_ppm','receiver_plan_id'}
        if set(z.files)!=required:
            raise ValueError('forecast NPZ contains missing or forbidden fields')
        ids=z['candidate_ids'].copy();xyz=z['source_xyz'].copy()
        responses=z['reference_response_ppm'].copy();plan=z['receiver_plan_id'].copy()
    if ids.ndim!=1 or ids.dtype.kind!='U' or not len(ids):
        raise ValueError('candidate_ids must be a nonempty Unicode vector')
    if xyz.shape!=(len(ids),3) or responses.ndim!=3 or responses.shape[0]!=len(ids) or responses.shape[-1]!=BLOCKS:
        raise ValueError('forecast coordinates/responses have inconsistent shapes')
    if plan.shape!=() or plan.dtype.kind!='U':
        raise ValueError('receiver_plan_id must be a Unicode scalar')
    candidates=tuple(ForecastCandidate(str(cid),response,tuple(point)) for cid,response,point in zip(ids,responses,xyz))
    return ForecastSet(model_id,candidates),_opaque(str(plan.item()),'receiver_plan_id')

def load_observation_json(path):
    """Read only the explicitly supplied scalar observation JSON file."""
    obj=json.loads(Path(path).read_text(encoding='utf-8'))
    if type(obj) is not dict or set(obj)!={'observation_id','observed_ppm','receiver_plan_id'}:
        raise ValueError('observation JSON contains missing or forbidden fields')
    return ObservationSeries(obj['observation_id'],obj['observed_ppm'],obj['receiver_plan_id'])

def infer_files(forecast_npz, observation_json, model_id):
    """Explicit file input adapter; does not glob either input directory."""
    forecasts,plan=load_forecast_npz(forecast_npz,model_id)
    observed=load_observation_json(observation_json)
    if plan!=observed.receiver_plan_id:
        raise ValueError('candidate/observation receiver plans do not match')
    return infer(forecasts,observed)
