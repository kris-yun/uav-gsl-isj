#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from pf_dei_v3_causal_tcn import initialize_frozen_model
from train_pf_dei_v3_nre import TrainingData, configure_determinism


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        house, source_count, length = "H01", 4, 24
        measured = np.arange(source_count * 8 * 30 * length, dtype=np.float32).reshape(source_count, 8, 30, length) / 1000
        np.save(root / f"{house}_measured_train.npy", measured)
        base = np.tile(np.linspace(0, 1, length, dtype=np.float32), (30, 1))
        np.savez_compressed(
            root / f"{house}_schedule_train.npz",
            lengths=np.full(30, length, dtype=np.int32),
            x=base, y=base + 1, dt=np.full_like(base, 0.2),
            stop_start=np.zeros_like(base), block_boundary=np.zeros_like(base),
            wind=np.zeros((30, length, 3), dtype=np.float32),
        )
        carriers = [
            {
                "centroid_x": float(index), "centroid_y": float(index + 1),
                "width_m": 0.6, "height_m": 0.6,
                "free_mask": [1, 1, 1, 1], "free_count": 1,
                "prior_mass": 0.25,
            }
            for index in range(source_count)
        ]
        (root / f"{house}_carriers.json").write_text(json.dumps(carriers))
        validation = np.zeros((source_count, 8, 30), dtype=np.bool_)
        validation[:, :, 0] = True
        np.save(root / f"{house}_validation_split.npy", validation)

        data = TrainingData(root, house, 1701)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        configure_determinism(1701)
        assert os.environ.get("CUBLAS_WORKSPACE_CONFIG") == ":4096:8"
        features, mask, labels = data.make_examples(np.array([1, 241, 481], dtype=np.int64), device)
        assert features.shape == (6, length, 16)
        assert mask.all() and torch.equal(labels, torch.tensor([1, 1, 1, 0, 0, 0], device=device, dtype=torch.float32))
        # Positive/negative pairs must share observation, wind and time fields;
        # candidate-relative geometry is the only allowed change.
        assert torch.equal(features[:3, :, 9:], features[3:, :, 9:])
        assert not torch.equal(features[:3, :, :9], features[3:, :, :9])
        model = initialize_frozen_model(1701).to(device)
        loss = F.binary_cross_entropy_with_logits(model(features, mask), labels)
        loss.backward()
        assert torch.isfinite(loss)
        data.measured._mmap.close()
        del data

    print("PF_DEI_V3_TRAINING_CONTRACT_SELFTEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
