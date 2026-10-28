"""Native S2 evaluator boundary. Only observations and public geometry reach policy.

The original 78MB S2 DATA-ONLY package is not included. This adapter validates
and imports it at runtime. The source-conditioned approximation is an independent
ordinary model, and must pass separate forward-parity tests before any E1/E2 GO.

Scientific boundary is API-level, not an OS sandbox. Source labels, future puff
states and evaluator wind fields are not passed to the Controller. Codex should
also run an import/static audit to enforce this on its own code base.
"""
from __future__ import annotations
import json,sys,importlib
from pathlib import Path
import numpy as np
from .types import Reading
from .control import Controller
from .public_geometry import PublicGeometry

EXPECTED_DATA_SHA='210771b27161b74d73c5e4d8c620a85f1652f402c80b81a68c12d41a03fceffe'
OBSERVATION_KEYS=frozenset({'tick','time_s','position_ENU_m','local_wind_m_s',
    'CH4_total_ppm','sensor_valid','instrument','sensor_delay_s','sensor_tau_s','hit'})


def check_root(root):
    root=Path(root).resolve()
    for p in ['dataset.json','code/s2dataset.py','code/agent_api.py',
              'assets/geometry.json','assets/obstacles.bin']:
        if not (root/p).is_file():
            raise FileNotFoundError('Missing complete native S2 file: '+str(root/p))
    meta=json.loads((root/'dataset.json').read_text())
    if (meta.get('version')!='DATA_ONLY_V1_20261026' or meta.get('worlds')!=5
            or meta.get('total_native_frames')!=3005 or meta.get('native_ticks_each')!=601):
        raise ValueError('Not the complete 5x601 native world and time range')
    if (root/'STATIC_SUBSET_NOTICE.json').exists():
        raise ValueError('V34 static-only subset MUST NOT stand in for native puff frames')
    return root,meta


class NativeGeometry:
    """Public map-only legality wrapper; NO private DatasetWorld or gas query."""
    def __init__(self,root): self._geom=PublicGeometry(root)
    def segment_legal(self,a,b):return bool(self._geom.segment_legal(a,b))


def load_sessions(root,world_id,start_xyz,*,sensor_seed=9001):
    root,meta=check_root(root)
    if world_id not in ('W001','W002','W003','W004','W005'):
        raise ValueError('Invalid world ID')
    code=str(root/'code')
    if code not in sys.path:sys.path.insert(0,code)
    reader=importlib.import_module('s2dataset')
    api=importlib.import_module('agent_api')
    world=reader.DatasetWorld(world_id)
    starts=np.asarray(start_xyz,float)
    if starts.shape!=(3,3):raise ValueError('S2 requires 3 UAV positions')
    public=PublicGeometry(root)
    if not public.valid_uav(starts):raise ValueError('Source-blind initial UAV formation not legal')
    if min(np.linalg.norm(starts[i]-starts[j]) for i in range(3)
           for j in range(i+1,3))<4.:
        raise ValueError('Initial UAV spacing < 4 m development safety envelope')
    sessions=[api.AgentSession(world,starts[i],sensor_seed=sensor_seed+101*i,
                   activity_bounds=meta['observation_ROI_ENU_m']) for i in range(3)]
    return sessions,meta


def reading_from_sessions(sessions,metadata,*,expected_tick=None):
    obs=[s.observe() for s in sessions]
    if any(set(x)!=OBSERVATION_KEYS for x in obs):
        raise ValueError('NATIVE_OBSERVATION_SCHEMA_DRIFT')
    ticks=[x['tick'] for x in obs]
    if len(set(ticks))!=1 or ticks[0]%10:
        raise ValueError('NOT_SIMULTANEOUS_1HZ_OBSERVATION')
    if expected_tick is not None and ticks[0]!=expected_tick:
        raise ValueError('UNEXPECTED_NATIVE_TIME_TICK')
    sensor=metadata['sensor']
    if any(not np.isclose(x['sensor_delay_s'],sensor['delay_s']) or
           not np.isclose(x['sensor_tau_s'],sensor['tau_s']) for x in obs):
        raise ValueError('NATIVE_SENSOR_CONTRACT_CHANGED')
    bkg=float(sensor['background_ppm'])
    return Reading(float(obs[0]['time_s']),
        np.asarray([x['position_ENU_m'] for x in obs],float),
        np.asarray([x['CH4_total_ppm']-bkg for x in obs],float),
        np.asarray([x['local_wind_m_s'] for x in obs],float),
        np.asarray([bool(x['sensor_valid']) for x in obs],bool),bkg,
        ('uav_0','uav_1','uav_2'))


