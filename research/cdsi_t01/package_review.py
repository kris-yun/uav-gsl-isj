"""Build a compact metadata-only CDSI Gate-A review package."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT/'evidence/cdsi_t01'


def main():
    first, second = EV/'pass1', EV/'pass2'
    names = sorted(p.name for p in first.iterdir() if p.is_file())
    assert names == sorted(p.name for p in second.iterdir() if p.is_file())
    checks = []
    for name in names:
        a, b = (first/name).read_bytes(), (second/name).read_bytes()
        assert a == b, name
        checks.append(dict(file=name, bytes=len(a), sha256=hashlib.sha256(a).hexdigest(), byte_identical=True))
    repeat = dict(pass_=True, compared_files=len(checks), checks=checks)
    (EV/'DETERMINISTIC_REPEAT.json').write_text(json.dumps(repeat, indent=2, sort_keys=True)+'\n', encoding='utf-8', newline='\n')
    for name in names:
        (EV/name).write_bytes((first/name).read_bytes())
    print(json.dumps({'repeat_pass':True,'compared_files':len(names)}, sort_keys=True))


def package():
    commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    branch = subprocess.check_output(['git','branch','--show-current'], cwd=ROOT, text=True).strip()
    files = [p for p in (ROOT/'research/cdsi_t01').rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    files += [p for p in EV.rglob('*') if p.is_file()]
    evidence = ROOT/'evidence/ocb_r2'
    files += list((evidence/'s2_runs').glob('*.RUN_MANIFEST.json'))
    files += list((evidence/'s2x/runs').glob('*.RUN_MANIFEST.json'))
    for rel in ('evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv',
        'evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv',
        'evidence/ocb_r2/mechanism_census_r0/R0_INPUT_HASHES.json',
        'research/ocb_r2/OCB_R2_S2X_MATCHED_SOURCE_CROSSOVER_32_PLAN.md',
        'research/ocb_r2/OCB_R2_GENERATOR_CONTRACT.md',
        'research/ocb_r2/RNG_THREAD_DETERMINISM_AUDIT.md',
        'research/ocb_r2/RNG_INVENTORY.tsv', 'research/ocb_r2/run_s2_vm.py',
        'research/ocb_r2/run_s2x_vm.py', 'research/ocb_r2/prepare_s2x_freeze.py'):
        files.append(ROOT/rel)
    files = sorted(set(files))
    inventory = [dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size,
        sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
    destination = Path('C:/Users/50176/Downloads/CDSI_T01_MATCHED_CONTRACT_REVIEW_20261001.zip')
    assert not destination.exists(), 'Refusing to overwrite prior review ZIP'
    provenance = dict(branch=branch, commit=commit, decision='CDSI_T01_MATCHED_INTERVENTION_FAIL',
        scope='Metadata-only prerequisite stop; scientific tests NOT EXECUTED', files=inventory)
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            z.write(p, p.relative_to(ROOT).as_posix())
        z.writestr('PACKAGE_PROVENANCE.json', json.dumps(provenance, indent=2, sort_keys=True)+'\n')
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        for entry in inventory:
            assert hashlib.sha256(z.read(entry['path'])).hexdigest() == entry['sha256']
    result = dict(path=str(destination), bytes=destination.stat().st_size,
        sha256=hashlib.sha256(destination.read_bytes()).hexdigest(), branch=branch, commit=commit)
    destination.with_suffix('.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    import sys
    package() if '--package' in sys.argv else main()
