"""Small immutable online data structures. Truth is never an inference input."""
from dataclasses import dataclass, asdict
from typing import Protocol, Sequence
import numpy as np

@dataclass(frozen=True)
class Action:
    x: float
    y: float
    z: float = 1.0
    time: float = 0.0
    dwell: float = 1.0

@dataclass(frozen=True)
class Observation:
    uid: str
    action: Action
    wind: tuple[float, float]
    gas: float

@dataclass(frozen=True)
class Mechanism:
    kind: str = "nominal"
    onset: int = 0
    duration: int | None = None
    magnitude: float = 0.0

    def active(self, index: int) -> bool:
        return self.kind != "nominal" and index >= self.onset and (self.duration is None or index < self.onset + self.duration)

class JointGenerator(Protocol):
    def log_prob(self, history: Sequence[Observation], source: np.ndarray, mechanism: Mechanism) -> float: ...
    def sample_future(self, history: Sequence[Observation], actions: Sequence[Action], source: np.ndarray, mechanism: Mechanism, rng: np.random.Generator) -> list[Observation]: ...

def observation_to_dict(obs: Observation) -> dict:
    return asdict(obs)

def observation_from_dict(obj: dict) -> Observation:
    return Observation(str(obj['uid']), Action(**obj['action']), tuple(map(float,obj['wind'][:2])), float(obj['gas']))
