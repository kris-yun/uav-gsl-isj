"""House123 environment factory -> online prediction-before-observe boundary."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'closed_loop/ctpi'))
from m2_cpo.environment import provider_from_environment
from cstar_m2_online import OnlineM2Session, RouteRequest, validate_law_shape


def main():
    for house in ('H01','H02','H03'):
        env=ROOT/'evidence/cstar_environment_20260906'
        provider=provider_from_environment(env/'maps_v1'/house,
                HERE/'CSTAR_ENVIRONMENT_CLOCK_V1.json',env/'probes_v1'/house/'sensor_manifest.json')
        c=provider.config
        assert c.transport_time_scale==2.5 and c.condition_noise_free_sensor
        index=next(i for i,free in enumerate(c.free) if free)
        y,x=divmod(index,c.nx)
        xy=(c.origin_xy[0]+(x+.5)*c.dx,c.origin_xy[1]+(y+.5)*c.dx)
        session=OnlineM2Session(provider)
        for kind,values in [('pose',xy),('gas',(0.,)),('wind',(.1,.02))]:
            session.ingest(kind,0,values)
        law=session.predict_before_observe(xy,(xy,)*3)
        validate_law_shape(law,3)
        for kind,values in [('pose',xy),('gas',(.2,)),('wind',(.08,.03))]:
            session.ingest(kind,200_000_000,values)
        session.finish(200_000_000)
        request=RouteRequest(xy,(xy,)*3)
        assert provider.predict(session.prefix,request)==provider.predict_assimilated(session.prefix,request)
    print('CSTAR_HOUSE123_M2_ENVIRONMENT_SESSION_PASS_NOT_CLOSED_LOOP')


if __name__=='__main__': main()
