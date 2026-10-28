"""V46 body-centred dual-path reference controller.

The runnable Green/ZOH backend is an exact *specified discrete reference model*,
not a GADEN adapter, real-flight controller, or a native-performance result.
"""

from .core import (
    Gate, GateStatus, Qualifications, SensorSpec, RawFrame, RawBlock,
    SourceBank, GreenZOHModel, GaussianPosterior, Candidate, ConvexBoxSafety,
    ControllerConfig, Controller, ReferenceWorld,
)

