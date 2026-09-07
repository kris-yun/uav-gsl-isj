"""Synthetic online M2 state-machine test; no ROS, House or source truth."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parents[2] / "closed_loop" / "ctpi"
sys.path.insert(0, str(HERE))
from cstar_m2_online import OnlineM2Session, validate_law_shape
from cstar_reference import CPORouteLaw


@dataclass
class Provider:
    calls: list

    def predict(self, prefix, request):
        self.calls.append((tuple(prefix), request))
        return CPORouteLaw.from_hazards([0.2, 0.4], [0.0, 0.1], [0.2, 0.2])


def expect_error(fn, text):
    try:
        fn()
    except ValueError as exc:
        assert text in str(exc), (str(exc), text)
    else:
        raise AssertionError("expected " + text)


def main():
    provider = Provider([])
    session = OnlineM2Session(provider, max_history=8)
    # Topic callback order is arbitrary; stamp join is not.
    session.ingest("pose", 0, (0.0, 0.0))
    session.ingest("gas", 0, (0.0,))
    session.ingest("wind", 0, (0.1, 0.0))
    assert session.ready and session.observation_count == 0
    session.ingest("pose", 200_000_000, (0.2, 0.0))
    session.ingest("wind", 200_000_000, (0.1, 0.0))
    expect_error(lambda: session.ingest("gas", 200_000_000, (0.1,)), "WITHOUT_PREDICTION")
    assert session.ingress.failed

    provider = Provider([])
    session = OnlineM2Session(provider, max_history=8)
    for kind, values in (("wind", (0.1, 0.0)), ("pose", (0.0, 0.0)), ("gas", (0.0,))):
        session.ingest(kind, 0, values)
    law = session.predict_before_observe((1.0, 1.0), ((0.0, 0.0), (1.0, 0.0)))
    validate_law_shape(law, 2)
    assert len(provider.calls) == 1 and len(provider.calls[0][0]) == 1
    # Future route prediction cannot be armed twice and one positive frame is
    # consumed exactly once after all three same-stamp topic messages arrive.
    expect_error(lambda: session.predict_before_observe((1, 1), ((0, 0),)), "ALREADY_ARMED")
    session.ingest("pose", 200_000_000, (0.2, 0.0))
    session.ingest("wind", 200_000_000, (0.1, 0.0))
    assert session.ingest("gas", 200_000_000, (0.2,)) == 1
    assert session.observation_count == 1 and not session._armed
    # Ingress terminal failure is intentionally sticky; test it on a separate
    # session so the valid session below remains usable.
    incomplete = OnlineM2Session(Provider([]), max_history=8)
    for kind, values in (("wind", (0.1, 0.0)), ("pose", (0.0, 0.0)), ("gas", (0.0,))):
        incomplete.ingest(kind, 0, values)
    expect_error(lambda: incomplete.finish(400_000_000), "INCOMPLETE_HORIZON")
    session.predict_before_observe((1.0, 1.0), ((0.0, 0.0),))
    session.ingest("pose", 400_000_000, (0.4, 0.0))
    session.ingest("wind", 400_000_000, (0.1, 0.0))
    session.ingest("gas", 400_000_000, (0.3,))
    session.finish(400_000_000)
    assert session.prediction_count == 2 and session.observation_count == 2
    assert provider.calls[1][0][-1].stamp_ns == 200_000_000
    print("CSTAR_M2_ONLINE_STATE_MACHINE_SELFTEST PASS")


if __name__ == "__main__":
    main()
