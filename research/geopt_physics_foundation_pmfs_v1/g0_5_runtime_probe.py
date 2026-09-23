#!/usr/bin/env python
"""G0.5 runtime probe for the released GeoPT 8-layer checkpoint.

This is deliberately a probe only: it does not train, modify the official
repository, or add a source adapter.  The small import shims keep the probe
reproducible in the local environment when ``timm``/``einops`` are absent;
the official Transolver implementation is imported unchanged.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import types
from pathlib import Path


def install_import_shims() -> None:
    """Provide only the two tiny utilities used by the released code."""
    if "einops" not in sys.modules:
        einops = types.ModuleType("einops")

        def rearrange(x, pattern, **kwargs):
            if pattern.strip() != "b h n d -> b n (h d)":
                raise NotImplementedError(pattern)
            return x.permute(0, 2, 1, 3).contiguous().reshape(
                x.shape[0], x.shape[2], x.shape[1] * x.shape[3]
            )

        def repeat(x, pattern, **kwargs):
            raise NotImplementedError("repeat is not used by the official unstructured probe")

        einops.rearrange = rearrange
        einops.repeat = repeat
        sys.modules["einops"] = einops
    if "timm.models.layers" not in sys.modules:
        timm = types.ModuleType("timm")
        models = types.ModuleType("timm.models")
        layers = types.ModuleType("timm.models.layers")

        def trunc_normal_(tensor, mean=0.0, std=1.0, a=-2.0, b=2.0):
            import torch.nn.init as init

            return init.trunc_normal_(tensor, mean=mean, std=std, a=a, b=b)

        layers.trunc_normal_ = trunc_normal_
        models.layers = layers
        timm.models = models
        sys.modules["timm"] = timm
        sys.modules["timm.models"] = models
        sys.modules["timm.models.layers"] = layers


def build_model(official_root: Path, out_dim: int):
    import torch
    from types import SimpleNamespace

    sys.path.insert(0, str(official_root))
    install_import_shims()
    from models.Transolver import Model

    args = SimpleNamespace(
        space_dim=3,
        fun_dim=11,
        out_dim=out_dim,
        n_hidden=256,
        n_heads=8,
        n_layers=8,
        mlp_ratio=2,
        slice_num=32,
        dropout=0.0,
        act="gelu",
        geotype="unstructured",
        shapelist=None,
        unified_pos=False,
        checkpoint=0,
    )
    return Model(args), args


def room_tensor(torch, n: int, device):
    """Create one deterministic House02-style free-space + wind tensor.

    The room is a normalized 7 x 5 x 3 m box with two internal rectangular
    obstacles.  The first 3 dimensions are coordinates passed separately to
    GeoPT; the remaining 11-D ``fx`` contract is
    ``[dwall, nx, ny, nz, wx, wy, wz, |w|, 0, 0, 0]``.
    The last three zero channels are reserved for future PMFS boundary/source
    metadata while preserving the audited 11-D fine-tuning interface.
    """
    import math

    # Uniform lattice, cropped deterministically to exactly n points.
    side = max(2, round(n ** (1.0 / 3.0)))
    g = torch.linspace(0.05, 0.95, side, device=device)
    xyz = torch.stack(torch.meshgrid(g, g, g, indexing="ij"), dim=-1).reshape(-1, 3)
    if xyz.shape[0] < n:
        reps = (n + xyz.shape[0] - 1) // xyz.shape[0]
        xyz = xyz.repeat((reps, 1))
    xyz = xyz[:n]
    # Signed distance to room walls in normalized coordinates, positive in free space.
    wall_dist = torch.minimum(torch.minimum(torch.minimum(xyz[:, 0], 1 - xyz[:, 0]),
                                             torch.minimum(xyz[:, 1], 1 - xyz[:, 1])),
                              torch.minimum(xyz[:, 2], 1 - xyz[:, 2]))
    # Two box obstacles: shrink free-space distance and use an outward normal.
    boxes = ((0.34, 0.52, 0.25, 0.62, 0.0, 0.68),
             (0.64, 0.80, 0.48, 0.78, 0.0, 0.55))
    for x0, x1, y0, y1, z0, z1 in boxes:
        inside = ((xyz[:, 0] >= x0) & (xyz[:, 0] <= x1) &
                  (xyz[:, 1] >= y0) & (xyz[:, 1] <= y1) &
                  (xyz[:, 2] >= z0) & (xyz[:, 2] <= z1))
        # A conservative local distance proxy to obstacle boundary.
        local = torch.minimum(torch.minimum(xyz[:, 0] - x0, x1 - xyz[:, 0]),
                              torch.minimum(xyz[:, 1] - y0, y1 - xyz[:, 1]))
        local = torch.minimum(local, torch.minimum(xyz[:, 2] - z0, z1 - xyz[:, 2]))
        wall_dist = torch.where(inside, -torch.abs(local), torch.minimum(wall_dist, torch.abs(local)))
    # A fixed House02-like horizontal wind with a mild vertical shear.
    wx = 0.72 + 0.08 * torch.sin(2 * math.pi * xyz[:, 2])
    wy = 0.12 * torch.cos(2 * math.pi * xyz[:, 0])
    wz = 0.03 * torch.sin(2 * math.pi * xyz[:, 1])
    speed = torch.sqrt(wx * wx + wy * wy + wz * wz)
    normals = torch.zeros_like(xyz)
    normals[:, 0] = torch.where(xyz[:, 0] < 0.5, -1.0, 1.0)
    normals[:, 1] = torch.where(xyz[:, 1] < 0.5, -1.0, 1.0)
    normals[:, 2] = torch.where(xyz[:, 2] < 0.5, -1.0, 1.0)
    fx = torch.cat((wall_dist[:, None], normals, wx[:, None], wy[:, None], wz[:, None],
                    speed[:, None], torch.zeros((n, 3), device=device)), dim=-1)
    return xyz[None], fx[None]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--official-root", type=Path, default=Path(r"D:\ZYC\A-gas\_staging\geopt_official_20260923"))
    p.add_argument("--checkpoint", type=Path, default=Path(r"D:\ZYC\A-gas\_staging\GeoPT_8layers.pt"))
    p.add_argument("--tokens", type=int, default=4096)
    p.add_argument("--device", default="cuda" if __import__("torch").cuda.is_available() else "cpu")
    p.add_argument("--out-dim", type=int, default=6, help="official GeoPT_craft fine-tune head")
    p.add_argument("--json-out", type=Path, default=None)
    a = p.parse_args()

    import torch
    import psutil

    device = torch.device(a.device)
    model, cfg = build_model(a.official_root, a.out_dim)
    ckpt = torch.load(a.checkpoint, map_location="cpu")
    model_state = model.state_dict()
    excluded = ("mlp2", "ln_3")
    shape_mismatch = [k for k, v in ckpt.items()
                      if k in model_state and tuple(v.shape) != tuple(model_state[k].shape)]
    filtered = {k: v for k, v in ckpt.items()
                if k in model_state and tuple(model_state[k].shape) == tuple(v.shape)
                and not any(excl in k for excl in excluded)}
    model_state.update(filtered)
    model.load_state_dict(model_state)
    model.eval().to(device)
    for param in model.parameters():
        param.requires_grad_(False)

    total_params = sum(v.numel() for v in model.parameters())
    loaded_params = sum(model_state[k].numel() for k in filtered)
    ckpt_params = sum(v.numel() for v in ckpt.values())
    x, fx = room_tensor(torch, a.tokens, device)

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)
    process = psutil.Process(os.getpid())
    rss_before = process.memory_info().rss
    peak_rss = [rss_before]
    stop_sampling = threading.Event()

    def sample_rss():
        while not stop_sampling.is_set():
            peak_rss[0] = max(peak_rss[0], process.memory_info().rss)
            stop_sampling.wait(0.001)

    rss_thread = threading.Thread(target=sample_rss, name="g05-rss", daemon=True)
    rss_thread.start()
    t0 = time.perf_counter()
    with torch.inference_mode():
        out = model(x, fx)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    wall = time.perf_counter() - t0
    stop_sampling.set()
    rss_thread.join(timeout=1.0)
    rss_after = process.memory_info().rss
    result = {
        "checkpoint": str(a.checkpoint),
        "checkpoint_bytes": a.checkpoint.stat().st_size,
        "official_config": vars(cfg),
        "checkpoint_tensor_keys": len(ckpt),
        "checkpoint_parameter_count": ckpt_params,
        "loaded_tensor_keys": len(filtered),
        "loaded_parameter_count": loaded_params,
        "model_total_parameter_count": total_params,
        "loaded_fraction_of_model_parameters": loaded_params / total_params,
        "excluded_layer_substrings": list(excluded),
        "excluded_keys": [k for k in ckpt if any(excl in k for excl in excluded)],
        "shape_mismatch_keys": shape_mismatch,
        "device": str(device),
        "tokens": int(x.shape[1]),
        "input_x_shape": list(x.shape),
        "input_fx_shape": list(fx.shape),
        "output_shape": list(out.shape),
        "wall_seconds": wall,
        "rss_before_bytes": rss_before,
        "rss_after_bytes": rss_after,
        "peak_rss_bytes": peak_rss[0],
        "rss_delta_bytes": rss_after - rss_before,
    }
    if device.type == "cuda":
        result.update({
            "gpu_name": torch.cuda.get_device_name(device),
            "peak_vram_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "peak_vram_reserved_bytes": torch.cuda.max_memory_reserved(device),
        })
    print(json.dumps(result, indent=2, sort_keys=True))
    if a.json_out:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
