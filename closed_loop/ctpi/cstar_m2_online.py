"""Strict online M2 boundary: stamped observations in, route law out.

This module deliberately contains no source estimator, source truth, future
wind/gas access, planner weight, or predictive bank. A provider implementing
the scientific CPO law is injected. The session enforces prediction-before-
observation and preserves the measured prefix as the only runtime history.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol, Sequence

from ctpi_v2_ingress import Frame, StampedIngress


@dataclass(frozen=True)
class RouteRequest:
    source_xy: tuple[float, float]
    route_xy: tuple[tuple[float, float], ...]

    def validate(self) -> None:
        if len(self.source_xy) != 2 or not all(math.isfinite(float(x)) for x in self.source_xy):
            raise ValueError("CSTAR_M2_SOURCE_HYPOTHESIS_INVALID")
        if not self.route_xy:
            raise ValueError("CSTAR_M2_EMPTY_ROUTE")
        if any(len(p) != 2 or not all(math.isfinite(float(x)) for x in p)
               for p in self.route_xy):
            raise ValueError("CSTAR_M2_ROUTE_POINT_INVALID")


class RouteLawProvider(Protocol):
    """Provider receives a copied past-only prefix and one route intervention.

    It must not mutate the prefix, read future values, or use simulator/member
    identity. The returned object is checked by the reference contract in the
    caller's integration tests.
    """

    def predict(self, prefix: Sequence[Frame], request: RouteRequest):
        ...


class OnlineM2Session:
    """Prediction-before-observation state machine for a real ROS ingress.

    t=0 is bootstrap. Each positive frame is accepted only after a prediction
    token was armed using the preceding prefix. A prediction is not evidence;
    the subsequent frame is appended exactly once by ``ingest``.
    """

    def __init__(self, provider: RouteLawProvider, *, cadence_ns: int = 200_000_000,
                 max_history: int = 1500):
        if not callable(getattr(provider, "predict", None)):
            raise ValueError("CSTAR_M2_PROVIDER_INTERFACE")
        if type(max_history) is not int or max_history < 1:
            raise ValueError("CSTAR_M2_HISTORY_LIMIT")
        self.provider = provider
        self.ingress = StampedIngress(cadence_ns=cadence_ns, max_pending=max_history)
        self.max_history = max_history
        self._prefix: list[Frame] = []
        self._armed = False
        self._last_request: RouteRequest | None = None
        self._last_law = None
        self.prediction_count = 0
        self.observation_count = 0

    @property
    def prefix(self) -> tuple[Frame, ...]:
        return tuple(self._prefix)

    @property
    def ready(self) -> bool:
        return bool(self._prefix) and not self.ingress.failed

    def ingest(self, kind: str, stamp_ns: int, values) -> int:
        """Push one ROS topic value; return number of newly joined frames."""
        frames = self.ingress.push(kind, stamp_ns, values)
        accepted = 0
        for frame in frames:
            if frame.stamp_ns == 0:
                if self._prefix:
                    raise ValueError("CSTAR_M2_DUPLICATE_BOOTSTRAP")
                self._prefix.append(frame)
                continue
            if not self._armed:
                self.ingress.failed = True
                raise ValueError("CSTAR_M2_OBSERVE_WITHOUT_PREDICTION")
            self._prefix.append(frame)
            if len(self._prefix) > self.max_history:
                self._prefix.pop(0)
            self._armed = False
            self.observation_count += 1
            accepted += 1
        return accepted

    def predict_before_observe(self, source_xy, route_xy):
        """Issue one route prediction from the current prefix and arm next frame."""
        if not self.ready:
            raise ValueError("CSTAR_M2_PREFIX_NOT_READY")
        if self._armed:
            raise ValueError("CSTAR_M2_PREDICTION_ALREADY_ARMED")
        request = RouteRequest(tuple(map(float, source_xy)),
                               tuple(tuple(map(float, p)) for p in route_xy))
        request.validate()
        prefix = tuple(self._prefix)  # provider cannot mutate online state
        law = self.provider.predict(prefix, request)
        if law is None:
            raise ValueError("CSTAR_M2_PROVIDER_RETURNED_NONE")
        self._last_request = request
        self._last_law = law
        self._armed = True
        self.prediction_count += 1
        return law

    def finish(self, final_stamp_ns: int) -> None:
        if self._armed:
            raise ValueError("CSTAR_M2_UNCONSUMED_PREDICTION")
        self.ingress.finish(final_stamp_ns)


def validate_law_shape(law, horizon: int) -> None:
    """Minimal M2 output guard; numerical law semantics stay in cstar_reference."""
    if horizon < 1:
        raise ValueError("CSTAR_M2_HORIZON")
    for name in ("first_hit_prob", "encounter_cdf", "logppm_mean", "logppm_scale"):
        value = getattr(law, name, None)
        if value is None or len(value) != (horizon + 1 if name == "first_hit_prob" else horizon):
            raise ValueError("CSTAR_M2_LAW_SHAPE:" + name)
    q = float(getattr(law, "route_committor", float("nan")))
    if not math.isfinite(q) or not 0.0 <= q <= 1.0:
        raise ValueError("CSTAR_M2_ROUTE_COMMITTOR")
