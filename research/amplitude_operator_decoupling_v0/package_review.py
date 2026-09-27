"""Portable implementation review: exact inputs, code, evidence and SHA inventory."""
from pathlib import Path
import argparse, hashlib, io, json, subprocess, zipfile
from run_saved_readout import EXPECTED


def main():
    p = argparse.ArgumentParser()
    for key in EXPECTED:
        p.add_argument('--'+key+'-zip', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    here = Path(__file__).resolve().parent
    repo = here.parents[1]
    entries = {}
    for key, expected in EXPECTED.items():
        f = getattr(a, key+'_zip')
        data = f.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Input ZIP mismatch')
        entries['original_inputs/'+f.name] = data
    for folder in ['research/amplitude_operator_decoupling_v0', 'evidence/amplitude_operator_decoupling_v0']:
        paths = subprocess.check_output(['git', 'ls-files', '-z', folder], cwd=repo).decode().split('\0')
        for name in paths:
            if name:
                entries[name] = (repo/name).read_bytes()
    entries['PACKAGE_PROVENANCE.json'] = (json.dumps(dict(
        branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=repo, text=True).strip(),
        final_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
        role='Implementation and posthoc OPEN reproduction only; STOP',
        exact_input_zip_hashes=EXPECTED, new_forward_runs=0, new_gaden_runs=0), indent=2)+'\n').encode()
    inventory = ''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n'
                        for name, data in sorted(entries.items()))
    entries['SHA256SUMS'] = inventory.encode()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.out, 'x') as z:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 27, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if name.endswith('.zip') else zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    with zipfile.ZipFile(a.out) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP CRC failure')
        for line in z.read('SHA256SUMS').decode().splitlines():
            expected, name = line.split('  ', 1)
            if hashlib.sha256(z.read(name)).hexdigest() != expected:
                raise ValueError('ZIP inventory mismatch: '+name)
    print(json.dumps(dict(path=str(a.out.resolve()), bytes=a.out.stat().st_size,
                          sha256=hashlib.sha256(a.out.read_bytes()).hexdigest(),
                          verified_inventory_entries=len(entries)-1), indent=2))


if __name__ == '__main__':
    main()
