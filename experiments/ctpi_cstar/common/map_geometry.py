"""Shared ROS occupancy geometry for online priors and trajectory audits.

Reuse the environment validator's byte-exact PGM/YAML contract.  Runtime
arrays use bottom-row-first order; YAML origin is the lower cell corner.
"""
from pathlib import Path
import math

try:
    from ..validate_environment_alignment_v2 import read_pgm, parse_map_yaml, p_occ
except ImportError:
    from validate_environment_alignment_v2 import read_pgm, parse_map_yaml, p_occ


def load_map_info(directory: Path):
    config = parse_map_yaml(directory / 'navigation_slice.yaml')
    width, height, maximum, pixels = read_pgm(directory / config['image'])
    free = tuple(
        p_occ(pixels[(height - 1 - y) * width + x], maximum, config['negate'])
        < config['free_thresh']
        for y in range(height) for x in range(width)
    )
    ox, oy = map(float, config['origin'][:2])
    return width, height, free, ox, oy, float(config['resolution'])


def world_cell(x, y, ox, oy, resolution):
    if not all(math.isfinite(float(v)) for v in (x, y, ox, oy, resolution)) or resolution <= 0:
        raise ValueError('CSTAR_MAP_NONFINITE_OR_RESOLUTION')
    return math.floor((x - ox) / resolution), math.floor((y - oy) / resolution)
