# Pre-analysis Windows label datatype repair

Starting frozen commit: `6eb41085e5853c66fdd4083a1bde494abb96d459`.

The official synthetic self-test failed before scientific training with `RuntimeError: expected scalar type Long but found Int`. On this Windows NumPy 1.26.4 environment, default integer label arrays are int32. The same code normally produces int64 on Linux; PyTorch cross-entropy requires int64 class indices.

The sole repair is `torch.from_numpy(y).long()` and `torch.from_numpy(e).long()` in `train()`. Integer values and labels are unchanged. No architecture, feature, split, seed, optimizer, epoch, loss coefficient, prototype score or gate is changed. This repair happened before any held-out metrics were computed.

The existing CPU PyTorch 2.2.2 and NumPy 1.26.4 meet `requirements.txt`. No package installation/upgrade or GPU port is necessary. Preserve the original CPU execution, one thread and deterministic algorithms. Input SHA audit and synthetic self-test must pass before the two full executions.
