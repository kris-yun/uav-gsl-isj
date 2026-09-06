"""Package already-extracted evidence; no raw queries, training or selection."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'evidence/cstar_controlled_assets_20260907_r2'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    assert not args.out.exists(), 'ARCHIVE_ALREADY_EXISTS'
    trace = json.loads((ASSETS / 'CONTROLLED_TRACE_AUDIT.json').read_text())
    assert trace['pass']
    counts = {k: sum(r[k] for r in trace['per_realization']) for k in
              ('route_hit_cases', 'route_no_hit_cases', 'same_context_different_first_hit_groups',
               'same_context_different_gas_sequence_groups')}
    immediate, persistence, cases = 0, 0, 0
    for path in sorted((ASSETS / 'realizations').glob('*/t*_outcome.jsonl')):
        future = [json.loads(s) for s in path.read_text().splitlines()]
        history = [json.loads(s) for s in (path.parent / 'measured_history.jsonl').read_text().splitlines()]
        step = int(path.name[1:3])*5
        target = next((i for i,f in enumerate(future) if f['gas_ppm'] > 0.1), 20)
        prediction = 0 if history[step-1]['gas_ppm'] > 0.1 else 20
        immediate += target == 0
        persistence += target == prediction
        cases += 1
    checkpoint = {'contract': 'CSTAR_CONTROLLED_DATA_CHECKPOINT_20260907',
        'packaging_source_git_sha': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'status': 'CONTROLLED_DATA_QUALIFIED_NOT_MODEL_UTILITY',
        'realizations': 12, 'seed': 12, 'm1_prefixes': 180, 'm2_cases': cases,
        'same_context_route_groups': 84, **counts, 'immediate_hit_cases': immediate,
        'posthoc_no_route_no_source_persistence_exact_labels': persistence,
        'posthoc_persistence_fraction': persistence/cases,
        'm1': 'PICR controlled causal screen not trained or evaluated',
        'm2': 'CPO not trained or evaluated; frozen first-hit labels have weak intervention contrast',
        'm3': 'not evaluated', 'production_closed_loop_started': False,
        'wind_correction': 'numeric header-to-file binding and corrected H01 live ROS probe PASS',
        'new_seeds_or_realizations_generated': False, 'deployment_predictive_bank_required': False,
        'next': 'M1 controlled causal-screen implementation; M2 route/source-free persistence plus frozen physics/FOPDT controls before gain interpretation',
        'do_not': 'no outcome-driven route/split/horizon/threshold rescue tuning; no multiseed expansion'}
    (ASSETS / 'CHECKPOINT.json').write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    groups = ['evidence/cstar_controlled_assets_20260907', 'evidence/cstar_controlled_assets_20260907_r2',
              'evidence/cstar_controlled_routes_20260907', 'evidence/cstar_environment_20260906',
              'evidence/cstar_raw_provenance_20260906', 'experiments/ctpi_cstar']
    files = {p for name in groups for p in (ROOT/name).rglob('*') if p.is_file()
             and '__pycache__' not in p.parts and p.name != 'BUNDLE_SHA256SUMS'}
    tools = ['cstar_audit_controlled_data.py', 'cstar_extract_controlled_assets.py', 'cstar_freeze_controlled_routes.py',
             'cstar_collect_provenance_metadata.py', 'cstar_inspect_wind_provenance.py',
             'cstar_reverify_controlled_bundle.py', 'cstar_package_controlled_evidence.py',
             'selftest_cstar_controlled_routes.py', 'cstar_numeric_wind_raw_query.cpp',
             'cstar_build_numeric_wind_query.sh', 'cstar_numeric_wind_query_build.json',
             'cstar_environment_vm_dependencies.sh', 'cstar_run_environment_house.py']
    files.update(ROOT/'tools'/name for name in tools)
    files.update(ROOT/'docs'/name for name in ['CSTAR_CONTROLLED_ROUTE_EXTRACTION_V1_20260907.md',
                 'CSTAR_WIND_INDEX_CORRECTION_20260907.md', 'CSTAR_CONTROLLED_DATA_QUALIFICATION_CODEX_HANDOFF_20260906.md'])
    files.add(ROOT / 'closed_loop/ctpi/cstar_environment_runtime_probe.py')
    files.add(ROOT / 'closed_loop/ctpi/ctpi_v2_ingress.py')
    index = ASSETS / 'BUNDLE_SHA256SUMS'
    index.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n'
                            for p in sorted(files)), encoding='utf-8')
    files.add(index)
    with tarfile.open(args.out, 'x:gz') as archive:
        for p in sorted(files):
            archive.add(p, arcname=p.relative_to(ROOT).as_posix(), recursive=False)
    print(json.dumps({'files_hashed':len(files)-1, 'archive':str(args.out),
                      'sha256':hashlib.sha256(args.out.read_bytes()).hexdigest(), 'checkpoint':checkpoint},indent=2))


if __name__ == '__main__':
    main()
