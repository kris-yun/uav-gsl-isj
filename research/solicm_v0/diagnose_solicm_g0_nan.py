#!/usr/bin/env python3
"""Read-only diagnostic rerun of one frozen failed arm; does not save a model."""
import collections
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from run_solicm_g0 import (AverageMeter, BATCH, LCA, load_bank, model_configs,
                           set_seed, source_risk, source_scaled_arrays)


def bad_tensors(named):
    return [name for name, tensor in named if not torch.isfinite(tensor).all().item()]


def main():
    bank = load_bank()
    set_seed(0)
    sx, sy, tx, _, _, _ = source_scaled_arrays(bank, 1, 0, 0)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data, args = model_configs("PL_ONLY")
    model = LCA(args, data, {"num_epochs": 40}, device).to(device)
    src = DataLoader(TensorDataset(torch.from_numpy(sx.transpose(0, 2, 1).copy()),
                                   torch.from_numpy(sy)), batch_size=BATCH, shuffle=True, drop_last=True)
    tgt = DataLoader(TensorDataset(torch.from_numpy(tx.transpose(0, 2, 1).copy()),
                                   torch.zeros(len(tx), dtype=torch.long)),
                     batch_size=BATCH, shuffle=True, drop_last=True)
    for epoch in range(1, 41):
        meter = collections.defaultdict(AverageMeter)
        model.train()
        model.training_epoch(src, tgt, meter, epoch)
        if epoch in (1, 2, 5, 10, 20, 30, 40):
            print(epoch, "train_source_loss", meter["Src_cls_loss"].avg,
                  "eval_source_risk", source_risk(model, sx, sy, device),
                  "bad_params", bad_tensors(model.named_parameters())[:8],
                  "bad_buffers", bad_tensors(model.named_buffers())[:8], flush=True)


if __name__ == "__main__":
    main()
