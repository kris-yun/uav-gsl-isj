"""M2 reference implementation.

The diagnostic network is deliberately absent from the likelihood algebra.  A
proposal can save computation; it cannot turn its own data-derived prediction
into another observation. All modes use a fixed, externally specified prior.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.special import logsumexp


class EvidenceLedger:
    """Append-only raw observation history with exactly-once ID semantics."""

    def __init__(self, observations=()):
        self._history = []
        self._ids = set()
        self.version = 0
        self.extend(observations)

    def append(self, observation):
        if not str(observation.uid):
            raise ValueError("Observation ID must be nonempty")
        if observation.uid in self._ids:
            raise ValueError(f"Duplicate evidence ID: {observation.uid}")
        if self._history and observation.action.time < self._history[-1].action.time:
            raise ValueError("Evidence must be appended in nondecreasing time order")
        vals = [observation.gas, *observation.wind, observation.action.time]
        if not np.all(np.isfinite(vals)):
            raise ValueError("Observation contains a nonfinite value")
        self._history.append(observation)
        self._ids.add(observation.uid)
        self.version += 1

    def extend(self, observations):
        # Atomic validation: an invalid block cannot leave half its evidence behind.
        pending = list(observations)
        probe = object.__new__(EvidenceLedger)
        probe._history = list(self._history)
        probe._ids = set(self._ids)
        probe.version = self.version
        for item in pending:
            probe.append(item)
        self._history, self._ids, self.version = probe._history, probe._ids, probe.version

    @property
    def history(self):
        return list(self._history)

    def __len__(self):
        return len(self._history)


def _probabilities(p, n, name):
    p = np.full(n, 1 / n) if p is None else np.asarray(p, dtype=float)
    if p.shape != (n,) or not np.all(np.isfinite(p)) or np.any(p <= 0):
        raise ValueError(f"{name} must be a finite positive vector of length {n}")
    return p / p.sum()


@dataclass
class ReplayResult:
    source_posterior: np.ndarray
    joint_posterior: np.ndarray
    log_likelihood: np.ndarray
    corrections: np.ndarray
    nominal_log_likelihood: np.ndarray
    source_log_evidence: np.ndarray
    records: list
    variant: str
    model_version: str
    conditional_mechanism_posterior: np.ndarray
    source_log_posterior: np.ndarray

    @property
    def mechanism_posterior(self):
        return self.joint_posterior.sum(axis=0)


class ReplayEngine:
    """Exact finite-mechanism reference and audited suffix replacement.

    `generator.log_prob` must be a normalized causal joint density and must
    mask the mechanism before its onset. Source priors are never replaced by
    the last posterior. This class does not assume independent gas windows.
    """

    def __init__(self, generator, sources, mechanisms, source_prior=None,
                 mechanism_prior=None, model_version="v1", prefix_tolerance=1e-7):
        self.generator = generator
        self.sources = np.asarray(sources, dtype=float)
        self.mechanisms = list(mechanisms)
        if self.sources.ndim != 2 or self.sources.shape[1] != 2 or len(self.sources) == 0:
            raise ValueError("sources must have nonempty shape [N,2]")
        if not self.mechanisms or self.mechanisms[0].kind != "nominal":
            raise ValueError("mechanisms[0] must be nominal")
        self.source_prior = _probabilities(source_prior, len(self.sources), "source prior")
        self.mechanism_prior = _probabilities(mechanism_prior, len(self.mechanisms), "mechanism prior")
        self.model_version = str(model_version)
        self.prefix_tolerance = float(prefix_tolerance)

    def infer(self, history, variant="Bprime"):
        aliases = {"A'": "Aprime", "A'+B": "B", "A'+B'": "Bprime", "exact": "Bprime"}
        variant = aliases.get(variant, variant)
        if variant not in {"Aprime", "B", "Bprime"}:
            raise ValueError("M2 variants are Aprime, B, Bprime; native A is an external PMFS run")
        history = list(history)
        n, ecount = len(self.sources), len(self.mechanisms)
        nominal = self.mechanisms[0]
        base = np.array([self.generator.log_prob(history, s, nominal) for s in self.sources])
        logs = np.repeat(base[:, None], ecount, axis=1)
        records = []
        if variant != "Aprime":
            for j, mechanism in enumerate(self.mechanisms[1:], start=1):
                onset = max(0, min(int(mechanism.onset), len(history)))
                prefix = history[:onset]
                for i, source in enumerate(self.sources):
                    old_prefix = float(self.generator.log_prob(prefix, source, nominal))
                    mode_prefix = float(self.generator.log_prob(prefix, source, mechanism))
                    if abs(old_prefix - mode_prefix) > self.prefix_tolerance:
                        raise ValueError("Mechanism changed pre-onset likelihood; replay contract violated")
                    full_new = float(self.generator.log_prob(history, source, mechanism))
                    old_suffix = base[i] - old_prefix
                    new_suffix = full_new - mode_prefix
                    if variant == "Bprime":
                        logs[i, j] = base[i] - old_suffix + new_suffix
                    else:
                        # Direct diagnostic transfer: the new mode can explain
                        # the newest observation but does not replace old factors.
                        last = max(0, len(history) - 1)
                        prior_new = float(self.generator.log_prob(history[:last], source, mechanism))
                        prior_old = float(self.generator.log_prob(history[:last], source, nominal))
                        logs[i, j] = prior_old + full_new - prior_new
                    records.append({"source_index": i, "mechanism_index": j,
                                    "onset": onset, "suffix_end": len(history),
                                    "removed_log_factor": float(old_suffix),
                                    "replacement_log_factor": float(new_suffix),
                                    "full_recompute_error": float(logs[i, j] - full_new)
                                    if variant == "Bprime" else None})
        if not np.all(np.isfinite(logs)):
            raise ValueError("Nonfinite model likelihood; stop instead of deleting source support")
        log_joint = np.log(self.source_prior)[:, None] + np.log(self.mechanism_prior)[None, :] + logs
        log_joint -= logsumexp(log_joint)
        joint = np.exp(log_joint)
        # A mathematically positive but negligible source can underflow in a
        # displayed probability map. Its mechanism law must remain available
        # for counterevidence planning. Normalize each source's mechanism row
        # directly in log space rather than dividing an underflowed joint row.
        source_log_posterior = logsumexp(log_joint, axis=1)
        conditional_logs = logs + np.log(self.mechanism_prior)[None, :]
        conditional_logs -= logsumexp(conditional_logs, axis=1, keepdims=True)
        conditional_mechanisms = np.exp(conditional_logs)
        # A' has no mechanism identification: its identical likelihood columns
        # intentionally leave the declared mechanism prior unchanged.
        return ReplayResult(joint.sum(axis=1), joint, logs, logs - base[:, None], base,
                            logsumexp(logs + np.log(self.mechanism_prior)[None, :], axis=1),
                            records, variant, self.model_version,
                            conditional_mechanisms, source_log_posterior)

    def infer_budgeted(self, history, diagnosis, rng, draws=4, reference_draws=4,
                       epsilon=0.1, variant="Bprime"):
        """Actually use diagnosis to allocate a finite replay computation budget.

        This is a separate approximation, audited against `infer`. The
        source-normalized output is finite-MC biased; no unbiased posterior
        claim is made. Each raw likelihood is evaluated at most once per
        source/mode in this call. Reference generation cost is also reported.
        """
        if variant not in {"B", "Bprime"} or draws<1:
            raise ValueError("Budgeted inference requires B/Bprime and positive draws")
        history=list(history)
        q=diagnosis.propose(history,self.sources,self.generator,self.mechanisms,rng,
                            draws=reference_draws,source_blind=(variant=="B"),
                            epsilon=epsilon,prior=self.mechanism_prior)
        log_evidence=[];chosen=[];evaluations=0
        nominal=self.mechanisms[0]
        for i,source in enumerate(self.sources):
            indices=rng.choice(len(self.mechanisms),int(draws),p=q[i])
            cache={}
            for j in np.unique(indices):
                mechanism=self.mechanisms[int(j)]
                log_full=float(self.generator.log_prob(history,source,mechanism))
                if variant=="B":
                    last=max(0,len(history)-1)
                    log_full=(float(self.generator.log_prob(history[:last],source,nominal))
                              +log_full-float(self.generator.log_prob(history[:last],source,mechanism)))
                cache[int(j)]=log_full
                evaluations+=1
            summands=np.array([cache[int(j)]+np.log(self.mechanism_prior[j])-np.log(q[i,j])
                                for j in indices])
            log_evidence.append(float(logsumexp(summands)-np.log(draws)))
            chosen.append(indices.tolist())
        logs=np.log(self.source_prior)+np.asarray(log_evidence)
        source_log_posterior=logs-logsumexp(logs)
        posterior=np.exp(source_log_posterior)
        return {"source_posterior":posterior,"source_log_evidence":np.asarray(log_evidence),
                "source_log_posterior":source_log_posterior,
                "proposal":q,"sampled_mechanisms":chosen,"likelihood_evaluations":evaluations,
                "reference_trajectories":len(self.sources)*reference_draws,
                "full_enumeration_evaluations":len(self.sources)*len(self.mechanisms),
                "variant":variant,"model_version":self.model_version,
                "status":"diagnostic_proposal_used_with_pi_over_q_correction"}


def defensive_importance(log_likelihood, prior, proposal, draws, rng, epsilon=0.1):
    """Unbiased *unnormalized* evidence MC estimate, represented in log space.

    Its normalized posterior is not finite-sample unbiased. `proposal` may
    depend on the observations; pi/q removes that dependence from the target.
    """
    logs = np.asarray(log_likelihood, dtype=float)
    prior = _probabilities(prior, len(logs), "prior")
    proposal = _probabilities(proposal, len(logs), "proposal")
    if not 0 < epsilon <= 1 or draws < 1:
        raise ValueError("epsilon must be in (0,1] and draws positive")
    q = (1 - epsilon) * proposal + epsilon * prior
    indices = rng.choice(len(logs), int(draws), p=q)
    weights = np.log(prior[indices]) - np.log(q[indices])
    result = logsumexp(logs[indices] + weights) - np.log(draws)
    return {"log_evidence": float(result), "indices": indices,
            "proposal": q, "max_importance_weight": float(np.exp(weights).max()),
            "weight_bound": 1.0 / epsilon}
