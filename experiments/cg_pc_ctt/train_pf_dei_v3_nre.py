#!/usr/bin/env python3
"""Train one frozen per-House PF-DEI V3 causal-TCN NRE model."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from pf_dei_v3_causal_tcn import INPUT_DIM, initialize_frozen_model


LR = 3e-4
WEIGHT_DECAY = 1e-4
EXAMPLE_BATCH_SIZE = 64
BASE_BATCH_SIZE = EXAMPLE_BATCH_SIZE // 2
MAX_EPOCHS = 100
PATIENCE = 10
GRAD_CLIP = 1.0
THRESHOLD_GAS_PPM = 0.1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def configure_determinism(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)


class TrainingData:
    def __init__(self, root: Path, house: str, model_seed: int):
        self.house = house
        self.measured = np.load(root / f"{house}_measured_train.npy", mmap_mode="r")
        schedule = np.load(root / f"{house}_schedule_train.npz")
        self.lengths = schedule["lengths"]
        self.x, self.y, self.dt = schedule["x"], schedule["y"], schedule["dt"]
        self.stop_start, self.block_boundary = schedule["stop_start"], schedule["block_boundary"]
        self.wind = schedule["wind"]
        self.carriers = json.loads((root / f"{house}_carriers.json").read_text())
        self.validation = np.load(root / f"{house}_validation_split.npy")
        self.shape = self.measured.shape[:3]
        if self.shape != self.validation.shape or self.shape[1:] != (8, 30):
            raise ValueError("PF_DEI_V3_TRAINING_SHAPE_CONTRACT_FAIL")
        self.source_count = self.shape[0]
        self.centroid_x = np.asarray([row["centroid_x"] for row in self.carriers], dtype=np.float32)
        self.centroid_y = np.asarray([row["centroid_y"] for row in self.carriers], dtype=np.float32)
        self.width = np.asarray([row["width_m"] for row in self.carriers], dtype=np.float32)
        self.height = np.asarray([row["height_m"] for row in self.carriers], dtype=np.float32)
        self.mask4 = np.asarray([row["free_mask"] for row in self.carriers], dtype=np.float32)
        self.free_count = np.asarray([row["free_count"] for row in self.carriers], dtype=np.float32)
        self.prior = np.asarray([row["prior_mass"] for row in self.carriers], dtype=np.float64)
        if not np.isclose(self.prior.sum(), 1.0):
            raise ValueError("PF_DEI_V3_TRAINING_PRIOR_NOT_NORMALIZED")

        self.indices = np.arange(np.prod(self.shape), dtype=np.int64)
        source, member, trajectory = np.unravel_index(self.indices, self.shape)
        self.source = source.astype(np.int64)
        self.member = member.astype(np.int64)
        self.trajectory = trajectory.astype(np.int64)
        self.train_indices = self.indices[~self.validation.reshape(-1)]
        self.validation_indices = self.indices[self.validation.reshape(-1)]
        rng = np.random.default_rng(model_seed)
        negative = rng.choice(self.source_count, size=self.indices.size, p=self.prior)
        same = negative == self.source
        while np.any(same):
            negative[same] = rng.choice(self.source_count, size=int(same.sum()), p=self.prior)
            same = negative == self.source
        self.negative = negative.astype(np.int64)

    def make_examples(self, base_indices: np.ndarray, device: torch.device) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        source = self.source[base_indices]
        member = self.member[base_indices]
        trajectory = self.trajectory[base_indices]
        negative = self.negative[base_indices]
        candidates = np.concatenate((source, negative))
        batch = base_indices.size
        max_length = int(self.lengths[trajectory].max())
        features = np.zeros((2 * batch, max_length, INPUT_DIM), dtype=np.float32)
        mask = np.zeros((2 * batch, max_length), dtype=np.bool_)
        for row in range(batch):
            length = int(self.lengths[trajectory[row]])
            ppm = np.asarray(self.measured[source[row], member[row], trajectory[row], :length])
            log_ppm = np.log1p(ppm.astype(np.float64) / THRESHOLD_GAS_PPM).astype(np.float32)
            for offset in (0, batch):
                out = row + offset
                candidate = candidates[out]
                features[out, :length, 0] = self.x[trajectory[row], :length] - self.centroid_x[candidate]
                features[out, :length, 1] = self.y[trajectory[row], :length] - self.centroid_y[candidate]
                features[out, :length, 2] = self.width[candidate]
                features[out, :length, 3] = self.height[candidate]
                features[out, :length, 4:8] = self.mask4[candidate]
                features[out, :length, 8] = self.free_count[candidate] / 4.0
                features[out, :length, 9] = log_ppm
                features[out, :length, 10:13] = self.wind[trajectory[row], :length]
                features[out, :length, 13] = self.dt[trajectory[row], :length]
                features[out, :length, 14] = self.stop_start[trajectory[row], :length]
                features[out, :length, 15] = self.block_boundary[trajectory[row], :length]
                mask[out, :length] = True
        labels = np.concatenate((np.ones(batch, dtype=np.float32), np.zeros(batch, dtype=np.float32)))
        return (
            torch.from_numpy(features).to(device, non_blocking=True),
            torch.from_numpy(mask).to(device, non_blocking=True),
            torch.from_numpy(labels).to(device, non_blocking=True),
        )


def evaluate(model, data: TrainingData, device: torch.device) -> float:
    model.eval()
    loss_sum, count = 0.0, 0
    with torch.no_grad():
        for start in range(0, data.validation_indices.size, BASE_BATCH_SIZE):
            indices = data.validation_indices[start : start + BASE_BATCH_SIZE]
            features, mask, labels = data.make_examples(indices, device)
            loss = F.binary_cross_entropy_with_logits(model(features, mask), labels, reduction="sum")
            loss_sum += float(loss.item())
            count += labels.numel()
    return loss_sum / count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--house", choices=("H01", "H02", "H03"), required=True)
    parser.add_argument("--model-seed", type=int, choices=(1701, 1702, 1703), required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("PF_DEI_V3_TRAINING_CUDA_REQUIRED")
    configure_determinism(args.model_seed)
    device = torch.device("cuda")
    data = TrainingData(args.dataset_root, args.house, args.model_seed)
    model = initialize_frozen_model(args.model_seed).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    args.output_root.mkdir(parents=True, exist_ok=True)
    log = []
    best_loss = float("inf")
    best_state = None
    stale = 0
    rng = np.random.default_rng(args.model_seed)
    started = time.monotonic()
    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        order = data.train_indices.copy()
        rng.shuffle(order)
        # Repeat only the beginning of the shuffled order when needed, so all
        # distinct traces are seen while every optimizer step remains exactly
        # 64 balanced positive/negative examples.
        remainder = order.size % BASE_BATCH_SIZE
        if remainder:
            order = np.concatenate((order, order[: BASE_BATCH_SIZE - remainder]))
        training_loss, examples = 0.0, 0
        for start in range(0, order.size, BASE_BATCH_SIZE):
            features, mask, labels = data.make_examples(order[start : start + BASE_BATCH_SIZE], device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(features, mask)
            loss = F.binary_cross_entropy_with_logits(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            optimizer.step()
            training_loss += float(loss.item()) * labels.numel()
            examples += labels.numel()
        validation_loss = evaluate(model, data, device)
        row = {
            "epoch": epoch, "training_bce": training_loss / examples,
            "validation_bce": validation_loss, "elapsed_s": time.monotonic() - started,
        }
        log.append(row)
        print("PF_DEI_V3_TRAINING_EPOCH " + json.dumps(row, sort_keys=True), flush=True)
        if validation_loss < best_loss:
            best_loss = validation_loss
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
            if stale >= PATIENCE:
                break
    if best_state is None:
        raise RuntimeError("PF_DEI_V3_TRAINING_NO_BEST_STATE")
    weights = args.output_root / f"{args.house}_seed{args.model_seed}.pt"
    torch.save(best_state, weights)
    training_log = args.output_root / f"{args.house}_seed{args.model_seed}_training.json"
    payload = {
        "contract": "PF_DEI_V3_FROZEN_CAUSAL_TCN_TRAINING_V1",
        "house": args.house, "model_seed": args.model_seed,
        "optimizer": "AdamW", "learning_rate": LR, "weight_decay": WEIGHT_DECAY,
        "batch_size": EXAMPLE_BATCH_SIZE, "max_epochs": MAX_EPOCHS,
        "patience": PATIENCE, "gradient_clip": GRAD_CLIP,
        "best_validation_bce": best_loss, "epochs_run": len(log),
        "weights_sha256": sha256_file(weights), "epochs": log,
    }
    training_log.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "PF_DEI_V3_NRE_TRAINING=PASS "
        f"house={args.house} seed={args.model_seed} epochs={len(log)} "
        f"weights_sha256={payload['weights_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
