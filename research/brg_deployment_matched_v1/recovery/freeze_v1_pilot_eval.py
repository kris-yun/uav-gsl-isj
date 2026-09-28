"""Freeze the already selected three-case Native-only development pilot."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    proposal_path = ROOT / 'quick_pilot_20260928' / 'THREE_CASE_PILOT_PROPOSAL.json'
    proposal = json.loads(proposal_path.read_text(encoding='utf-8'))
    parent_path = ROOT / 'V1_EVAL8_FROZEN_MANIFEST.json'
    if proposal['parent_eval_manifest_sha256'] != sha(parent_path):
        raise RuntimeError('parent eight-case manifest drift')
    parent = json.loads(parent_path.read_text())
    selected = []
    for proposed in proposal['cases']:
        matches = [case for case in parent['cases'] if case['ordinal'] == proposed['ordinal']]
        if len(matches) != 1 or matches[0] != proposed:
            raise RuntimeError('pilot selection differs from frozen parent')
        case_path = ROOT / proposed['case_file']
        if sha(case_path) != proposed['case_file_sha256']:
            raise RuntimeError('pilot case hash drift')
        case = json.loads(case_path.read_text())
        if case['split'] != 'eval' or case['case_id'] != proposed['case_id']:
            raise RuntimeError('pilot case binding drift')
        selected.append(proposed)
    if [x['ordinal'] for x in selected] != [9, 21, 65]:
        raise RuntimeError('pilot selection changed')
    freeze = {
        'status': 'BRG_V1_NATIVE_ONLY_THREE_CASE_PILOT_FROZEN',
        'experiment_identity': 'NATIVE_ONLY_INITIAL_PILOT_NOT_FULL_V1',
        'proposal_sha256': sha(proposal_path),
        'parent_eval_manifest_sha256': sha(parent_path),
        'pretrain_freeze_sha256': sha(ROOT / 'quick_pilot_20260928' / 'PILOT_PRETRAIN_FREEZE.json'),
        'cases': selected,
        'arms': ['native_pmfs', 'candidate_gru', 'brg', 'brg_ungated'],
        'expected_run_count': 12,
        'sim_budget_s': 300,
        'geometric_success_radius_m': 0.5,
        'primary_metric': 'final Native source-map position estimate within 0.5m',
        'timeout_without_declaration_may_still_be_geometric_success': True,
        'native_planner_and_stop_rules_unchanged': True,
        'training_collection': False,
        'fixed_source_blind_coverage': False,
        'source_truth_used_for_training_or_model_selection': False,
        'scope': 'three developmental examples; not a scientific significance gate',
    }
    out = ROOT / 'PILOT_EVAL_FREEZE.json'
    payload = json.dumps(freeze, indent=2) + '\n'
    if out.exists():
        if out.read_text() != payload:
            raise RuntimeError('existing pilot evaluation freeze drift')
    else:
        out.write_text(payload)
    print(json.dumps({'status': freeze['status'], 'cases': len(selected),
                      'runs': freeze['expected_run_count'], 'sha256': sha(out)}))


if __name__ == '__main__':
    main()