def run_native(root,world_id,controller:Controller,start_xyz,
               *,sensor_seed=9001,duration_s=60):
    """Actual native data-only replay, NOT native source-conditioned PMFS.

    Multi-session parity must be compared against a single-session official
    AgentSession run before reporting data qualification. A shared-world multi-
    session sequential stepping may diverge from the reader's intended semantics.
    Even when gas queries are real, the posterior needs separate model audit.
    """
    if not isinstance(duration_s,int) or not 1<=duration_s<=60:
        raise ValueError('60 s physical playback only')
    sessions,meta=load_sessions(root,world_id,start_xyz,sensor_seed=sensor_seed)
    # Only public geometry is exposed to policy, not the complete native world.
    controller.geometry=NativeGeometry(root)
    audit={'world':world_id,'world_frames':meta['total_native_frames'],
           'model_type':type(controller.model).__name__,
           'source_conditioned_native_parity':'NOT_QUALIFIED',
           'multi_session_parity':'NOT_QUALIFIED',
           'truth_used_by_controller':False,'readouts':'ORIGINAL_AGENT_SESSION',
           'original_data_sha_expected':EXPECTED_DATA_SHA}
    rows=[]
    for t in range(duration_s):
        snapshot=reading_from_sessions(sessions,meta,expected_tick=t*10)
        dec=controller.step(snapshot)
        xy,pxy=controller.posterior.source_xy_probability()
        rows.append({'time':float(snapshot.t),'measured_excess_ppm':snapshot.gas_ppm.tolist(),
                     'pose_ENU':snapshot.pos.tolist(),'wind_ENU':snapshot.wind.tolist(),
                     'decision':dec.action.name,'velocity':dec.action.velocity.tolist(),
                     'source_candidate_map_3d':controller.posterior.map_source.tolist(),
                     'source_map_xy':controller.posterior.map_xy.tolist(),
                     'xy_grid_ENU':xy.tolist(), 'source_xy_probability':pxy.tolist(),
                     'model_gate_certified':dec.qualified,'phase':dec.stage,
                     'estimated_profile_margin':dec.pair_margin,
                     'future_response_calls':dec.forward_calls})
        for tick in range(10):
            for i,ss in enumerate(sessions):
                ss.step(dec.action.velocity[i].tolist())
    # Last 1 Hz response at native t=60 is an observed final sample but cannot
    # retroactively change any previous action. Store and update once.
    final=reading_from_sessions(sessions,meta,expected_tick=duration_s*10)
    controller.observe(final)
    xy,pxy=controller.posterior.source_xy_probability()
    rows.append({'time':final.t,'measured_excess_ppm':final.gas_ppm.tolist(),
                 'pose_ENU':final.pos.tolist(),'wind_ENU':final.wind.tolist(),
                 'decision':'FINAL_ONLY_NO_ACTION',
                 'source_candidate_map_3d':controller.posterior.map_source.tolist(),
                 'source_map_xy':controller.posterior.map_xy.tolist(),
                 'xy_grid_ENU':xy.tolist(), 'source_xy_probability':pxy.tolist(),
                 'model_gate_certified':False})
    audit['actual_sensor_records_per_uav']=len(rows)
    audit['model_verified_for_true_native_response']=False
    return {'audit':audit,'records':rows}