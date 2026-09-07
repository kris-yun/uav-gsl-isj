"""Integration contract: stamped ingress -> physical causal route law."""
from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "m2_cpo"))
sys.path.insert(0, str(HERE.parent.parent / "closed_loop" / "ctpi"))
from m2_cpo.physical_prior import PhysicalCPOProvider, PhysicalPriorConfig
from cstar_m2_online import OnlineM2Session, validate_law_shape


def main():
    cfg = PhysicalPriorConfig(nx=6, ny=2, dx=1.0, diffusion=0.05,
                              free=tuple(True for _ in range(12)))
    session = OnlineM2Session(PhysicalCPOProvider(cfg), max_history=8)
    for kind, values in (("wind", (1.0, 0.0)), ("gas", (0.0,)),
                         ("pose", (0.0, 0.0))):
        session.ingest(kind, 0, values)
    law = session.predict_before_observe((0.0, 0.0),
                                         ((1.0, 0.0), (2.0, 0.0), (3.0, 0.0)))
    validate_law_shape(law, 3)
    for kind, values in (("gas", (0.0,)), ("pose", (0.2, 0.0)),
                         ("wind", (1.0, 0.0))):
        session.ingest(kind, 200_000_000, values)
    session.finish(200_000_000)
    assert session.prediction_count == 1 and session.observation_count == 1
    print("CSTAR_M2_ONLINE_PHYSICAL_INTEGRATION_SELFTEST PASS")


if __name__ == "__main__":
    main()
