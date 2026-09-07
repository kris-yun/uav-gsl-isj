"""Bind the online physical provider to declared map, clock and sensor files.

No House-specific coordinates, rates, raw field, source truth or future trace
are read. This factory prevents replay metadata becoming unused documentation.
"""
import json
import math
from pathlib import Path

try:
    from ..common.map_geometry import load_map_info
except ImportError:
    from common.map_geometry import load_map_info
from .physical_prior import PhysicalCPOProvider, PhysicalPriorConfig


class PrefixAssimilatedPhysicalProvider(PhysicalCPOProvider):
    """Expose the explicitly prefix-fitted predictor through the online API."""
    def predict(self,prefix,request):
        return self.predict_assimilated(prefix,request)


def provider_from_environment(map_directory, clock_path, sensor_manifest_path, *,
                              diffusion=.01, condition_noise_free_sensor=True,
                              transport_backend='numpy', assimilate_prefix=True):
    nx,ny,free,ox,oy,dx=load_map_info(Path(map_directory))
    clock=json.loads(Path(clock_path).read_text())
    sensor=json.loads(Path(sensor_manifest_path).read_text())['sensor']['config']
    dt=float(clock['sensor_dt_s']); field_dt=float(clock['stored_field_dt_s'])
    ratio=float(clock['field_replay_speed_ratio'])
    if not math.isclose(dt*ratio,field_dt) or clock['frame_id']!='map':
        raise ValueError('CSTAR_M2_ENVIRONMENT_CLOCK')
    if not math.isclose(sensor['tau_rise_s'],sensor['tau_recovery_s']):
        raise ValueError('CSTAR_M2_ENVIRONMENT_ASYMMETRIC_SENSOR_UNSUPPORTED')
    if any(float(sensor[k])!=v for k,v in {'gain':1.,'baseline':0.,'drift_rate_ppm_s':0.}.items()):
        raise ValueError('CSTAR_M2_ENVIRONMENT_SENSOR_RESPONSE_UNSUPPORTED')
    if condition_noise_free_sensor:
        expected={'gain':1.,'baseline':0.,'drift_rate_ppm_s':0.,'noise_std_ppm':0.,
                  'saturation_min_ppm':0.,'saturation_max_ppm':1e6}
        if any(float(sensor[k])!=v for k,v in expected.items()):
            raise ValueError('CSTAR_M2_ENVIRONMENT_SENSOR_STATE_NOT_OBSERVABLE')
    provider_type=PrefixAssimilatedPhysicalProvider if assimilate_prefix else PhysicalCPOProvider
    return provider_type(PhysicalPriorConfig(
        nx,ny,dx,diffusion,free,(ox,oy),field_dt=field_dt,route_dt=dt,
        sensor_tau=float(sensor['tau_rise_s']),sensor_dead=float(sensor['dead_time_s']),
        transport_time_scale=ratio,condition_noise_free_sensor=condition_noise_free_sensor,
        transport_backend=transport_backend))
