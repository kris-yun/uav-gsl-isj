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
      [log1p_gas, sensor_state, wind_u, wind_v, pose_x, pose_y,
       time_from_start_s, in_measurement_block]

    Runtime candidates are arbitrary XY coordinates from the current map. No
    House/source/member identity is represented in the model input.
    """

    def __init__(self, d_model: int = 96, nhead: int = 4, layers: int = 3,
                 z_source_dim: int = 48, z_nuisance_dim: int = 32):
        super().__init__()
        if d_model % nhead:
            raise ValueError("PICR_DMODEL_HEAD_MISMATCH")
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
        # token state + candidate-relative causal geometry [dx,dy,dist,along,cross]
        self.evidence = nn.Sequential(
            nn.Linear(d_model + 5, d_model), nn.SiLU(),
            nn.Linear(d_model, d_model // 2), nn.SiLU(), nn.Linear(d_model // 2, 1),
        )

    @staticmethod
    def _causal_mask(t: int, device) -> torch.Tensor:
        return torch.triu(torch.ones(t, t, dtype=torch.bool, device=device), diagonal=1)

    @staticmethod
    def _masked_mean(x: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        w = valid.to(x.dtype).unsqueeze(-1)
        denom = w.sum(dim=1).clamp_min(1.0)
        return (x * w).sum(dim=1) / denom

    def forward(self, history: torch.Tensor, candidate_xy: torch.Tensor,
                valid_time: torch.Tensor,
                transport_support: torch.Tensor | None = None) -> PICROutput:
        if history.ndim != 3 or history.shape[-1] != 8:
            raise ValueError("PICR_HISTORY_SHAPE")
        if candidate_xy.ndim != 3 or candidate_xy.shape[-1] != 2:
            raise ValueError("PICR_CANDIDATE_SHAPE")
        b, t, _ = history.shape
        if valid_time.shape != (b, t) or valid_time.dtype != torch.bool:
            raise ValueError("PICR_VALID_TIME_SHAPE")
        if candidate_xy.shape[0] != b:
            raise ValueError("PICR_BATCH_MISMATCH")
        n = candidate_xy.shape[1]
        if transport_support is not None and transport_support.shape != (b, n, t):
            raise ValueError("PICR_SUPPORT_SHAPE")

        h = self.response_encoder(history[..., :2]) + self.context_encoder(history[..., 2:])
        h = self.temporal(
            h, mask=self._causal_mask(t, h.device),
            src_key_padding_mask=~valid_time,
        )
        pooled = self._masked_mean(h, valid_time)
        z_s = self.source_proj(pooled)
        z_n = self.nuisance_proj(pooled)
        # log-amplitude location + unconstrained scale parameter; trainer applies softplus to scale.
        amp = self.amplitude_head(pooled)

        pose = history[..., 4:6]
        wind = history[..., 2:4]
        delta = pose[:, None, :, :] - candidate_xy[:, :, None, :]
        dist = torch.linalg.vector_norm(delta, dim=-1, keepdim=True)
        speed = torch.linalg.vector_norm(wind, dim=-1, keepdim=True).clamp_min(1e-6)
        unit = wind / speed
        along = (delta * unit[:, None, :, :]).sum(dim=-1, keepdim=True)
        cross = (
            delta[..., 0:1] * unit[:, None, :, 1:2]
            - delta[..., 1:2] * unit[:, None, :, 0:1]
        ).abs()
        rel = torch.cat([delta, dist, along, cross], dim=-1)
        ht = h[:, None, :, :].expand(-1, n, -1, -1)
        ev = self.evidence(torch.cat([ht, rel], dim=-1)).squeeze(-1)

        support = valid_time[:, None, :].expand(-1, n, -1)
        if transport_support is not None:
            support = support & transport_support
        count = support.sum(dim=-1)
        # Mean evidence avoids rewarding a candidate merely because it has more
        # supported samples. Unsupported candidates get an explicit finite floor.
        ev_sum = (ev * support.to(ev.dtype)).sum(dim=-1)
        logits = ev_sum / count.clamp_min(1).to(ev.dtype)
        logits = torch.where(count > 0, logits, torch.full_like(logits, -1.0e4))
        posterior = torch.softmax(logits, dim=-1)
        return PICROutput(logits, posterior, z_s, z_n, amp, count)


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
