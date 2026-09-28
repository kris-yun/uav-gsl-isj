"""Bind the previously chosen four-source/eight-plume development evaluation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    original = ROOT / 'PROPOSED_PRE_DATA_SPLIT_AND_COST.json'
    plan = json.loads(original.read_text())
    bindings = json.loads((ROOT / 'V1_CASE_BINDINGS.json').read_text())
    selected = []
    for wanted in plan['eval_cases']:
        matches = []
        for row in bindings['cases']:
            path = ROOT / 'v1_cases' / row['case_file']
            case = json.loads(path.read_text())
            if all(case[key] == wanted[key] for key in
                   ('house', 'wind', 'source_id', 'historical_seed')):
                if case['split'] != 'eval' or sha(path) != row['sha256']:
                    raise RuntimeError('frozen evaluation case binding drift')
                matches.append({'ordinal': case['ordinal'], 'case_id': case['case_id'],
                                'case_file': 'v1_cases/' + row['case_file'],
                                'case_file_sha256': sha(path),
                                'house': case['house'], 'wind': case['wind'],
                                'source_id': case['source_id'],
                                'historical_seed': case['historical_seed'],
                                'plume_id': case['plume_id']})
        if len(matches) != 1:
            raise RuntimeError('missing or ambiguous frozen eval case')
        selected.extend(matches)
    if sorted(x['ordinal'] for x in selected) != [9, 10, 21, 22, 65, 66, 69, 70]:
        raise RuntimeError('evaluation case IDs changed')
    result = {'status': 'BRG_V1_8_CASE_4_ARM_EVALUATION_FROZEN',
              'prior_split_plan_sha256': sha(original),
              'case_bindings_sha256': sha(ROOT / 'V1_CASE_BINDINGS.json'),
              'arms': ['native_pmfs', 'candidate_gru', 'brg', 'brg_ungated'],
              'sim_budget_s': 300, 'geometric_success_radius_m': .5,
              'primary_metric': 'final Native source-map position estimate within 0.5m',
              'timeout_without_declaration_may_still_be_geometric_success': True,
              'native_planner_and_stop_rules_unchanged': True,
              'cases': selected, 'expected_run_count': 32,
              'stage_p0_ordinals': [9],
              'stage_p1_cumulative_ordinals': [9, 10, 21, 65],
              'stage_full_ordinals': [9, 10, 21, 22, 65, 66, 69, 70],
              'source_truth_used_for_training_or_model_selection': False}
    target = ROOT / 'V1_EVAL8_FROZEN_MANIFEST.json'
    if target.exists():
        if json.loads(target.read_text()) != result:
            raise RuntimeError('existing evaluation freeze drift')
    else:
        target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'cases': len(selected),
                      'runs': result['expected_run_count'], 'sha256': sha(target)}))


if __name__ == '__main__':
    main()
