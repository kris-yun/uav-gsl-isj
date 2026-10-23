"""Small CPU trainable adaptation of the CDN differential-encoder operation.

This is not a reproduction of the authors' FCI/axial-attention architecture.
The transferred operator is E(D_observed)-E(D_reference) with shared learned
parameters, followed by mechanism classification. Raw diagnostic probabilities
are proposals, never likelihood factors.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp


def history_descriptor(history):
    """21 bounded dynamic channel statistics; no unobserved map cells filled in.

    Channels are wind-x, wind-y, gas. Inputs are a complete measured or sampled
    history. Empty histories have no diagnosis and are represented by zeros.
    """
    if not history:
        return np.zeros(21)
    x = np.array([[*o.wind, o.gas] for o in history], dtype=float)
    mean, std = x.mean(axis=0), x.std(axis=0)
    centered = x - mean
    cov = centered.T @ centered / max(1, len(x))
    corr = cov / np.maximum(std[:, None] * std[None, :], 1e-6)
    lag = (x[1:] * x[:-1]).mean(axis=0) if len(x) > 1 else np.zeros(3)
    increment = np.abs(np.diff(x, axis=0)).mean(axis=0) if len(x) > 1 else np.zeros(3)
    return np.tanh(np.concatenate([mean, std, corr.ravel(), lag, increment]))


def diagnostic_pairs(history, sources, generator, nominal_mechanism, rng, draws=8,
                     source_blind=False):
    """Actual vs legal source-conditioned reference descriptors, shape [N,21].

    Source-blind B uses one reference averaged across the source registry;
    B' retains a separate reference per competing source. Neither consumes
    the true source label or future observations at inference.
    """
    if draws < 1:
        raise ValueError("draws must be positive")
    actual = history_descriptor(history)
    actions = [o.action for o in history]
    refs = []
    for source in sources:
        samples = [history_descriptor(generator.sample_future([], actions, source,
                       nominal_mechanism, rng)) for _ in range(draws)]
        refs.append(np.mean(samples, axis=0))
    refs = np.asarray(refs)
    if source_blind:
        refs[:] = refs.mean(axis=0)
    return np.repeat(actual[None, :], len(refs), axis=0), refs


class DifferentialDiagnoser:
    """Trainable two-branch shared tanh encoder with an exact NumPy gradient."""

    def __init__(self, n_classes, input_dim=21, hidden=16, seed=0):
        if n_classes < 2:
            raise ValueError("At least nominal and one mechanism class are required")
        self.n_classes, self.input_dim, self.hidden = int(n_classes), int(input_dim), int(hidden)
        rng = np.random.default_rng(seed)
        self.W = rng.normal(0, 0.1, (input_dim, hidden))
        self.b = np.zeros(hidden)
        self.V = rng.normal(0, 0.1, (hidden, n_classes))
        self.c = np.zeros(n_classes)
        self.training_receipt = None
        self.catalog_json = None
        self.catalog_hash = None

    @staticmethod
    def _catalog_identity(mechanisms):
        data=[{"kind":str(e.kind),"onset":int(e.onset),
               "duration":None if e.duration is None else int(e.duration),
               "magnitude":float(e.magnitude)} for e in mechanisms]
        payload=json.dumps(data,sort_keys=True,separators=(",",":"),allow_nan=False)
        return payload,hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def bind_catalog(self, mechanisms):
        """Bind output-label identity, including physical values and order.

        Equal class counts do not make different mechanism catalogues
        interchangeable. Rebinding a trained checkpoint is prohibited.
        """
        if len(mechanisms)!=self.n_classes:
            raise ValueError("Mechanism catalogue length differs from diagnosis outputs")
        payload,digest=self._catalog_identity(mechanisms)
        if self.catalog_hash is not None and self.catalog_hash!=digest:
            raise ValueError("BLOCKED: diagnosis catalogue cannot be rebound to different mechanisms")
        self.catalog_json,self.catalog_hash=payload,digest
        return self

    def _pack(self):
        return np.concatenate([self.W.ravel(), self.b, self.V.ravel(), self.c])

    def _unpack(self, theta):
        d, h, k = self.input_dim, self.hidden, self.n_classes
        p = d * h
        self.W = theta[:p].reshape(d, h)
        self.b = theta[p:p+h]
        self.V = theta[p+h:p+h+h*k].reshape(h, k)
        self.c = theta[p+h+h*k:]

    def predict_proba(self, observed, reference):
        a, b = np.asarray(observed, float), np.asarray(reference, float)
        if a.shape != b.shape or a.shape[-1] != self.input_dim:
            raise ValueError("Observed and reference feature shapes must agree")
        delta = np.tanh(a @ self.W + self.b) - np.tanh(b @ self.W + self.b)
        logits = delta @ self.V + self.c
        return np.exp(logits - logsumexp(logits, axis=-1, keepdims=True))

    def fit(self, observed, reference, labels, max_iter=120, l2=1e-3):
        a, b, y = np.asarray(observed, float), np.asarray(reference, float), np.asarray(labels, int)
        if a.shape != b.shape or a.ndim != 2 or a.shape[1] != self.input_dim:
            raise ValueError("Training arrays must have shape [examples,input_dim]")
        if y.shape != (len(a),) or np.any(y < 0) or np.any(y >= self.n_classes):
            raise ValueError("Invalid class labels")
        target = np.eye(self.n_classes)[y]
        def objective(theta):
            self._unpack(theta)
            ha, hb = np.tanh(a @ self.W + self.b), np.tanh(b @ self.W + self.b)
            delta = ha - hb
            logits = delta @ self.V + self.c
            probs = np.exp(logits - logsumexp(logits, axis=1, keepdims=True))
            loss = np.mean(logsumexp(logits, axis=1) - logits[np.arange(len(y)), y])
            loss += 0.5 * l2 * (np.sum(self.W**2) + np.sum(self.V**2))
            dl = (probs - target) / len(y)
            dV, dc = delta.T @ dl + l2 * self.V, dl.sum(axis=0)
            dh = dl @ self.V.T
            da, db = dh * (1 - ha**2), -dh * (1 - hb**2)
            dW, d_b = a.T @ da + b.T @ db + l2 * self.W, (da+db).sum(axis=0)
            return float(loss), np.concatenate([dW.ravel(), d_b, dV.ravel(), dc])
        theta = self._pack()
        initial = objective(theta)[0]
        result = minimize(objective, theta, jac=True, method="L-BFGS-B",
                          options={"maxiter": int(max_iter), "ftol": 1e-9})
        self._unpack(result.x)
        self.training_receipt = {"initial_loss": initial, "final_loss": float(result.fun),
                                 "iterations": int(result.nit), "optimizer_success": bool(result.success),
                                 "examples": len(y), "source": "observed/reference mechanism supervision"}
        return self.training_receipt

    def propose(self, history, sources, generator, mechanisms, rng, draws=8,
                source_blind=False, epsilon=0.1, prior=None):
        if len(mechanisms) != self.n_classes:
            raise ValueError("Diagnosis class order must match mechanism catalogue")
        _,expected=self._catalog_identity(mechanisms)
        if self.catalog_hash is None or expected!=self.catalog_hash:
            raise ValueError("BLOCKED: diagnosis checkpoint mechanism identity/order differs or is unbound")
        actual, reference = diagnostic_pairs(history, sources, generator, mechanisms[0], rng,
                                             draws=draws, source_blind=source_blind)
        raw = self.predict_proba(actual, reference)
        prior = np.ones(self.n_classes)/self.n_classes if prior is None else np.asarray(prior, float)
        if not 0 < epsilon <= 1 or np.any(prior <= 0):
            raise ValueError("Defensive proposal must preserve all mechanism support")
        prior /= prior.sum()
        return (1-epsilon)*raw + epsilon*prior[None, :]

    def save(self, path):
        if self.catalog_hash is None:
            raise ValueError("BLOCKED: bind_catalog before saving a mechanism classifier")
        np.savez(Path(path), W=self.W, b=self.b, V=self.V, c=self.c,
                 catalog_json=self.catalog_json,catalog_hash=self.catalog_hash,format_version=2)

    @classmethod
    def load(cls, path):
        with np.load(Path(path), allow_pickle=False) as f:
            if "catalog_json" not in f or "catalog_hash" not in f:
                raise ValueError("BLOCKED: legacy diagnosis checkpoint lacks mechanism identity")
            out = cls(f["V"].shape[1], f["W"].shape[0], f["W"].shape[1])
            out.W, out.b, out.V, out.c = (f[k].copy() for k in ("W", "b", "V", "c"))
            payload=str(f["catalog_json"].item());digest=str(f["catalog_hash"].item())
            if hashlib.sha256(payload.encode("utf-8")).hexdigest()!=digest:
                raise ValueError("BLOCKED: diagnosis catalogue metadata hash mismatch")
            if len(json.loads(payload))!=out.n_classes:
                raise ValueError("BLOCKED: diagnosis catalogue metadata shape mismatch")
            out.catalog_json,out.catalog_hash=payload,digest
        return out
