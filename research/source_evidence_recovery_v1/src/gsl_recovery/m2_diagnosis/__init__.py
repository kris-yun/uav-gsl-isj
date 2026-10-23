"""Mechanism proposals from shared-encoder causal-channel differences."""
from .network import DifferentialDiagnoser, history_descriptor, diagnostic_pairs

__all__ = ["DifferentialDiagnoser", "history_descriptor", "diagnostic_pairs"]
