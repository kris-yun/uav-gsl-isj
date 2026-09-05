from __future__ import annotations

from dataclasses import dataclass
import torch
from torch import nn
import torch.nn.functional as F


@dataclass
class CPOOutput:
    hazards: torch.Tensor
    first_hit_prob: torch.Tensor
    committor: torch.Tensor
    logppm_mean: torch.Tensor
    logppm_scale: torch.Tensor


def hazards_to_first_passage_torch(h: torch.Tensor) -> torch.Tensor:
    if h.ndim != 2:
        raise ValueError("CPO_HAZARD_SHAPE")
    if torch.any((h < 0) | (h > 1) | ~torch.isfinite(h)):
        raise ValueError("CPO_HAZARD_RANGE")
    one_minus = 1.0 - h
    prefix = torch.cat(
        [torch.ones_like(h[:, :1]), torch.cumprod(one_minus[:, :-1], dim=1)], dim=1
    )
    hit = prefix * h
    no_hit = torch.prod(one_minus, dim=1, keepdim=True)
    law = torch.cat([hit, no_hit], dim=1)
    return law / law.sum(dim=1, keepdim=True).clamp_min(1e-12)


class CPOResidualOperator(nn.Module):
    """Geometry/context-conditioned residual operator around a physical prior.

    step_features are causal/context features for a known candidate route under
    do(route). They must not contain source truth, future gas or future wind.
    `prior_hazard_logit` and `prior_logppm_mean` come from a named causal prior
    such as local-persistence-broadcast + V2 Transport/FOPDT.
    """

    def __init__(self, feature_dim: int, d_model: int = 96,
                 nhead: int = 4, layers: int = 3):
        super().__init__()
        if d_model % nhead:
            raise ValueError("CPO_DMODEL_HEAD_MISMATCH")
        self.in_proj = nn.Sequential(
            nn.Linear(feature_dim + 2, d_model), nn.SiLU(), nn.LayerNorm(d_model)
        )
        block = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=4 * d_model,
            dropout=0.0, activation="gelu", batch_first=True, norm_first=True,
        )
        self.operator = nn.TransformerEncoder(block, num_layers=layers)
        self.hazard_delta = nn.Linear(d_model, 1)
        self.mean_delta = nn.Linear(d_model, 1)
        self.scale_head = nn.Linear(d_model, 1)

    def forward(self, step_features: torch.Tensor,
                prior_hazard_logit: torch.Tensor,
                prior_logppm_mean: torch.Tensor,
                valid_step: torch.Tensor | None = None) -> CPOOutput:
        if step_features.ndim != 3:
            raise ValueError("CPO_FEATURE_SHAPE")
        b, h, _ = step_features.shape
        if prior_hazard_logit.shape != (b, h) or prior_logppm_mean.shape != (b, h):
            raise ValueError("CPO_PRIOR_SHAPE")
        if valid_step is not None and (
            valid_step.shape != (b, h) or valid_step.dtype != torch.bool
        ):
            raise ValueError("CPO_VALID_SHAPE")
        x = torch.cat(
            [
                step_features,
                prior_hazard_logit.unsqueeze(-1),
                prior_logppm_mean.unsqueeze(-1),
            ],
            dim=-1,
        )
        x = self.in_proj(x)
        # The whole route is a known intervention at decision time, so route
        # context can be bidirectional; no future observation is an input.
        x = self.operator(
            x, src_key_padding_mask=(~valid_step if valid_step is not None else None)
        )
        hazards = torch.sigmoid(
            prior_hazard_logit + self.hazard_delta(x).squeeze(-1)
        )
        if valid_step is not None:
            hazards = torch.where(valid_step, hazards, torch.zeros_like(hazards))
        law = hazards_to_first_passage_torch(hazards)
        committor = torch.cumsum(law[:, :-1], dim=1)
        mean = prior_logppm_mean + self.mean_delta(x).squeeze(-1)
        scale = F.softplus(self.scale_head(x).squeeze(-1)) + 1e-4
        return CPOOutput(hazards, law, committor, mean, scale)


def cpo_first_passage_nll(out: CPOOutput,
                          first_hit_index: torch.Tensor) -> torch.Tensor:
    """first_hit_index in [0,H], where H denotes no-hit-by-horizon."""
    if (
        first_hit_index.ndim != 1
        or first_hit_index.shape[0] != out.first_hit_prob.shape[0]
    ):
        raise ValueError("CPO_TARGET_SHAPE")
    h = out.first_hit_prob.shape[1] - 1
    if torch.any((first_hit_index < 0) | (first_hit_index > h)):
        raise ValueError("CPO_TARGET_RANGE")
    p = out.first_hit_prob.gather(
        1, first_hit_index.long().unsqueeze(1)
    ).squeeze(1).clamp_min(1e-12)
    return -torch.log(p).mean()


def cpo_brier(out: CPOOutput,
              first_hit_index: torch.Tensor) -> torch.Tensor:
    target = F.one_hot(
        first_hit_index.long(), num_classes=out.first_hit_prob.shape[1]
    ).to(out.first_hit_prob.dtype)
    return (out.first_hit_prob - target).square().sum(dim=1).mean()
