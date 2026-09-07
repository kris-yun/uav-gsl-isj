"""CPU contract test for the causal finite-volume M2 physical prior."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "m2_cpo"))
from m2_cpo.physical_prior import PhysicalCPOProvider, PhysicalPriorConfig


@dataclass(frozen=True)
class Frame:
    wind_uv: tuple[float, float]
    pose_xy: tuple[float, float] = (0.0, 1.0)


@dataclass(frozen=True)
class Request:
    source_xy: tuple[float, float]
    route_xy: tuple[tuple[float, float], ...]


def expect_error(fn, code):
    try:
        fn()
    except ValueError as exc:
        assert code in str(exc), (str(exc), code)
    else:
        raise AssertionError("expected " + code)


def main():
    cfg = PhysicalPriorConfig(
        nx=5, ny=3, dx=1.0, diffusion=0.05,
        free=tuple(True for _ in range(15)),
        field_dt=0.5, route_dt=0.2, source_rate_per_field_second=1.0,
        sensor_tau=1.2, sensor_dead=0.4, hazard_scale=0.2,
    )
    provider = PhysicalCPOProvider(cfg)
    prefix = (Frame((1.0, 0.0)),)
    req = Request((0.0, 1.0), ((0.0, 1.0), (1.0, 1.0), (2.0, 1.0)))
    law = provider.predict(prefix, req)
    assert len(law.first_hit_prob) == 4
    assert all(0.0 <= p <= 1.0 for p in law.first_hit_prob)
    assert abs(sum(law.first_hit_prob) - 1.0) < 1e-12
    assert 0.0 <= law.route_committor <= 1.0
    components, weights = provider.predict_ensemble(prefix, req)
    assert len(components) == 3 and abs(sum(weights) - 1.0) < 1e-12
    assert any(components[0].logppm_mean[i] != components[-1].logppm_mean[i]
               for i in range(3))
    context_a = provider.predict_context(prefix, req.route_xy)
    context_b = provider.predict_context(prefix, req.route_xy)
    assert context_a == context_b  # source identity is absent from the context law
    assert provider.predict_context(prefix, req.route_xy) == context_a
    # The provider receives a decision-time prefix.  Mutating a caller-owned
    # list after prediction cannot alter the already returned law.
    mutable_prefix = [Frame((1.0, 0.0))]
    before = provider.predict(mutable_prefix, req)
    mutable_prefix.append(Frame((99.0, -99.0)))
    assert before == provider.predict([Frame((1.0, 0.0))], req)
    # Causal empty-prefix and solid-cell failures are explicit.
    expect_error(lambda: provider.predict((), req), "EMPTY_PREFIX")
    blocked = PhysicalPriorConfig(nx=2, ny=1, dx=1.0, diffusion=0.0,
                                  free=(True, False))
    bad = PhysicalCPOProvider(blocked)
    expect_error(lambda: bad.predict(prefix, Request((1.0, 0.0), ((0.0, 0.0),))),
                 "POINT_IN_SOLID")
    print("CSTAR_M2_PHYSICAL_PRIOR_SELFTEST PASS")


if __name__ == "__main__":
    main()
