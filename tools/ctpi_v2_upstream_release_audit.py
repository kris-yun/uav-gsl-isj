"""Read pinned public source, record checkable operator anchors, no House payloads."""
import argparse
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path
from urllib.request import Request, urlopen

COMMIT = "4a299217e0e82925ca51762e7be25e83e3c138dd"
SOURCE = "gaden_filament_simulator/src/filament_simulator.cpp"
ANCHORS = [
    "numFilament_aux += numFilaments_step;",
    "int filaments_to_release = floor(numFilament_aux);",
    "filaments_to_release = (int)round(random_number(0.0, filaments_to_release));",
    "current_number_filaments += floor(numFilament_aux);",
    "numFilament_aux -= floor(numFilament_aux);",
    "double n = (double)(rand() % 100);",
    "srand(time(NULL));",
    "sim.sim_time = sim.sim_time + sim.time_step;",
]


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "CTPI-source-contract-audit"}), timeout=30) as r:
        return r.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    url = f"https://raw.githubusercontent.com/MAPIRlab/gaden/{COMMIT}/{SOURCE}"
    raw = fetch(url)
    lines = raw.decode('utf-8').splitlines()
    anchors = []
    for anchor in ANCHORS:
        matches = [i + 1 for i, line in enumerate(lines) if anchor in line]
        if len(matches) != 1:
            raise ValueError(f"source anchor is missing/ambiguous: {anchor}")
        anchors.append({"expression": anchor, "line": matches[0]})
    identity = json.loads(fetch(f"https://api.github.com/repos/MAPIRlab/gaden/commits/{COMMIT}"))
    if identity['sha'] != COMMIT:
        raise ValueError('commit identity mismatch')
    root = Path(__file__).resolve().parents[1]
    model = root / 'closed_loop/ctpi/ctpi_v2_release_schedule.py'
    spec = importlib.util.spec_from_file_location('release', model)
    release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release)
    carry = 0
    caps = []
    for _ in range(10):
        cap, carry = release.nominal_step(carry, 7, .1)
        caps.append(cap)
    law = [Fraction(1, 100)] * 100
    report = {
        'status': 'PINNED_ROS1_OPERATOR_CONTRACT_ONLY_NOT_HOUSE_BINDING_OR_M1_PASS',
        'source_url': url, 'commit': COMMIT,
        'commit_date': identity['commit']['committer']['date'],
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'source_line_count': len(lines), 'anchors': anchors,
        'fixture': {'rate': 7, 'native_dt': .1, 'initial_carry': 0,
                    'nominal_caps_first_ten_steps': caps,
                    'actual_expected_total_if_uniform_residues': sum(sum(float(n * p) for n, p in release.conditional_count_law(cap, law).items()) for cap in caps),
                    'uniform_residues_are_an_assumption_not_a_generator_proof': True},
        'operator_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations': ['No historical data-to-generator identity binding.',
                        'No independence or uniformity proof for the shared C PRNG.',
                        'Rate is a nominal cap parameter, not known gas mass flux.',
                        'No release prior, initial plume prior or propagation model qualified.',
                        'No protected bank, House payload or fresh source world accessed.']}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
