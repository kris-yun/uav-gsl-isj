"""V41 proof-of-executable closed-loop algorithmic candidate (not native S2 GO)."""
from .types import Configuration,Reading,Trajectory
from .inference import joint_posterior,Posterior
from .physics import GaussianAdvectionDemo,ForwardModel
from .encoder import encode,Signature
from .control import Controller,ActionDecision,OpenGeometry
from .legacy_forward import LegacyV34MultiUAV
__all__=['Configuration','Reading','Trajectory','joint_posterior','Posterior',
         'GaussianAdvectionDemo','ForwardModel','encode','Signature',
         'Controller','ActionDecision','OpenGeometry','LegacyV34MultiUAV']