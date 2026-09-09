"""Analytic tests for the frozen M1 counterfactual likelihood contract."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from m1_causal.counterfactual_likelihood import (
    FopdtConfig, decide_with_observability, fopdt_response, score_candidates,
)


def main() -> None:
    stamps = (0.2, 0.4, 0.6, 0.8, 1.0, 1.2)
    sensor = FopdtConfig(tau_s=1.2, dead_time_s=0.4)
    source_members = ((0., 0., 1., 1., 1., 1.), (0., 0., .9, 1., 1.1, 1.))
    decoy_members = ((0., 0., 0., 0., 0., 0.), (0., 0., .1, 0., 0., .1))
    observed = fopdt_response(stamps, source_members[0], sensor)
    scores = score_candidates(timestamps_s=stamps, observed_sensor=observed,
                              candidate_member_exposure={"source": source_members, "decoy": decoy_members},
                              sensor=sensor, observation_sigma=.05)
    assert scores[0].candidate_id == "source"
    assert scores[0].mean_response[2] == 0.0  # 0.4 s delay is preserved.
    assert decide_with_observability(scores, sensor_discrepancy_bound=.01).decision == "COMMIT"
    identical = score_candidates(timestamps_s=stamps, observed_sensor=observed,
                                 candidate_member_exposure={"a": source_members, "b": source_members},
                                 sensor=sensor, observation_sigma=.05)
    assert decide_with_observability(identical, sensor_discrepancy_bound=.01).decision == "ABSTAIN"
    # Bind the implementation to the simulator's audited piecewise-linear,
    # delayed FOPDT law on a nonconstant trace.  This prevents a merely
    # first-order-looking recurrence from being accepted as the sensor law.
    sensor_path = Path(__file__).resolve().parents[2] / "evidence" / "cstar_environment_20260906" / "source_snapshot" / "sensor_model.py"
    module_spec = importlib.util.spec_from_file_location("audited_sensor_model", sensor_path)
    assert module_spec is not None and module_spec.loader is not None
    audited = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = audited
    module_spec.loader.exec_module(audited)
    exposure = (0., .2, 1.0, .4, 1.2, .1)
    model = audited.SensorModel("fopdt", seed=12)
    reference = tuple(model.process(value, .2) for value in exposure)
    ours = fopdt_response(stamps, exposure, sensor)
    assert max(abs(left - right) for left, right in zip(reference, ours)) < 1.0e-12
    print("M1_CAUSAL_COUNTERFACTUAL_LIKELIHOOD_SELFTEST=PASS")


if __name__ == "__main__":
    main()
