from __future__ import annotations

from dataclasses import dataclass
import torch
from torch import nn
import torch.nn.functional as F


@dataclass
class PICROutput:
    source_logits: torch.Tensor
    source_posterior: torch.Tensor
    source_representation: torch.Tensor
    nuisance_representation: torch.Tensor
    amplitude_state: torch.Tensor
    candidate_support: torch.Tensor
    valid_source_belief: torch.Tensor
    abstain: torch.Tensor


class GradientReversal(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x: torch.Tensor, scale: float):
        ctx.scale = float(scale)
        return x.view_as(x)

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor):
        return -ctx.scale * grad_output, None


def grad_reverse(x: torch.Tensor, scale: float = 1.0) -> torch.Tensor:
    return GradientReversal.apply(x, scale)


class PICRModel(nn.Module):
    """Perturbation-Invariant Causal Representation research model.

    History feature contract (last dimension = 8):
      [log1p_gas, gas_ema_aux, wind_u, wind_v, pose_x, pose_y,
       time_from_start_s, in_measurement_block]

    ``gas_ema_aux`` is explicitly an observation-derived auxiliary statistic. It
    is *not* an audited FOPDT internal sensor state. Formal controlled data may
    replace this channel only under a versioned typed input contract.

    Runtime candidates are arbitrary XY coordinates from the current map. No
    House/source/member identity is represented in the model input.

    Load-bearing source-path rule:
      - all history-dependent information (gas, wind, pose, time) must first be
        compressed into zS;
      - candidate scoring may use zS and candidate-static coordinates/validity;
      - it may not re-read history-dependent candidate-relative summaries.

    Candidate-only bias is removed exactly by subtracting the same evidence
    network evaluated at zS=0. Consequently, for a fixed candidate set, a
    posterior that changes with history must change through zS.
    """

    def __init__(self, d_model: int = 96, nhead: int = 4, layers: int = 3,
                 z_source_dim: int = 48, z_nuisance_dim: int = 32):
        super().__init__()
        if d_model % nhead:
            raise ValueError("PICR_DMODEL_HEAD_MISMATCH")
        self.z_source_dim = int(z_source_dim)
        self.response_encoder = nn.Sequential(
            nn.Linear(2, d_model), nn.SiLU(), nn.LayerNorm(d_model),
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(6, d_model), nn.SiLU(), nn.LayerNorm(d_model),
        )
        block = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=4 * d_model,
            dropout=0.0, activation="gelu", batch_first=True, norm_first=True,
        )
        self.temporal = nn.TransformerEncoder(block, num_layers=layers)
        self.source_proj = nn.Sequential(
            nn.Linear(d_model, z_source_dim), nn.LayerNorm(z_source_dim)
        )
        self.nuisance_proj = nn.Sequential(
            nn.Linear(d_model, z_nuisance_dim), nn.LayerNorm(z_nuisance_dim)
        )
        self.amplitude_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2), nn.SiLU(), nn.Linear(d_model // 2, 2)
        )
        self.candidate_encoder = nn.Sequential(
            nn.Linear(2, d_model // 2), nn.SiLU(), nn.LayerNorm(d_model // 2)
        )
        self.evidence = nn.Sequential(
            nn.Linear(z_source_dim + d_model // 2, d_model), nn.SiLU(),
            nn.Linear(d_model, d_model // 2), nn.SiLU(), nn.Linear(d_model // 2, 1),
        )

    @staticmethod
    def _causal_mask(t: int, device) -> torch.Tensor:
        return torch.triu(
            torch.ones(t, t, dtype=torch.bool, device=device), diagonal=1
        )

    @staticmethod
    def _validate_prefix_mask(valid: torch.Tensor) -> None:
        """Require right padding: True...True, False...False for every row.

        Left padding plus a causal mask can create fully-masked query rows on
        some Torch versions. We fail closed instead of accepting version-
        dependent NaN behaviour.
        """
        if valid.ndim != 2 or valid.dtype != torch.bool:
            raise ValueError("PICR_VALID_TIME_SHAPE")
        if not bool(valid.any(dim=1).all()):
            raise ValueError("PICR_EMPTY_HISTORY")
        # A True after the first False means the mask is not a valid prefix.
        seen_false = (~valid).cumsum(dim=1) > 0
        if bool((seen_false & valid).any()):
            raise ValueError("PICR_VALID_TIME_NOT_PREFIX_RIGHT_PAD_REQUIRED")

    @staticmethod
    def _masked_mean(x: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        w = valid.to(x.dtype).unsqueeze(-1)
        denom = w.sum(dim=1).clamp_min(1.0)
        return (x * w).sum(dim=1) / denom

    def forward(self, history: torch.Tensor, candidate_xy: torch.Tensor,
                valid_time: torch.Tensor,
                candidate_valid: torch.Tensor | None = None) -> PICROutput:
        if history.ndim != 3 or history.shape[-1] != 8:
            raise ValueError("PICR_HISTORY_SHAPE")
        if candidate_xy.ndim != 3 or candidate_xy.shape[-1] != 2:
            raise ValueError("PICR_CANDIDATE_SHAPE")
        b, t, _ = history.shape
        if valid_time.shape != (b, t):
            raise ValueError("PICR_VALID_TIME_SHAPE")
        self._validate_prefix_mask(valid_time)
        if candidate_xy.shape[0] != b:
            raise ValueError("PICR_BATCH_MISMATCH")
        n = candidate_xy.shape[1]
        if n <= 0:
            raise ValueError("PICR_EMPTY_CANDIDATE_DOMAIN")
        if candidate_valid is None:
            candidate_valid = torch.ones(
                (b, n), dtype=torch.bool, device=candidate_xy.device
            )
        if candidate_valid.shape != (b, n) or candidate_valid.dtype != torch.bool:
            raise ValueError("PICR_CANDIDATE_VALID_SHAPE")

        h = self.response_encoder(history[..., :2]) + self.context_encoder(history[..., 2:])
        h = self.temporal(
            h, mask=self._causal_mask(t, h.device),
            src_key_padding_mask=~valid_time,
        )
        if not bool(torch.isfinite(h[valid_time]).all()):
            raise RuntimeError("PICR_NONFINITE_TEMPORAL_STATE")
        pooled = self._masked_mean(h, valid_time)
        z_s = self.source_proj(pooled)
        z_n = self.nuisance_proj(pooled)
        amp = self.amplitude_head(pooled)
        if not bool(torch.isfinite(z_s).all()):
            raise RuntimeError("PICR_NONFINITE_SOURCE_REPRESENTATION")

        cand = self.candidate_encoder(candidate_xy)
        zs = z_s[:, None, :].expand(-1, n, -1)
        zeros = torch.zeros_like(zs)
        # Exact subtraction removes any candidate-only score path. Candidate
        # coordinates remain necessary for localization, but they cannot react
        # to gas/wind/pose unless that information first changes zS.
        raw = self.evidence(torch.cat([zs, cand], dim=-1)).squeeze(-1)
        raw_zero = self.evidence(torch.cat([zeros, cand], dim=-1)).squeeze(-1)
        logits = raw - raw_zero

        has_candidate = candidate_valid.any(dim=-1)
        masked_logits = torch.where(
            candidate_valid, logits, torch.full_like(logits, -1.0e9)
        )
        # If no candidate is valid, return an explicitly abstaining uniform
        # distribution rather than silently presenting it as a valid belief.
        masked_logits = torch.where(
            has_candidate[:, None], masked_logits, torch.zeros_like(masked_logits)
        )
        posterior = torch.softmax(masked_logits, dim=-1)
        if not bool(torch.isfinite(posterior).all()):
            raise RuntimeError("PICR_NONFINITE_POSTERIOR")

        support = candidate_valid.to(torch.int64)
        valid_belief = has_candidate
        abstain = ~has_candidate
        return PICROutput(
            masked_logits, posterior, z_s, z_n, amp, support,
            valid_belief, abstain,
        )


class PICRNuisanceAdversary(nn.Module):
    """Training-only nuisance leakage adversary; never a runtime input."""

    def __init__(self, z_dim: int, nuisance_classes: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(z_dim, 64), nn.SiLU(), nn.Linear(64, nuisance_classes)
        )

    def forward(self, z_source: torch.Tensor,
                reversal_scale: float = 1.0) -> torch.Tensor:
        return self.net(grad_reverse(z_source, reversal_scale))


def picr_pair_losses(out_a: PICROutput, out_b: PICROutput,
                     same_source: torch.Tensor,
                     margin: float = 1.0) -> dict[str, torch.Tensor]:
    """Causal pair losses independent of House identity.

    same_source=True pairs should be invariant under nuisance interventions;
    same_source=False matched-context source interventions must remain separated.
    """
    if same_source.dtype != torch.bool or same_source.ndim != 1:
        raise ValueError("PICR_PAIR_LABEL_SHAPE")
    d = torch.linalg.vector_norm(
        out_a.source_representation - out_b.source_representation, dim=-1
    )
    inv = torch.where(same_source, d.square(), torch.zeros_like(d))
    sep = torch.where(
        ~same_source, F.relu(margin - d).square(), torch.zeros_like(d)
    )
    same_den = same_source.sum().clamp_min(1)
    diff_den = (~same_source).sum().clamp_min(1)
    return {
        "invariance": inv.sum() / same_den,
        "source_separation": sep.sum() / diff_den,
    }
