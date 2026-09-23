#!/usr/bin/env python3
"""M6 G0.6 probe: source-injection adapter for GeoPT without changing its 11-D input.

Design goals
------------
1. Preserve GeoPT's pretrained preprocess layer exactly.
2. Encode candidate source only AFTER the pretrained environment projection.
3. Use a localized, PMFS-native source injection feature.
4. Keep the adapter tiny relative to the 8-layer GeoPT backbone.
5. Allow zero-initialized source gating so the starting function is the pretrained environment model.

This is an interface/algebra probe. It does not use source truth.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class SourceInjectionAdapter(nn.Module):
    """Candidate-source adapter injected after GeoPT's input projection."""

    def __init__(self, hidden_dim: int = 256, adapter_hidden: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, adapter_hidden),
            nn.SiLU(),
            nn.Linear(adapter_hidden, hidden_dim),
        )
        self.gate = nn.Parameter(torch.zeros(()))

    def source_features(
        self,
        pos: torch.Tensor,
        source_xyz: torch.Tensor,
        sigma_s: float,
    ) -> torch.Tensor:
        if source_xyz.ndim == 2:
            source_xyz = source_xyz[:, None, :]
        if source_xyz.shape[-1] != 3:
            raise ValueError("source_xyz must end in 3 coordinates")
        if sigma_s <= 0:
            raise ValueError("sigma_s must be > 0")

        delta = pos - source_xyz
        d2 = torch.sum(delta * delta, dim=-1, keepdim=True)
        q = torch.exp(-0.5 * d2 / (sigma_s * sigma_s))
        return torch.cat([q, q * delta], dim=-1)

    def forward(
        self,
        pos: torch.Tensor,
        source_xyz: torch.Tensor,
        sigma_s: float,
    ) -> torch.Tensor:
        r = self.source_features(pos, source_xyz, sigma_s)
        return self.gate * self.net(r)


class GeoPTSourceConditionedWrapper(nn.Module):
    """Wrap an official GeoPT Transolver without changing raw input width.

    Expected GeoPT members:
      model.preprocess
      model.placeholder
      model.blocks
      model.args
    """

    def __init__(
        self,
        geopt_model: nn.Module,
        adapter_hidden: int = 64,
    ):
        super().__init__()
        self.geopt = geopt_model
        hidden_dim = int(geopt_model.args.n_hidden)
        self.source_adapter = SourceInjectionAdapter(
            hidden_dim=hidden_dim,
            adapter_hidden=adapter_hidden,
        )

    def forward(
        self,
        pos: torch.Tensor,
        fx11: torch.Tensor,
        source_xyz: torch.Tensor,
        sigma_s: float,
    ) -> torch.Tensor:
        if pos.shape[-1] != 3:
            raise ValueError("pos must be [B,N,3]")
        if fx11.shape[-1] != 11:
            raise ValueError(
                "fx11 must be the original GeoPT-compatible 11-D "
                "geometry+dynamics feature tensor"
            )

        # Official GeoPT preprocessing receives xyz plus the remaining
        # non-coordinate pointwise features. The gas contract is:
        # pos = features[..., :3], env_fx = features[..., 3:].
        env_fx = fx11[..., 3:]

        h = self.geopt.preprocess(torch.cat([pos, env_fx], dim=-1))
        h = h + self.geopt.placeholder[None, None, :]
        h = h + self.source_adapter(pos, source_xyz, sigma_s)

        for block in self.geopt.blocks:
            h = block(h)
        return h


def adapter_parameter_count(hidden_dim: int = 256, adapter_hidden: int = 64) -> int:
    adapter = SourceInjectionAdapter(hidden_dim, adapter_hidden)
    return sum(p.numel() for p in adapter.parameters())


def gaussian_sigma_from_candidate_cell(cell_size: float, factor: float = 0.5) -> float:
    """Source-blind source-kernel scale tied to candidate-cell geometry."""
    if cell_size <= 0 or factor <= 0:
        raise ValueError("cell_size and factor must be > 0")
    return float(cell_size) * float(factor)


def _self_test() -> None:
    B, N = 2, 17
    pos = torch.randn(B, N, 3)
    source = torch.randn(B, 3)
    adapter = SourceInjectionAdapter(hidden_dim=256, adapter_hidden=64)

    z = adapter(pos, source, sigma_s=0.5)
    assert z.shape == (B, N, 256)

    # Zero-init gate must make initial source perturbation exactly zero.
    assert torch.allclose(z, torch.zeros_like(z))

    # Source feature is largest near the candidate source.
    p = torch.tensor([[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]])
    s = torch.tensor([[0.0, 0.0, 0.0]])
    f = adapter.source_features(p, s, sigma_s=0.5)
    assert float(f[0, 0, 0]) > float(f[0, 1, 0])

    n = adapter_parameter_count()
    assert n == 16961, n


if __name__ == "__main__":
    _self_test()
    n = adapter_parameter_count()
    geopt_params = 3_865_673
    print("M6 source-injection adapter F0: PASS")
    print(f"adapter_params={n}")
    print(f"geopt_reference_params={geopt_params}")
    print(f"adapter_fraction_pct={100*n/geopt_params:.6f}")
    print("zero_init_gate=True")
