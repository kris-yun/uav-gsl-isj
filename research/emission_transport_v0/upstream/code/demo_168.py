"""168 synthetic grid START STATES; exact finite-state law, no GADEN runs."""
import json
import time
from pathlib import Path
import numpy as np
from emission_transport import MarkedTransport, grid_kernel, log_likelihood, source_posterior

start = time.perf_counter()
free = np.ones((12, 14), dtype=bool)
wind = np.zeros((12, 14, 2)); wind[..., 0] = .1
p, cells = grid_kernel(free, wind, dx=1., diffusivity=.12, dt=.5)
marks = np.zeros((2, len(cells), 2), dtype=int)
# A fixed point-like numerical sensor, same location at two times.
for k in range(2):
    dist = np.sum(abs(cells - np.array([6, 7])), axis=1)
    marks[k, :, k] = np.maximum(0, 2 - dist)
model = MarkedTransport(np.stack([p, p]), marks)
laws = model.all_source_laws(list(range(len(cells))), [{1: 1.}, {1: 1.}])
# Chosen illustrative observation, not generated/held-out plume data.
y = np.array([1., 2.])
ll = log_likelihood(laws, y, np.ones(2), np.full(2, .3))
q = source_posterior(ll, np.full(len(cells), 1 / len(cells)))
result = {
    'scope': 'SYNTHETIC FINITE-STATE COMPUTATION ONLY; NOT 168 GADEN-source evaluation',
    'candidate_count': len(cells), 'observation_dimension': 2,
    'fixed_birth_counts': [1, 1], 'posterior_mass': float(q.sum()),
    'max_law_mass_defect': max(abs(sum(l.values()) - 1.) for l in laws),
    'maximum_atoms_per_candidate': max(map(len, laws)),
    'map_grid_yx': cells[int(np.argmax(q))].tolist(),
    'elapsed_seconds': time.perf_counter() - start,
    'observed_example': y.tolist(), 'sensor_sd_example': [.3, .3],
    'not_tested': ['GADEN equivalence', 'transport realism', 'unknown wind identification',
                   '300-dimensional exact law', 'UAV real-time feasibility', 'scientific novelty']}
base = Path(__file__).resolve().parents[1] / 'evidence'
(base / 'SYNTHETIC_168_COMPUTATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
np.savez_compressed(base / 'SYNTHETIC_168_POSTERIOR.npz', cells=cells, posterior=q, log_likelihood=ll)
print(json.dumps(result, indent=2))
