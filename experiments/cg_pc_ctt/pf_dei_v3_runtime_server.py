#!/usr/bin/env python3
"""Persistent fail-closed PF-DEI V3 inference server.

The server is an engineering deployment of the frozen Python reference.  It
accepts only the complete causal sensor prefix plus fixed geometry carrier IDs
and returns the carrier posterior.  Source truth, native posterior, planner
state, future samples, and localization error are absent from the protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socketserver
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from pf_dei_v3_causal_tcn import initialize_frozen_model
from pf_dei_v3_features import build_features, load_carriers
from pf_dei_v3_schema import FEATURE_NAMES


MODEL_SEEDS = (1701, 1702, 1703)
MAX_SAMPLES = 10000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def posterior_from_logits(prior: np.ndarray, logits: np.ndarray) -> np.ndarray:
    q0 = np.asarray(prior, dtype=np.float64)
    f = np.asarray(logits, dtype=np.float64)
    if q0.ndim != 1 or f.shape != q0.shape or np.any(q0 <= 0.0):
        raise ValueError("PF_DEI_V3_RUNTIME_BAD_POSTERIOR_INPUT")
    log_weight = np.log(q0) + f
    log_weight -= float(np.max(log_weight))
    posterior = np.exp(log_weight)
    posterior /= float(posterior.sum())
    if not np.isfinite(posterior).all() or np.any(posterior <= 0.0):
        raise ValueError("PF_DEI_V3_RUNTIME_NONFINITE_POSTERIOR")
    return posterior


@dataclass(frozen=True)
class RuntimeRequest:
    house: str
    update_id: int
    carrier_ids: tuple[str, ...]
    time: np.ndarray
    x: np.ndarray
    y: np.ndarray
    measured: np.ndarray
    wind: np.ndarray
    stop_start: np.ndarray
    block_boundary: np.ndarray

    def schedule(self) -> dict[str, np.ndarray]:
        dt = np.diff(np.concatenate(([0.0], self.time))).astype(np.float32)
        if np.any(dt <= 0.0):
            raise ValueError("PF_DEI_V3_RUNTIME_NONCAUSAL_TIME")
        return {
            "time": self.time,
            "x": self.x,
            "y": self.y,
            "dt": dt,
            "stop_start": self.stop_start,
            "block_boundary": self.block_boundary,
        }


def parse_request(lines: list[str]) -> RuntimeRequest:
    if not lines:
        raise ValueError("PF_DEI_V3_RUNTIME_EMPTY_REQUEST")
    header = lines[0].split()
    if len(header) != 5 or header[0] != "PFDEI_V3_REQUEST":
        raise ValueError("PF_DEI_V3_RUNTIME_BAD_HEADER")
    house, update_text, sample_text, carrier_text = header[1:]
    if house not in ("H01", "H02", "H03"):
        raise ValueError("PF_DEI_V3_RUNTIME_BAD_HOUSE")
    update_id, sample_count, carrier_count = int(update_text), int(sample_text), int(carrier_text)
    if update_id <= 0 or not 1 <= sample_count <= MAX_SAMPLES or carrier_count <= 0:
        raise ValueError("PF_DEI_V3_RUNTIME_BAD_COUNTS")
    if len(lines) != sample_count + 3 or lines[-1] != "END":
        raise ValueError("PF_DEI_V3_RUNTIME_BAD_LENGTH")
    carrier_ids = tuple(token for token in lines[1].split(",") if token)
    if len(carrier_ids) != carrier_count or len(set(carrier_ids)) != carrier_count:
        raise ValueError("PF_DEI_V3_RUNTIME_BAD_CARRIER_IDS")
    values = np.asarray([[float(token) for token in row.split(",")] for row in lines[2:-1]], dtype=np.float64)
    if values.shape != (sample_count, 9) or not np.isfinite(values).all():
        raise ValueError("PF_DEI_V3_RUNTIME_BAD_SAMPLE_MATRIX")
    if np.any(values[:, 3] < 0.0):
        raise ValueError("PF_DEI_V3_RUNTIME_NEGATIVE_MEASURED_PPM")
    for column in (7, 8):
        if not np.isin(values[:, column], (0.0, 1.0)).all():
            raise ValueError("PF_DEI_V3_RUNTIME_BAD_MARKER")
    request = RuntimeRequest(
        house=house, update_id=update_id, carrier_ids=carrier_ids,
        time=values[:, 0], x=values[:, 1].astype(np.float32), y=values[:, 2].astype(np.float32),
        measured=values[:, 3], wind=values[:, 4:7].astype(np.float32),
        stop_start=values[:, 7].astype(np.float32), block_boundary=values[:, 8].astype(np.float32),
    )
    request.schedule()
    return request


class FrozenInferenceEngine:
    def __init__(self, support: Path, weights_root: Path, device: torch.device):
        forbidden = ("truth", "source_z", "latent", "error", "future", "native")
        if any(token in name for name in FEATURE_NAMES for token in forbidden):
            raise ValueError("PF_DEI_V3_RUNTIME_FEATURE_LEAKAGE")
        self.device = device
        self.carriers = load_carriers(support)
        self.models = {}
        self.weight_hashes = {}
        for house in ("H01", "H02", "H03"):
            house_models = []
            house_hashes = {}
            for seed in MODEL_SEEDS:
                path = weights_root / f"{house}_seed{seed}.pt"
                model = initialize_frozen_model(seed)
                model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
                house_models.append(model.to(device).eval())
                house_hashes[str(seed)] = sha256_file(path)
            self.models[house] = house_models
            self.weight_hashes[house] = house_hashes

    def infer(self, request: RuntimeRequest) -> np.ndarray:
        carriers = self.carriers[request.house]
        expected_ids = tuple(carrier.carrier_id for carrier in carriers)
        if request.carrier_ids != expected_ids:
            raise ValueError("PF_DEI_V3_RUNTIME_CARRIER_IDENTITY_FAIL")
        schedule = request.schedule()
        logits = np.empty(len(carriers), dtype=np.float64)
        for start in range(0, len(carriers), 64):
            selected = carriers[start : start + 64]
            features = np.stack([
                build_features(schedule, request.measured, request.wind, carrier)
                for carrier in selected
            ])
            mask = np.ones(features.shape[:2], dtype=np.bool_)
            x = torch.from_numpy(features).to(self.device)
            m = torch.from_numpy(mask).to(self.device)
            with torch.no_grad():
                batch_logits = torch.stack([
                    model(x, m) for model in self.models[request.house]
                ]).mean(dim=0)
            logits[start : start + len(selected)] = batch_logits.detach().cpu().numpy()
        prior = np.asarray([carrier.prior_mass for carrier in carriers], dtype=np.float64)
        return posterior_from_logits(prior, logits)


class RuntimeState:
    def __init__(self, engine: FrozenInferenceEngine, audit_path: Path):
        self.engine = engine
        self.audit_path = audit_path
        self.lock = threading.Lock()
        audit_path.parent.mkdir(parents=True, exist_ok=True)

    def audit(self, payload: dict) -> None:
        with self.lock, self.audit_path.open("a", encoding="utf-8") as sink:
            sink.write(json.dumps(payload, sort_keys=True) + "\n")


class Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        raw_lines = []
        while True:
            raw = self.rfile.readline(1024 * 1024)
            if not raw:
                raise ConnectionError("PF_DEI_V3_RUNTIME_EOF_BEFORE_END")
            line = raw.decode("utf-8").rstrip("\r\n")
            raw_lines.append(line)
            if line == "END":
                break
            if len(raw_lines) > MAX_SAMPLES + 3:
                raise ValueError("PF_DEI_V3_RUNTIME_OVERSIZE_REQUEST")
        request_hash = hashlib.sha256(("\n".join(raw_lines) + "\n").encode()).hexdigest()
        try:
            request = parse_request(raw_lines)
            posterior = self.server.state.engine.infer(request)  # type: ignore[attr-defined]
            response = " ".join(f"{value:.17g}" for value in posterior)
            self.wfile.write(
                f"PFDEI_V3_OK {request.house} {request.update_id} {posterior.size} {request_hash}\n".encode()
            )
            self.wfile.write((response + "\nEND\n").encode())
            self.server.state.audit({  # type: ignore[attr-defined]
                "status": "PASS", "house": request.house, "update_id": request.update_id,
                "sample_count": request.time.size, "carrier_count": posterior.size,
                "request_sha256": request_hash,
                "posterior_sum": float(posterior.sum()),
                "posterior_min": float(posterior.min()), "posterior_max": float(posterior.max()),
                "weights_sha256": self.server.state.engine.weight_hashes[request.house],  # type: ignore[attr-defined]
                "truth_fields_used": False,
            })
        except Exception as error:
            self.server.state.audit({  # type: ignore[attr-defined]
                "status": "FAIL", "request_sha256": request_hash,
                "error_type": type(error).__name__, "error": str(error),
            })
            self.wfile.write(f"PFDEI_V3_ERROR {type(error).__name__} {error}\nEND\n".encode())


class ThreadedServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--weights-root", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=38081)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("PF_DEI_V3_RUNTIME_CUDA_REQUIRED")
    engine = FrozenInferenceEngine(args.support, args.weights_root, torch.device(args.device))
    with ThreadedServer((args.host, args.port), Handler) as server:
        server.state = RuntimeState(engine, args.audit)  # type: ignore[attr-defined]
        print(
            f"PF_DEI_V3_RUNTIME_SERVER=READY host={args.host} port={args.port} "
            f"device={args.device}", flush=True,
        )
        server.serve_forever(poll_interval=0.2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
