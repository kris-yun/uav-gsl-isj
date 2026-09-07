"""Mechanism tests for PICR conditional-incremental evidence; synthetic only."""
from __future__ import annotations

from pathlib import Path
import sys
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.ctpi_cstar.m1_picr.conditional_evidence import (
    estimate_conditional_evidence, nuisance_permutation_invariance,
)


def reject(fn, marker):
    try:
        fn()
    except ValueError as exc:
        assert marker in str(exc), (str(exc), marker)
    else:
        raise AssertionError("expected " + marker)


def main():
    # Candidate 0 has the true source signal (+3) but also a nuisance shortcut
    # (+8). Raw same-input Bayes chooses the shortcut; residual evidence does not.
    source = torch.tensor([11.0, 8.0, 1.0])
    context = torch.tensor([8.0, 0.0, 0.0])
    raw = estimate_conditional_evidence(source, torch.zeros(3)).posterior
    cie = estimate_conditional_evidence(source, context).posterior
    assert int(raw.argmax()) == 0 and int(cie.argmax()) == 1, (raw, cie)
    assert cie[1] > cie[0] and torch.isclose(cie.sum(), torch.tensor(1.0), atol=1e-6)

    # A nuisance-only intervention can change context scores, but when the
    # source contrast is unchanged the ratio remains source-stable.
    source2 = torch.tensor([3.0, 1.0, 0.0])
    c1 = torch.tensor([4.0, 2.0, 1.0])
    c2 = torch.tensor([2.0, 0.0, -1.0])
    p1 = estimate_conditional_evidence(source2, c1).posterior
    p2 = estimate_conditional_evidence(source2, c2).posterior
    assert torch.allclose(p1, p2, atol=1e-6), (p1, p2)
    perm = nuisance_permutation_invariance(source2, c1, torch.tensor([2, 1, 0]))
    # Permuting nuisance/candidate pairing is a destructive control: it must
    # alter the residual rather than being silently ignored.
    assert not torch.allclose(perm, p1, atol=1e-6)

    # No valid frame is neutral evidence; valid zero is still scored.
    prior = torch.log(torch.tensor([0.2, 0.3, 0.5]))
    empty = estimate_conditional_evidence(source2, c1, prior, observation_valid=False)
    assert torch.allclose(empty.posterior, torch.tensor([0.2, 0.3, 0.5]), atol=1e-6)
    zero = estimate_conditional_evidence(torch.tensor([-1., -2., -3.]), torch.zeros(3), prior,
                                         observation_valid=True)
    assert int(zero.posterior.argmax()) == 0

    # Candidate-only masking and malformed inputs fail closed.
    reject(lambda: estimate_conditional_evidence(source, context, candidate_valid=torch.zeros(3, dtype=torch.bool)), "NO_VALID")
    reject(lambda: estimate_conditional_evidence(source[:2], context), "SHAPE")
    reject(lambda: estimate_conditional_evidence(source, context, candidate_valid=torch.tensor([1, 0, 1])), "MASK")
    reject(lambda: estimate_conditional_evidence(torch.tensor([float('nan'), 0., 1.]), context), "SOURCE")
    print("CSTAR_M1_CONDITIONAL_EVIDENCE_SELFTEST PASS")


if __name__ == "__main__":
    main()
