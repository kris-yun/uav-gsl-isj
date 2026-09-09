"""Unit tests for the M1 causal temporal transport provider."""
from __future__ import annotations

from types import SimpleNamespace

from m1_causal.temporal_transport import replay_candidate_exposure
from m2_cpo.physical_prior import PhysicalPriorConfig


def frame(stamp_ns: int, pose_xy: tuple[float, float], wind_uv: tuple[float, float]):
    return SimpleNamespace(stamp_ns=stamp_ns, pose_xy=pose_xy, wind_uv=wind_uv)


def main() -> None:
    config = PhysicalPriorConfig(nx=4, ny=1, dx=1.0, diffusion=0.0,
                                 free=(True,) * 4, route_dt=.2, field_dt=.2)
    prefix = (frame(0, (.5, .5), (1., 0.)), frame(200_000_000, (.5, .5), (1., 0.)),
              frame(400_000_000, (1.5, .5), (1., 0.)))
    response = replay_candidate_exposure(prefix, config=config, source_xy=(.5, .5))
    assert len(response) == 2 and response[0] > 0 and response[1] >= 0
    future_changed = prefix[:-1] + (frame(400_000_000, (1.5, .5), (-1., 0.)),)
    assert replay_candidate_exposure(prefix[:2], config=config, source_xy=(.5, .5)) == \
           replay_candidate_exposure(future_changed[:2], config=config, source_xy=(.5, .5))
    print("M1_CAUSAL_TEMPORAL_TRANSPORT_SELFTEST=PASS")


if __name__ == "__main__":
    main()
