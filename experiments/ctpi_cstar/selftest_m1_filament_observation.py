"""Analytic tests only; not native binary parity or cross-House utility."""
from dataclasses import replace
import json
import math
from m1_causal.filament_observation import FilamentState, CandidateFrame, concentration_ppm, observe_candidate_prefix
from m1_causal.counterfactual_likelihood import FopdtConfig, fopdt_response, score_candidates


def main():
    # Synthetic constants chosen to make centre concentration exactly 1 ppm.
    density = 4.e-5
    sigma = 10.
    mass = (2*math.pi)**1.5 * sigma**3 * density / 1.e6
    filament = FilamentState((0., 0., 0.), sigma, mass)
    def sample(point, states=(filament,), visible=lambda a,b: True):
        return concentration_ppm(states, point, air_moles_per_cm3=density, visible=visible)
    assert math.isclose(sample((0.,0.,0.)), 1., abs_tol=1.e-14)
    assert math.isclose(sample((.1,0.,0.)), math.exp(-.5), rel_tol=1.e-14)
    assert sample((.3,0.,0.)) == 0  # strict native 3-sigma cutoff
    assert sample((0.,0.,0.), visible=lambda a,b: False) == 0
    assert math.isclose(sample((0.,0.,0.), (filament, filament)), 2.)
    assert sample((0.,0.,.31)) == 0  # no silent 2D projection
    wide = replace(filament, sigma_cm=20.)
    assert math.isclose(sample((0.,0.,0.), (wide,)), .125)
    assert sample((0.,0.,0.), ()) == 0
    # Centre lies outside a sample's 0.1 m cell, yet Gaussian support reaches it.
    assert int(.15/.1) != int(filament.position_m[0]/.1)
    off_cell_ppm = sample((.15,0.,0.))
    assert off_cell_ppm > 0
    frames = tuple(CandidateFrame(i*.2, 'c', 'm', (0.,0.,0.), (i*.01,0.,0.),
                                  (filament,), (i-1)*.2) for i in range(1,7))
    values = observe_candidate_prefix(frames, air_moles_per_cm3=density, visible=lambda a,b: True)
    for k in range(1, len(frames)+1):
        assert observe_candidate_prefix(frames[:k], air_moles_per_cm3=density, visible=lambda a,b: True) == values[:k]
    bad = (replace(frames[1], fixed_source_m=(1.,0.,0.)),
           replace(frames[1], latest_input_s=10.), replace(frames[1], stamp_s=frames[0].stamp_s))
    for item in bad:
        try:
            observe_candidate_prefix((frames[0],item), air_moles_per_cm3=density, visible=lambda a,b: True)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid prefix accepted')
    sensor = FopdtConfig(1.2,.4)
    stamps = tuple(f.stamp_s for f in frames)
    observed = fopdt_response(stamps,values,sensor)
    scores = score_candidates(timestamps_s=stamps, observed_sensor=observed,
        candidate_member_exposure={'c':(values,), 'empty':((0.,)*len(values),)},
        sensor=sensor, observation_sigma=.05, input_semantics='time_resolved_concentration')
    assert scores[0].candidate_id == 'c'
    print(json.dumps(dict(verdict='M1_FILAMENT_OBSERVATION_ANALYTIC_PASS',
        off_cell_concentration_ppm=off_cell_ppm,
        scope='analytic kernel, prefix integrity and synthetic likelihood integration only')))


if __name__ == '__main__':
    main()
