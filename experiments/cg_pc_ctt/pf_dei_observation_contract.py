#!/usr/bin/env python3
"""PF-DEI observation-operator contract.

This module contains NO source-localization likelihood.  It exists to prevent a
physically invalid shortcut from CTT filament occupancy to the PMFS gas sensor
observation.

Normative causal chain:
    source -> transport -> physical concentration -> persistent sensor state
           -> measured concentration -> PMFS block mean -> HIT/NOTHING

The main predictive payload is valid only if physical concentration and measured
concentration are produced by the authoritative GADEN/sensor forward operator.
Filament occupancy/frequency may be retained only as an ablation/diagnostic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence
import numpy as np


FORBIDDEN_OBSERVED_KEYS = {
    "true_gas_ppm", "true_source", "source_truth", "localization_error",
    "final_error", "off_on_improvement",
}

ALLOWED_CONCENTRATION_ORIGINS = {
    "native_gaden_physical_concentration",
    "native_gaden_sensor_forward",
}


@dataclass(frozen=True)
class BlockObservation:
    block_id: int
    sample_indices: tuple[int, ...]
    measured_mean_ppm: float
    hit: bool


def validate_measured_trace(sample_time, measured_gas_ppm):
    t = np.asarray(sample_time, dtype=float)
    y = np.asarray(measured_gas_ppm, dtype=float)
    if t.ndim != 1 or y.shape != t.shape or len(t) < 1:
        raise ValueError("measured trace shape mismatch")
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(y)):
        raise ValueError("measured trace must be finite")
    if np.any(np.diff(t) <= 0):
        raise ValueError("sample_time must be strictly increasing")
    return t, y


def reconstruct_completed_blocks(sample_time, measured_gas_ppm,
                                 block_sample_indices: Sequence[Sequence[int]],
                                 gas_threshold: float,
                                 archived_hit: Sequence[bool],
                                 expected_samples_per_block: int = 10):
    """Recompute the exact PMFS block observation from consumed measured samples.

    `block_sample_indices` MUST come from authoritative runtime/state provenance;
    this function deliberately does not infer block membership from a floating
    timestamp window.  That avoids silently assigning settle/moving-state samples
    to a StopAndMeasure block.
    """
    t, y = validate_measured_trace(sample_time, measured_gas_ppm)
    hit = np.asarray(archived_hit, dtype=bool)
    if len(block_sample_indices) != len(hit):
        raise ValueError("block count mismatch")
    if not np.isfinite(gas_threshold):
        raise ValueError("gas threshold must be finite")
    used: set[int] = set()
    out: list[BlockObservation] = []
    last_end_time = -np.inf
    for b, raw_idx in enumerate(block_sample_indices):
        idx = np.asarray(raw_idx, dtype=int).reshape(-1)
        if len(idx) != int(expected_samples_per_block):
            raise ValueError(f"block {b}: expected {expected_samples_per_block} consumed samples")
        if np.any(idx < 0) or np.any(idx >= len(y)) or len(np.unique(idx)) != len(idx):
            raise ValueError(f"block {b}: invalid sample indices")
        if np.any(np.diff(idx) <= 0):
            raise ValueError(f"block {b}: sample indices must increase")
        if any(int(i) in used for i in idx):
            raise ValueError(f"block {b}: consumed sample reused")
        if t[idx[0]] <= last_end_time:
            raise ValueError(f"block {b}: block sample times overlap or reverse")
        used.update(map(int, idx))
        last_end_time = float(t[idx[-1]])
        mean_ppm = float(np.mean(y[idx], dtype=np.float64))
        predicted_hit = bool(mean_ppm > gas_threshold)
        if predicted_hit != bool(hit[b]):
            raise ValueError(
                f"block {b}: measured-sample reconstruction disagrees with archived PMFS decision"
            )
        out.append(BlockObservation(b, tuple(map(int, idx)), mean_ppm, predicted_hit))
    return tuple(out)


def validate_forward_payload(payload: dict):
    """Validate a candidate/source forward payload before any likelihood is allowed."""
    required = {
        "sample_time", "physical_concentration_ppm", "simulated_measured_ppm",
        "source_xy", "transport_keys", "sensor_model_hash", "sensor_parameter_hash",
        "concentration_origin", "sensor_state_scope", "context_state_reset",
        "source_truth_used",
    }
    missing = sorted(required.difference(payload))
    if missing:
        raise ValueError(f"forward payload missing {missing}")
    if payload["source_truth_used"] is not False:
        raise ValueError("forward payload must be truth-free with respect to the observed run")
    if payload["concentration_origin"] not in ALLOWED_CONCENTRATION_ORIGINS:
        raise ValueError("physical concentration was not produced by an authoritative GADEN forward path")
    if payload["sensor_state_scope"] != "run_persistent" or payload["context_state_reset"] is not False:
        raise ValueError("sensor internal state must persist across contexts; per-context reset is forbidden")
    if not str(payload["sensor_model_hash"]) or not str(payload["sensor_parameter_hash"]):
        raise ValueError("sensor model/parameter provenance hashes are required")

    t = np.asarray(payload["sample_time"], dtype=float)
    c = np.asarray(payload["physical_concentration_ppm"], dtype=float)
    m = np.asarray(payload["simulated_measured_ppm"], dtype=float)
    sxy = np.asarray(payload["source_xy"], dtype=float)
    if t.ndim != 1 or len(t) < 2 or np.any(np.diff(t) <= 0):
        raise ValueError("invalid forward sample_time")
    if c.ndim != 3 or m.shape != c.shape or c.shape[2] != len(t):
        raise ValueError("forward concentration arrays must be [source,member,time]")
    if sxy.shape != (c.shape[0], 2):
        raise ValueError("source_xy mismatch")
    if len(payload["transport_keys"]) != c.shape[1]:
        raise ValueError("transport key count mismatch")
    if not np.all(np.isfinite(c)) or not np.all(np.isfinite(m)) or np.any(c < 0):
        raise ValueError("non-finite/negative forward concentration")
    return True


def reject_occupancy_as_main_observation(payload: dict):
    """Explicit regression guard against the superseded occupancy->HIT shortcut."""
    has_physical = "physical_concentration_ppm" in payload and "simulated_measured_ppm" in payload
    occupancy_only = any(k in payload for k in ("occupancy", "occupancy_words", "hit_frequency", "stop_probability")) and not has_physical
    if occupancy_only:
        raise ValueError("CTT occupancy/frequency cannot serve as the normative PF-DEI observation operator")
    return True
