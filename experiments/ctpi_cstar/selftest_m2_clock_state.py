"""Check two clocks and observable FOPDT state against analytic cases."""
from dataclasses import dataclass, replace
import math
from types import SimpleNamespace

from m2_cpo.physical_prior import PhysicalCPOProvider, PhysicalPriorConfig, _cell, _advance


@dataclass(frozen=True)
class Frame:
    stamp_ns: int
    gas_ppm: float
    pose_xy: tuple = (.5,.5)
    wind_uv: tuple = (0.,0.)


def main():
    import numpy as np
    rng=np.random.default_rng(12)
    for _ in range(30):
        mask=tuple(bool(x) for x in (rng.random(63)>.2))
        start=np.where(mask,rng.random(63),0.).tolist()
        cf=PhysicalPriorConfig(9,7,.1,.01,mask)
        wind=tuple(rng.uniform(-1,1,2))
        source=int(np.flatnonzero(mask)[0])
        reference=list(start); vectorized=list(start)
        _advance(reference,cf,wind,source,duration=.5)
        _advance(vectorized,replace(cf,transport_backend='numpy'),wind,source,duration=.5)
        assert np.allclose(reference,vectorized,atol=1e-12,rtol=1e-12)
        assert abs(sum(vectorized)-sum(start)-.5)<1e-10
    cfg=PhysicalPriorConfig(1,1,1.,0.,(True,),route_dt=.2,field_dt=.5,
                            transport_time_scale=2.5,sensor_dead=0.,
                            source_rate_values=(1.,),condition_noise_free_sensor=True)
    provider=PhysicalCPOProvider(cfg)
    prefix=[Frame(0,2.)]
    req=SimpleNamespace(source_xy=(.5,.5),route_xy=((.5,.5),)*3)
    law=provider.predict(prefix,req)
    alpha=math.exp(-.2/1.2)
    sensor=2.
    for k,mu in enumerate(law.logppm_mean,1):
        # One no-flux cell gains 0.5 per field step, sensor advances 0.2 s.
        sensor=alpha*sensor+(1-alpha)*(.5*k)
        assert abs(math.expm1(mu)-sensor)<1e-12
    # Source-masked context cannot acquire measured-gas dependence.
    context=provider.predict_context(prefix,req.route_xy)
    assert context==provider.predict_context([Frame(0,99.)],req.route_xy)
    assert all(mu==0. for mu in context.logppm_mean)
    for bad in [[Frame(200_000_000,0.)],[Frame(0,0.),Frame(400_000_000,0.)]]:
        try: provider.predict(bad,req)
        except ValueError as exc: assert 'BOOTSTRAP' in str(exc) or 'CADENCE' in str(exc)
        else: raise AssertionError('TRUNCATED_HISTORY_SILENTLY_RESET')
    try: provider.predict([Frame(0,1e6)],req)
    except ValueError as exc: assert 'SATURATED' in str(exc)
    else: raise AssertionError('SATURATION_TREATED_AS_KNOWN_STATE')
    print('CSTAR_M2_CLOCK_STATE_SELFTEST_PASS')


if __name__=='__main__': main()
