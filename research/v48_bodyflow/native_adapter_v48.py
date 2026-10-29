"""Port V48 proposal/safety resolution to the supplied V46 native B0.

This adapter intentionally RETAINS the original B0 and endpoint EIG.  It is an
interface/controlled-repair arm, NOT a qualified forward-model replacement.
No Green simulator is substituted for VGR.  The native root must contain the
user-supplied immutable evidence modules.  Restore/qualify the shared forward
backend separately as required by the execution contract.
"""
from pathlib import Path
import importlib,sys
from v47_flowolf.core import Controller,GateStatus


def controller_class(native_root: str | Path):
    root=Path(native_root).resolve()
    required=['native_backend.py','raw_tobit.py','DEVELOPMENT_ASSETS_FROZEN.json']
    if any(not (root/n).is_file() for n in required):
        raise FileNotFoundError('Missing native evidence root; no surrogate fallback')
    sys.path.insert(0,str(root))
    backend=importlib.import_module('native_backend')
    if Path(backend.__file__).resolve().parent!=root:
        raise RuntimeError('Another native backend is already imported; use a clean process')

    class NativeControllerV48(Controller):
        backend_scope='V46_B0_RETAINED_MODEL_UNQUALIFIED'
        score_scope='EXACT_BANK_XY_EIG_OUTER_MC_RAW_ENDPOINT'

        def __init__(self,posterior,safety,config,mode='m1_full',*,outer_samples=128):
            if not isinstance(posterior,backend.NativePosterior):
                raise TypeError('Must use the supplied NativePosterior, never GreenZOHModel')
            if not isinstance(outer_samples,int) or outer_samples<1:
                raise ValueError('Positive outer MC count required')
            super().__init__(posterior,safety,config,mode)
            self.mc_outer=outer_samples
            self.score_cache={}

        def _score(self,candidate):
            return backend.NativeController._score(self,candidate)

        def decide(self):
            self.score_cache={}
            action,receipt=super().decide()
            receipt['native_backend_scope']=self.backend_scope
            receipt['prediction_scope']=self.score_scope
            receipt['catalog_scales']=list(self.cfg.catalog_scales)
            # An interface pass cannot certify the fixed uniform-wind B0.
            if self.last_frame and self.last_frame.qualifications.model.status==GateStatus.UNKNOWN:
                receipt['source_confirmation']=False
            return action,receipt

    return NativeControllerV48
