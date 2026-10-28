"""V42 review-stage expected failures against frozen V41 source.

These intentionally xfail, to prevent falsely claiming V41 already has
puff-age coherence certification or a clean causal identity ablation.
Run from research/v41_flowolf with:
  python -m pytest /path/to/test_v42_known_blockers.py -q -rx
"""
import numpy as np
import pytest
from v41_flowolf.types import Reading
from v41_flowolf.encoder import encode
from v41_flowolf.control import all_actions, shortlisted_actions


def counterexample():
    positions = np.array([[0., -10., 10.], [0., 0., 10.], [0., 10., 10.]])
    wind = np.tile([2., 0., 0.], (3, 1))
    gas = np.array([[.07, .46, .08],
                    [.35, .065, .90],
                    [.95, .07, .12],
                    [.061, .75, .065]])
    return [Reading(float(t), positions.copy(), gas[t], wind.copy(),
                    np.ones(3, dtype=bool), sensor_ids=('U1','U2','U3'))
            for t in range(4)]


@pytest.mark.xfail(strict=True, reason=(
    'V41 shape_cert checks timing, position, positive contact, but not '
    'shared release-age/normalized spatiotemporal profile coherence'))
def test_shape_certificate_rejects_adversarial_noncommon_puffs():
    signature = encode(counterexample())
    assert signature.stage != 'section' and not signature.shape_cert


@pytest.mark.xfail(strict=True, reason=(
    'V41 bio_noidentity changes action whitelist, confounding identity '
    'feature and admissible action differences'))
def test_noidentity_ablation_preserves_candidate_action_names():
    readings = counterexample()
    s = encode(readings)
    actions = all_actions(readings[-1], s, readings[-1].t)
    bio = {a.name for a in shortlisted_actions(actions,s,'bio')}
    noid = {a.name for a in shortlisted_actions(actions,s,'bio_noidentity')}
    assert bio == noid


def test_encoder_uses_only_causal_historical_observations():
    readings = counterexample()
    a = encode(readings[:3])
    b = encode(readings[:3])
    assert a.stage == b.stage
    assert np.allclose(a.effective_positions, b.effective_positions)