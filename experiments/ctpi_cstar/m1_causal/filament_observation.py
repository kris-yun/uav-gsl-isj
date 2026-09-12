"""Chronological concentration observation of candidate filament states.

Implements the inspected GADEN CPU Gaussian observation kernel, not its
transport integrator. Positions are metres, sigma centimetres, mass moles,
air density mol/cm^3, output ppm. Visibility is required from the map owner.
Snapshot production must separately validate transport and source identity.
"""
from dataclasses import dataclass
import math
from typing import Callable, Sequence

XYZ = tuple[float, float, float]


def _xyz(value: XYZ) -> None:
    if len(value) != 3 or not all(math.isfinite(x) for x in value):
        raise ValueError('M1_FILAMENT_POSITION')


@dataclass(frozen=True)
class FilamentState:
    position_m: XYZ
    sigma_cm: float
    moles: float

    def validate(self) -> None:
        _xyz(self.position_m)
        if not math.isfinite(self.sigma_cm) or self.sigma_cm <= 0:
            raise ValueError('M1_FILAMENT_SIGMA')
        if not math.isfinite(self.moles) or self.moles < 0:
            raise ValueError('M1_FILAMENT_MASS')


def concentration_ppm(filaments: Sequence[FilamentState], sample_m: XYZ, *,
                      air_moles_per_cm3: float,
                      visible: Callable[[XYZ, XYZ], bool]) -> float:
    """GADEN 3-sigma truncated, visibility-filtered Gaussian sum.

    The truncation is not renormalized, matching the inspected CPU kernel.
    This function does not silently substitute 2D distance or free-space LOS.
    """
    _xyz(sample_m)
    if not math.isfinite(air_moles_per_cm3) or air_moles_per_cm3 <= 0:
        raise ValueError('M1_FILAMENT_AIR_DENSITY')
    contributions = []
    for f in filaments:
        f.validate()
        distance2_m = sum((x-y)**2 for x,y in zip(f.position_m, sample_m))
        if distance2_m >= (3*f.sigma_cm/100)**2:
            continue
        if not visible(sample_m, f.position_m):
            continue
        centre = 1.e6 * f.moles / ((2*math.pi)**1.5 * f.sigma_cm**3 * air_moles_per_cm3)
        contributions.append(centre * math.exp(-10000*distance2_m / (2*f.sigma_cm**2)))
    result = math.fsum(contributions)
    if not math.isfinite(result):
        raise ValueError('M1_FILAMENT_CONCENTRATION_OVERFLOW')
    return result


@dataclass(frozen=True)
class CandidateFrame:
    stamp_s: float
    candidate_id: str
    member_id: str
    fixed_source_m: XYZ
    sensor_pose_m: XYZ
    filaments: tuple[FilamentState, ...]
    # Latest input used to produce this state, not a future wind timestamp.
    latest_input_s: float


def observe_candidate_prefix(frames: Sequence[CandidateFrame], *,
                             air_moles_per_cm3: float,
                             visible: Callable[[XYZ, XYZ], bool]) -> tuple[float, ...]:
    """One immutable candidate/member/source per strictly ordered prefix.

    Metadata checks reject explicit future inputs and identity switches; they
    cannot certify that a producer truthfully reported its inputs.
    """
    if not frames:
        raise ValueError('M1_FILAMENT_EMPTY_PREFIX')
    identity = (frames[0].candidate_id, frames[0].member_id, frames[0].fixed_source_m)
    if not identity[0] or not identity[1]:
        raise ValueError('M1_FILAMENT_IDENTITY')
    previous = -math.inf
    result = []
    for frame in frames:
        _xyz(frame.fixed_source_m)
        if (frame.candidate_id, frame.member_id, frame.fixed_source_m) != identity:
            raise ValueError('M1_FILAMENT_SOURCE_SWITCH')
        if (not math.isfinite(frame.stamp_s) or frame.stamp_s < 0 or frame.stamp_s <= previous
                or not math.isfinite(frame.latest_input_s) or frame.latest_input_s > frame.stamp_s):
            raise ValueError('M1_FILAMENT_CAUSAL_CLOCK')
        result.append(concentration_ppm(frame.filaments, frame.sensor_pose_m,
                                       air_moles_per_cm3=air_moles_per_cm3, visible=visible))
        previous = frame.stamp_s
    return tuple(result)
