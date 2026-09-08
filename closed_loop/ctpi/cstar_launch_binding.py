"""Optional prospective launch binding; does not authorize a scientific arm."""
import json
from pathlib import Path

from experiments.ctpi_cstar.environment_runtime import load_runtime_preflight, require, sha256
from experiments.ctpi_cstar.common.map_geometry import load_map_info, world_cell


def validate_launch_binding(value):
    certificate = value('cstar_environment_preflight')
    if not certificate:
        return None  # explicitly preserve legacy reproduction semantics
    geometry_path = Path(value('cstar_geometry_manifest')).resolve()
    house = value('cstar_house')
    realization = Path(value('raw_gas_results')).resolve()
    report = load_runtime_preflight(certificate, value('raw_query_executable'),
                                    geometry_path, house, realization)
    geometry = json.loads(geometry_path.read_text(encoding='utf-8'))[house]
    map_path = Path(value('gmrf_map_yaml_file')).resolve()
    require(map_path == Path(geometry['map_yaml_path']).resolve(), 'LAUNCH_GMRF_MAP_PATH')
    require(sha256(map_path) == geometry['map_yaml_sha256'], 'LAUNCH_GMRF_MAP_BYTES')
    require(sha256(geometry['map_image_path']) == geometry['map_image_sha256'], 'LAUNCH_MAP_IMAGE_BYTES')
    occupancy = Path(value('vgr_data_path')) / 'OccupancyGrid3D.csv'
    require(sha256(occupancy) == geometry['occupancy_sha256'], 'LAUNCH_BRIDGE_OCCUPANCY')
    require(float(value('flight_height')) == geometry['navigation_height_m'], 'LAUNCH_HEIGHT')
    clock = report['clock_sensor']['clock']
    require(int(value('seed')) == clock['seed'] and float(value('deltaTime')) == clock['sensor_dt_s'],
            'LAUNCH_CLOCK_SEED')
    require(value('gaden_iteration_mode') == 'seeded_time_replay', 'LAUNCH_REPLAY_MODE')
    require(value('sensor_model_mode') == 'dynamic', 'LAUNCH_SENSOR_MODE')
    width, height, free, ox, oy, resolution = load_map_info(map_path.parent)
    x, y = world_cell(float(value('start_x')), float(value('start_y')), ox, oy, resolution)
    require(0 <= x < width and 0 <= y < height and free[x + y * width], 'LAUNCH_START_NOT_FREE')
    return {'house': house, 'map_yaml_sha256': geometry['map_yaml_sha256'],
            'environment_preflight_sha256': sha256(certificate),
            'scope': 'launch input binding only; actual GMRF grid and PMFS candidate grid still require live audit'}
