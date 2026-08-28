#!/usr/bin/env python3
"""Engineering-only fixed-shape throughput preflight for the frozen V3 TCN."""

from __future__ import annotations

import time

import torch
from torch.nn import functional as F

from pf_dei_v3_causal_tcn import INPUT_DIM, initialize_frozen_model


def main() -> int:
    if not torch.cuda.is_available():
        raise SystemExit("PF_DEI_V3_CUDA_UNAVAILABLE")
    device = torch.device("cuda")
    model = initialize_frozen_model(1701).to(device).train()
    features = torch.randn(64, 1684, INPUT_DIM, device=device)
    mask = torch.ones(64, 1684, dtype=torch.bool, device=device)
    target = torch.cat((torch.ones(32, device=device), torch.zeros(32, device=device)))
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    torch.cuda.reset_peak_memory_stats()
    elapsed = []
    for _ in range(3):
        torch.cuda.synchronize()
        start = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        loss = F.binary_cross_entropy_with_logits(model(features, mask), target)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        torch.cuda.synchronize()
        elapsed.append(time.perf_counter() - start)
    peak = torch.cuda.max_memory_allocated() / (1024 ** 3)
    print(
        "PF_DEI_V3_TCN_GPU_PREFLIGHT=PASS "
        f"device={torch.cuda.get_device_name(0)!r} batch=64 length=1684 "
        f"median_step_s={sorted(elapsed)[1]:.6f} peak_allocated_gib={peak:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
