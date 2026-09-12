"""Synthetic tests of reference transport, not House utility."""
from dataclasses import replace
import json
import math
from m1_causal.filament_transport import TransportConfig, WindSnapshot, FixedSourceMember
from m1_causal.filament_observation import observe_candidate_prefix


def main():
    c = TransportConfig(.2, 2.5, 1.e-8, 10., 2., 0., 4.e-5, 1.)
    def member(config=c, boundary=lambda a,b: b):
        return FixedSourceMember(candidate_id='c', member_id='m', source_m=(0.,0.,0.),
            config=config, seed=12, is_free=lambda p: True, step_boundary=boundary)
    a = member()
    frames = [a.advance(wind=WindSnapshot(i*.2, lambda p: (1.,0.,0.)), sensor_pose_m=(.15,0.,0.)) for i in range(10)]
    assert [len(f.filaments) for f in frames] == [0,1,1,2,2,3,3,4,4,5]
    assert math.isclose(sum(f.moles for f in frames[-1].filaments),5.e-8)
    assert math.isclose(frames[1].filaments[0].position_m[0], .2)
    assert math.isclose(frames[1].filaments[0].sigma_cm, 10.02)
    assert frames[-1].fixed_source_m == (0.,0.,0.)
    # Cold re-execution of a prefix must exactly equal its original trajectory.
    b = member()
    for i in range(5):
        assert b.advance(wind=WindSnapshot(i*.2,lambda p:(1.,0.,0.)),sensor_pose_m=(.15,0.,0.)) == frames[i]
    before = b.time_s
    try:
        b.advance(wind=WindSnapshot(100.,lambda p:(0.,0.,0.)),sensor_pose_m=(0.,0.,0.))
    except ValueError:
        assert b.time_s == before
    else:
        raise AssertionError('future wind accepted')
    outlet = member(boundary=lambda a,b: None)
    for i in range(4):
        assert not outlet.advance(wind=WindSnapshot(i*.2,lambda p:(1.,0.,0.)),sensor_pose_m=(0.,0.,0.)).filaments
    # Same seed + same inputs gives the same stochastic member, no source jitter.
    noisy = replace(c, noise_velocity_std_m_s=.1)
    x,y = member(noisy),member(noisy)
    for i in range(8):
        kwargs = dict(wind=WindSnapshot(i*.2,lambda p:(0.,0.,0.)),sensor_pose_m=(0.,0.,0.))
        assert x.advance(**kwargs) == y.advance(**kwargs)
    ppm = observe_candidate_prefix(frames, air_moles_per_cm3=c.air_moles_per_cm3, visible=lambda a,b: True)
    assert ppm[0] == 0 and ppm[1] > 0
    # Removing all old particles must not change the random forcing of newly
    # emitted corresponding particles. Sequential RNG streams fail this check.
    crn_config = replace(c, filaments_per_s=5., noise_velocity_std_m_s=.1)
    keep = member(crn_config)
    drop_old = member(crn_config, boundary=lambda a,b: b if a==(0.,0.,0.) else None)
    for i in range(10):
        kwargs = dict(wind=WindSnapshot(i*.2,lambda p:(1.,0.,0.)), sensor_pose_m=(0.,0.,0.))
        full, sparse = keep.advance(**kwargs), drop_old.advance(**kwargs)
        assert len(full.filaments)==i+1 and len(sparse.filaments)==1
        assert full.filaments[-1] == sparse.filaments[-1]
    print(json.dumps(dict(verdict='M1_FILAMENT_TRANSPORT_SYNTHETIC_PASS',
        samples=len(ppm), final_particle_count=5, concentration_at_second_sample_ppm=ppm[1],
        scope='fixed-source release, mass, advection, growth, outlets, RNG and prefix causality only')))


if __name__ == '__main__':
    main()
