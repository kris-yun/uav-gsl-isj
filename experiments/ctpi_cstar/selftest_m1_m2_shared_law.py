"""Mechanism-only check that M1 can consume the same law emitted by M2."""
from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "m2_cpo"))
from m1_picr.route_law_score import score_route_laws
from m2_cpo.physical_prior import PhysicalCPOProvider, PhysicalPriorConfig


class Frame:
    wind_uv = (1.0, 0.0)
    pose_xy = (0.0, 1.0)


def main():
    cfg = PhysicalPriorConfig(nx=8, ny=3, dx=1.0, diffusion=0.05,
                              free=tuple(True for _ in range(24)))
    provider = PhysicalCPOProvider(cfg)
    prefix = (Frame(),)
    route = ((0.0, 1.0), (1.0, 1.0), (2.0, 1.0), (3.0, 1.0))
    requests = [type("R", (), {"source_xy": p, "route_xy": route})()
                for p in ((0.0, 1.0), (0.0, 0.0))]
    candidate_laws = [provider.predict(prefix, r) for r in requests]
    context = provider.predict_context(prefix, route)
    observed = candidate_laws[0].logppm_mean
    result = score_route_laws(candidate_laws, [context, context], observed,
                              [True] * len(route), rho=0.3)
    assert result.posterior[0] > result.posterior[1]
    print("CSTAR_M1_M2_SHARED_LAW_SELFTEST PASS")


if __name__ == "__main__":
    main()
