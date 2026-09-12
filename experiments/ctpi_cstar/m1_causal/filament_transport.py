"""Reference fixed-source filament evolution; NOT validated ROS transport.

Wind and obstacle handling are mandatory external, auditable dependencies.
Release is point-source, not spatially resampled. Numerical laws follow the
inspected GADEN Euler update, but RNG/point emission do not reproduce its binary.
"""
from dataclasses import dataclass
from fractions import Fraction
import math
import hashlib
import json
from typing import Callable
from .filament_observation import XYZ, _xyz, FilamentState, CandidateFrame


def keyed_normal(seed: int, member_id: str, particle_id: int, step: int, axis: int) -> float:
    """CRN_V1: counter-based normal, independent of candidate and survivors.

    A particle id is its cumulative emission ordinal, not its vector position.
    Box-Muller inputs use open-interval 52-bit uniforms from SHA256.
    """
    key = json.dumps(['M1_CRN_V1', seed, member_id, particle_id, step, axis],
                     ensure_ascii=True, separators=(',', ':')).encode('ascii')
    digest = hashlib.sha256(key).digest()
    u = ((int.from_bytes(digest[:8], 'big') >> 12) + .5) / 2**52
    v = ((int.from_bytes(digest[8:16], 'big') >> 12) + .5) / 2**52
    return math.sqrt(-2*math.log(u))*math.cos(2*math.pi*v)


@dataclass(frozen=True)
class TransportConfig:
    dt_s: float
    filaments_per_s: float
    moles_per_filament: float
    initial_sigma_cm: float
    growth_cm2_per_s: float
    noise_velocity_std_m_s: float
    air_moles_per_cm3: float
    gas_specific_gravity: float

    def validate(self):
        positive = (self.dt_s, self.filaments_per_s, self.moles_per_filament,
                    self.initial_sigma_cm, self.air_moles_per_cm3, self.gas_specific_gravity)
        nonnegative = (self.growth_cm2_per_s, self.noise_velocity_std_m_s)
        if any(not math.isfinite(x) or x <= 0 for x in positive) or any(not math.isfinite(x) or x < 0 for x in nonnegative):
            raise ValueError('M1_TRANSPORT_CONFIG')


@dataclass(frozen=True)
class WindSnapshot:
    available_s: float
    velocity_m_s: Callable[[XYZ], XYZ]


class FixedSourceMember:
    """Explicit empty t=0 plume; no invented steady-state/prehistory bootstrap."""
    def __init__(self, *, candidate_id: str, member_id: str, source_m: XYZ,
                 config: TransportConfig, seed: int,
                 is_free: Callable[[XYZ], bool],
                 step_boundary: Callable[[XYZ, XYZ], XYZ | None]):
        config.validate()
        _xyz(source_m)
        if not candidate_id or not member_id or not is_free(source_m):
            raise ValueError('M1_TRANSPORT_SOURCE')
        self._identity = (candidate_id, member_id, tuple(source_m))
        self._config = config
        self._is_free = is_free
        self._step_boundary = step_boundary
        if not isinstance(seed, int):
            raise ValueError('M1_TRANSPORT_SEED')
        self._seed = seed
        self._release_per_step = Fraction(str(config.dt_s))*Fraction(str(config.filaments_per_s))
        self._steps = 0
        self._filaments = ()
        self._particle_ids = ()
        self._last_wind_s = -math.inf

    @property
    def time_s(self):
        return self._steps*self._config.dt_s

    def advance(self, *, wind: WindSnapshot, sensor_pose_m: XYZ) -> CandidateFrame:
        _xyz(sensor_pose_m)
        if not self._is_free(sensor_pose_m):
            raise ValueError('M1_TRANSPORT_SENSOR_POSE')
        if (not math.isfinite(wind.available_s) or wind.available_s < 0
                or wind.available_s > self.time_s or wind.available_s < self._last_wind_s):
            raise ValueError('M1_TRANSPORT_WIND_NOT_AVAILABLE')
        c = self._config
        # No mutable RNG stream: removal of another particle cannot shift keys.
        released = int((self._steps+1)*self._release_per_step)-int(self._steps*self._release_per_step)
        particles = self._filaments + tuple(FilamentState(self._identity[2], c.initial_sigma_cm,
                                  c.moles_per_filament) for _ in range(released))
        first_new_id = int(self._steps*self._release_per_step)
        particle_ids = self._particle_ids + tuple(range(first_new_id, first_new_id+released))
        updated = []
        updated_ids = []
        for particle_id, f in zip(particle_ids, particles):
            velocity = wind.velocity_m_s(f.position_m)
            _xyz(velocity)
            # Native GADEN terminal-buoyancy approximation, with explicit gas
            # density ratio. g=9.8 m/s2, air density=1.205 kg/m3, mu=19e-6 Pa s.
            centre_fraction = f.moles / ((2*math.pi)**1.5*f.sigma_cm**3*c.air_moles_per_cm3)
            buoyancy = 9.8*(1-c.gas_specific_gravity)*1.205*centre_fraction/(18*19.e-6)
            proposed = tuple(f.position_m[i]+c.dt_s*(velocity[i]+(buoyancy if i == 2 else 0.)
                             +c.noise_velocity_std_m_s*keyed_normal(self._seed, self._identity[1],
                                particle_id, self._steps, i)) for i in range(3))
            _xyz(proposed)
            destination = self._step_boundary(f.position_m, proposed)
            if destination is None:  # explicit outlet; not arbitrary clipping
                continue
            _xyz(destination)
            if not self._is_free(destination):
                raise ValueError('M1_TRANSPORT_BOUNDARY_RETURNED_OBSTACLE')
            state = FilamentState(tuple(destination), f.sigma_cm+c.growth_cm2_per_s*c.dt_s/(2*f.sigma_cm), f.moles)
            state.validate()
            updated.append(state)
            updated_ids.append(particle_id)
        self._filaments = tuple(updated)
        self._particle_ids = tuple(updated_ids)
        self._steps += 1
        self._last_wind_s = wind.available_s
        return CandidateFrame(self.time_s, *self._identity, tuple(sensor_pose_m), self._filaments, wind.available_s)
