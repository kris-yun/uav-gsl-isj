#!/usr/bin/env python
"""M6 G1 gate: audit data, register the split, and run a development smoke test.

The default action is deliberately data-only.  It does not train on the
existing CTPI/TSDC worlds, because those worlds contain 1-D sensor trajectories
and no spatial plume field plus explicit wind prompt.  ``--development-smoke``
only checks that a source adapter can alter a frozen GeoPT hidden state and
compares it with a randomly initialized same-capacity backbone; it is not a
scientific result and writes no model checkpoint.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path


WORKTREE = Path(__file__).resolve().parents[3]
OFFICIAL_ROOT = Path(r"D:\ZYC\A-gas\_staging\geopt_official_20260923")
CHECKPOINT = Path(r"D:\ZYC\A-gas\_staging\GeoPT_8layers.pt")
TSDC_ROOT = Path(r"D:\ZYC\A-gas\_staging\CTPI_M2_TSDC_FRESH_CONFIRM_PASS_20260903\vm_run_root\01_WORLDS")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_tsd_data(root: Path) -> dict:
    worlds = []
    if root.exists():
        for d in sorted(p for p in root.glob("TSDC_FRESH_*") if p.is_dir()):
            audit_path = d / "WORLD_AUDIT.json"
            src_path = d / "sealed" / "source_intervention.json"
            ppm_path = d / "physical_ppm.npy"
            route_path = d / "route_1500.csv"
            if not (audit_path.exists() and src_path.exists() and ppm_path.exists()):
                continue
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            source = json.loads(src_path.read_text(encoding="utf-8"))
            # Numpy is imported only for shape/rank inspection, not for training.
            import numpy as np

            ppm = np.load(ppm_path, mmap_mode="r")
            route_header = []
            route_rows = 0
            if route_path.exists():
                with route_path.open(newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    route_header = next(reader, [])
                    route_rows = sum(1 for _ in reader)
            worlds.append({
                "world": d.name,
                "house": audit.get("house"),
                "route_index": audit.get("route_index"),
                "source_xyz_m": source.get("source_xyz_m"),
                "source_visibility": source.get("runtime_visibility"),
                "ppm_shape": list(ppm.shape),
                "ppm_ndim": int(ppm.ndim),
                "ppm_dtype": str(ppm.dtype),
                "route_rows": route_rows,
                "route_header": route_header,
                "explicit_wind_prompt": False,
                "spatial_plume_field": bool(ppm.ndim >= 2),
                "audit_sha256": sha256(audit_path),
                "ppm_sha256": sha256(ppm_path),
            })
    sources = {tuple(w["source_xyz_m"] or []) for w in worlds}
    houses = sorted({w["house"] for w in worlds if w["house"]})
    spatial = [w for w in worlds if w["spatial_plume_field"]]
    winds = [w for w in worlds if w["explicit_wind_prompt"]]
    qualified = [w for w in worlds if w["spatial_plume_field"] and w["explicit_wind_prompt"]]
    return {
        "root": str(root),
        "world_count": len(worlds),
        "houses": houses,
        "unique_source_coordinates": len(sources),
        "spatial_plume_field_count": len(spatial),
        "explicit_wind_prompt_count": len(winds),
        "qualified_source_wind_field_count": len(qualified),
        "worlds": worlds,
        "status": "DATA_HOLD" if not qualified else "DATA_AVAILABLE_FOR_REVIEW",
        "reason": (
            "physical_ppm.npy is a 1-D trajectory signal (1500 samples), and "
            "route_1500.csv contains pose/seed columns but no spatial plume grid "
            "or explicit 4-D wind prompt; therefore no source×wind field sample "
            "can enter G1 without new data generation."
        ),
    }


def load_g05_helpers():
    path = Path(__file__).with_name("g0_5_runtime_probe.py")
    spec = importlib.util.spec_from_file_location("g05_runtime_probe", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def load_filtered(model, torch, checkpoint: Path):
    ckpt = torch.load(checkpoint, map_location="cpu")
    state = model.state_dict()
    filtered = {
        k: v for k, v in ckpt.items()
        if k in state and tuple(state[k].shape) == tuple(v.shape)
        and not ("mlp2" in k or "ln_3" in k)
    }
    state.update(filtered)
    model.load_state_dict(state)
    return filtered


def development_smoke(args) -> dict:
    """Check source injection and frozen/scratch parity of the interface only."""
    import torch
    import torch.nn as nn

    g05 = load_g05_helpers()
    g05.install_import_shims()
    torch.manual_seed(20260923)
    loaded, cfg = g05.build_model(OFFICIAL_ROOT, out_dim=6)
    scratch, _ = g05.build_model(OFFICIAL_ROOT, out_dim=6)
    loaded.to(args.device).eval()
    scratch.to(args.device).eval()
    load_filtered(loaded, torch, CHECKPOINT)
    for p in loaded.parameters():
        p.requires_grad_(False)
    for p in scratch.parameters():
        p.requires_grad_(False)

    class SourceInjectionAdapter(nn.Module):
        def __init__(self, hidden=256):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(4, 64), nn.GELU(), nn.Linear(64, hidden))

        def forward(self, x, source):
            rel = x - source[:, None, :]
            dist = torch.linalg.vector_norm(rel, dim=-1, keepdim=True)
            return self.net(torch.cat((rel, dist), dim=-1))

    adapter_loaded = SourceInjectionAdapter().to(args.device).eval()
    adapter_scratch = SourceInjectionAdapter().to(args.device).eval()
    x, fx = g05.room_tensor(torch, args.tokens, args.device)
    sources = torch.tensor([[0.25, 0.55, 0.45], [0.75, 0.35, 0.55]], device=args.device)

    def hidden(model, adapter, source):
        h = model.preprocess(torch.cat((x, fx), dim=-1))
        h = h + model.placeholder[None, None, :]
        h = h + adapter(x, source)
        # Stop before the last block's excluded/uninitialized output head.  The
        # resulting 256-D tensor is the transferable frozen representation.
        for block in model.blocks[:-1]:
            h = block(h)
        return h

    with torch.inference_mode():
        h_l0 = hidden(loaded, adapter_loaded, sources[0:1])
        h_l1 = hidden(loaded, adapter_loaded, sources[1:2])
        h_s0 = hidden(scratch, adapter_scratch, sources[0:1])
        h_s1 = hidden(scratch, adapter_scratch, sources[1:2])
    return {
        "status": "DEVELOPMENT_ONLY_SMOKE",
        "scientific_interpretation": "NONE",
        "device": str(args.device),
        "tokens": int(args.tokens),
        "source_candidates": 2,
        "loaded_hidden_shape": list(h_l0.shape),
        "scratch_hidden_shape": list(h_s0.shape),
        "frozen_geopt_source_delta_l2": float(torch.linalg.vector_norm(h_l0 - h_l1).item()),
        "scratch_source_delta_l2": float(torch.linalg.vector_norm(h_s0 - h_s1).item()),
        "source_adapter_parameters": sum(p.numel() for p in adapter_loaded.parameters()),
        "note": "No target plume, rank, held-out source, or held-out wind was used.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--tsdc-root", type=Path, default=TSDC_ROOT)
    p.add_argument("--json-out", type=Path, default=None)
    p.add_argument("--development-smoke", action="store_true")
    p.add_argument("--tokens", type=int, default=1024)
    p.add_argument("--device", default="cuda" if __import__("torch").cuda.is_available() else "cpu")
    args = p.parse_args()
    audit = audit_tsd_data(args.tsdc_root)
    result = {
        "gate": "M6_G1",
        "status": audit["status"],
        "data_audit": audit,
        "preregistered_interface": {
            "estimands": ["truth-containing source candidate rank", "field error (auxiliary)"],
            "primary_comparison": "frozen GeoPT backbone + source adapter vs same-capacity scratch backbone + source adapter",
            "required_input": "spatial free-space geometry (7-D) + explicit 4-D wind prompt + localized source intervention",
            "required_split": "seen source×wind training cells and at least one unseen source×wind test cell, fixed before training",
            "controls": ["random GeoPT weights", "source adapter shuffle", "wind prompt shuffle"],
            "pass_rule": "frozen transfer improves held-out source rank over scratch with source/wind shuffle collapse; no field-only pass",
            "stop_rule": "without spatial plume fields and explicit wind prompts, report DATA_HOLD and do not train or tune",
        },
    }
    if args.development_smoke:
        result["development_smoke"] = development_smoke(args)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
