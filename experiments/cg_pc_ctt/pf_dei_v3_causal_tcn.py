#!/usr/bin/env python3
"""Frozen PF-DEI-SR V3 causal-TCN ratio-estimator architecture."""

from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

from pf_dei_v3_schema import DILATIONS, INPUT_DIM


class CausalResidualBlock(nn.Module):
    def __init__(self, width: int, dilation: int, kernel_size: int = 5):
        super().__init__()
        self.left_padding = dilation * (kernel_size - 1)
        self.conv = nn.Conv1d(width, width, kernel_size, dilation=dilation)
        self.norm = nn.LayerNorm(width)
        self.activation = nn.GELU()

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        # [batch,time,width] -> causal convolution with no access to t+1:.
        channel_first = values.transpose(1, 2)
        filtered = self.conv(F.pad(channel_first, (self.left_padding, 0))).transpose(1, 2)
        return values + self.activation(self.norm(filtered))


class PFDEIV3CausalTCN(nn.Module):
    def __init__(self, input_dim: int = INPUT_DIM, width: int = 64):
        super().__init__()
        self.input_dim = input_dim
        self.width = width
        self.sample_encoder = nn.Sequential(nn.Linear(input_dim, width), nn.GELU())
        self.blocks = nn.ModuleList(CausalResidualBlock(width, dilation) for dilation in DILATIONS)
        self.head = nn.Sequential(nn.Linear(2 * width, 64), nn.GELU(), nn.Linear(64, 1))

    def encode_sequence(self, features: torch.Tensor) -> torch.Tensor:
        if features.ndim != 3 or features.shape[-1] != self.input_dim:
            raise ValueError("PF_DEI_V3_TCN_BAD_FEATURE_SHAPE")
        hidden = self.sample_encoder(features)
        for block in self.blocks:
            hidden = block(hidden)
        return hidden

    def forward(self, features: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        if mask.ndim != 2 or mask.shape != features.shape[:2]:
            raise ValueError("PF_DEI_V3_TCN_BAD_MASK_SHAPE")
        if not mask.dtype == torch.bool:
            raise ValueError("PF_DEI_V3_TCN_MASK_NOT_BOOL")
        lengths = mask.sum(dim=1)
        if torch.any(lengths <= 0):
            raise ValueError("PF_DEI_V3_TCN_EMPTY_SEQUENCE")
        hidden = self.encode_sequence(features)
        weights = mask.unsqueeze(-1).to(hidden.dtype)
        pooled = (hidden * weights).sum(dim=1) / lengths.unsqueeze(-1).to(hidden.dtype)
        final = hidden[torch.arange(hidden.shape[0], device=hidden.device), lengths - 1]
        return self.head(torch.cat((pooled, final), dim=-1)).squeeze(-1)


def initialize_frozen_model(seed: int) -> PFDEIV3CausalTCN:
    if seed not in (1701, 1702, 1703):
        raise ValueError("PF_DEI_V3_UNAUTHORIZED_MODEL_SEED")
    torch.manual_seed(seed)
    return PFDEIV3CausalTCN()
