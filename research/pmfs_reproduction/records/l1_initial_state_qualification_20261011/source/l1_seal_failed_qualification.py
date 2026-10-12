"""Seal the interrupted V1 qualification without rebuilding or resampling."""
from pathlib import Path
import datetime, hashlib, json, shutil, time, zipfile

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'outputs/PMFS_L1_INITIAL_STATE_QUALIFICATION_20261011'
SHARE = Path('D:/ZYC/A-gas/workspace/PMFS_L1_INITIAL_STATE_QUALIFICATION_20261011')
REVIEW = OUT.with_name(OUT.name + '_REVIEW')
RECORD = BASE / 'work/pmfs_r3_r5_checkout/research/pmfs_reproduction/records/l1_initial_state_qualification_20261011'


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as r:
        for chunk in iter(lambda: r.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def dump(p, value):
    assert not p.exists(), f'Preserve existing artifact: {p}'
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def main():
    start = time.monotonic()
    assert not REVIEW.exists() and not RECORD.exists()
    before = {p.name: sha(p) for p in OUT.iterdir() if p.is_file()}
    prepared = json.loads((OUT / 'L1_PREP_OUTPUT_SHA256.json').read_text())
    mismatches = [n for n, r in prepared.items() if sha(SHARE / n) != r['sha256']]
    isolated = json.loads((OUT / 'L1_ISOLATED_SOURCE_SHA256.json').read_text())
    mismatches += [n for n, h in isolated.items() if sha(SHARE / n) != h]
    assert not mismatches, mismatches
    old_contract = json.loads((OUT / 'L1_PROSPECTIVE_MODEL_CONTRACT_REV1.json').read_text())
    snapshot = json.loads((OUT / 'L1_RESUMPTION_PROCESS_AND_LIBRARY_RECEIPT.json').read_text())
    assert snapshot['matching_processes'] == [] and not snapshot['worker_binary_exists']
    assert snapshot['pinned_original_library_sha256'] == old_contract['gas_operator']['pinned_library_SHA']
    assert snapshot['root_free_bytes'] >= old_contract['budget']['reserve_bytes']
    prep = json.loads((OUT / 'L1_PREP_GUARD_RECEIPT.json').read_text())
    b1 = json.loads((OUT / 'ATTEMPT1_L1_BUILD_RECEIPT.json').read_text())
    b2 = json.loads((OUT / 'L1_BUILD_RECEIPT.json').read_text())
    build_s = b1['active_wall_s'] + b2['active_wall_s']
    ledger = {
        'UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'previous_conservative_balance_s': 11226.578,
        'same_stage_reservation_debit_s': 1800,
        'remaining_conservative_s': 9426.578,
        'reservation': {'preparation_s': 900, 'build_s': 600, 'gas_batch_TOTAL_s': 300},
        'measured_preparation_s': prep['active_wall_s'], 'measured_build_s': build_s,
        'measured_build_attempts_s': [b1['active_wall_s'], b2['active_wall_s']],
        'measured_gas_forward_s': 0, 'gas_forward_calls': 0, 'native_goals': 0,
        'same_model_technical_repairs_used': 2, 'same_model_technical_repairs_limit': 2,
        'build_attempts': 2, 'metadata_reconstruction_repeated_flow': False,
        'checkpoint_continuation_new_builds': 0, 'checkpoint_continuation_new_references': 0,
        'no_calendar_reset': True, 'network_gap_creates_no_budget': True,
        'unused_reservation_is_not_new_authorization': True,
        'sealing_and_readonly_checks_covered_by_existing_stage_reservation': True,
        'R5': 'STOP_PRESERVED', 'new_trueplant_batches': 0,
    }
    dump(OUT / 'L1_FINAL_BUDGET_LEDGER.json', ledger)
    dump(OUT / 'L1_GO_STOP.json', {
        'verdict': 'L1_V1_INVALID_BOUNDARY_CONTRACT_AND_K2_SAMPLER_FAIL',
        'geometry447': 'PASS_STATIC_SUPPORT_ONLY', 'stored_divergence': 'PASS',
        'boundary': 'FAIL', 'finite_reference': 'FAIL', 'native_build': 'FAIL_LINK_UNRESOLVED',
        'actual_gas_RNG_ppm_validation': 'NOT_STARTED', 'full447_filter': 'NOT_QUALIFIED',
        'native_consumer': 'NOT_CONNECTED', 'gas_calls': 0, 'native_goals': 0,
        'branch': 'STOP_CURRENT_V1', 'research_objective': 'NOT_ACHIEVED',
        'R4': 'ORDINARY_SUFFICIENT_IN_CONTROLLED_TASK_ONLY', 'R5': 'STOP_PRESERVED',
        'next_action': 'Review explicit cumulative repair exception; no new execution authorized by this file',
    })
    dump(OUT / 'L1_REPAIR_AMENDMENT_PROPOSAL.json', {
        'status': 'PROPOSAL_NOT_FROZEN_NOT_EXECUTED',
        'reason': 'Two permitted same-model repairs exhausted; current continuation seals evidence only',
        'base_contract_sha256': sha(OUT / 'L1_PROSPECTIVE_MODEL_CONTRACT_REV1.json'),
        'requested_change': 'One further bounded repair phase, cumulative counter starts at two, never resets',
        'boundary_correction': 'OOB and Obstacle no normal flux; only original marked Outlet open. Preserve native gas StepTowards.',
        'reuse_policy': 'Preserve original bank; prove nested discrete projection before reusing corrected modes; old conditioned paths cannot serve as corrected-boundary samples',
        'build_correction': 'Resolve pinned libbsc and ROS dependencies via existing overlay and exact DT_NEEDED; no installation or original-library overwrite',
        'sampler_policy': 'Keep registered target priors and likelihood. Freeze numerical hyperparameter proposal and MC diagnostics before calculation; no outcome-based choice or relaxed ESS gate',
        'cumulative_stage_limits_s': {'preparation_TOTAL': 900, 'build_TOTAL': 600, 'gas_six_calls_TOTAL': 300},
        'measured_capacity_remaining_s': {'preparation': 900 - prep['active_wall_s'], 'build': 600 - build_s, 'gas': 300},
        'prior_reservation_already_charged_s': 1800, 'remaining_wallet_s': 9426.578,
        'gas_calls_limit': 6, 'new_trueplant_batches': 0, 'native_goals_now': 0,
        'fixed_constraints': ['same447 source support', 'no true source/CFD/plume/future wind', 'no prior/threshold/plant-seed tuning', 'full release0 to322s history', 'RSS1GiB/newdisk8GiB/reserve4GiB/rootwrite64MiB', 'R5_STOP'],
        'failure_policy': 'Stop dependent gas and localization on boundary/statistics/build/resource failure; preserve evidence; no fourth repair inferred',
        'qualification_limit': 'Six cost/RNG pilot forwards never establish full447 Monte Carlo adequacy or innovation',
    })
    dump(OUT / 'L1_SHARED_ASSET_MANIFEST.json', {
        'shared_directory': str(SHARE), 'kept_in_place': True,
        'files': {p.relative_to(SHARE).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
                  for p in sorted(SHARE.rglob('*')) if p.is_file()},
        'gas_realization_bank': False, 'contains_diagnostic_prior_and_unqualified_paths': True,
    })
    REVIEW.mkdir()
    for p in OUT.iterdir():
        if p.is_file() and p.name != 'L1_PAPER_SEARCH_RAW.json':
            shutil.copy2(p, REVIEW / p.name)
    public = REVIEW / 'public_inputs'
    public.mkdir()
    for n in ('OccupancyGrid3D.csv', 'geometry_states.u8', 'native_mask.txt', 'C1B_PAST_LOCAL_WIND.csv',
              'RunningSimulation.original.cpp', 'RunningSimulation.original.hpp', 'L1_GEOMETRY_META.json',
              'wind_times.f64', 'wind_coeff_ref0.f64', 'wind_coeff_ref1.f64', 'L1_EXECUTION_CONFIG.json'):
        shutil.copy2(SHARE / n, public / n)
    sources = REVIEW / 'source'
    sources.mkdir()
    for n in ('L1RunningSimulation.cpp', 'l1_reference_worker.cpp'):
        shutil.copy2(SHARE / n, sources / n)
    shutil.copytree(SHARE / 'gaden', sources / 'gaden')
    for n in ('l1_prepare_wind.py', 'l1_build_reference_sources.py', 'l1_independent_fail_gates.py',
              'l1_seal_failed_qualification.py', 'l1_verify_sealed_review.py'):
        shutil.copy2(BASE / 'work' / n, sources / n)
    authorization = REVIEW / 'authorization'
    authorization.mkdir()
    shutil.copy2(BASE / 'outputs/PMFS_R3_R5_CONTINUOUS_20261011/authorization/CODEX_R3_R5_CONTINUOUS_RESEARCH_CONTRACT_zh.md', authorization)
    dump(REVIEW / 'L1_PAPER_SEARCH_METADATA_ONLY.json', {
        'original_local_sha256': sha(OUT / 'L1_PAPER_SEARCH_RAW.json'),
        'raw_preserved_locally': True, 'abstracts_excluded_from_review': True,
        'records': [{k: v for k, v in r.items() if k not in ('abstract', 'summary', 'text')}
                    for rows in json.loads((OUT / 'L1_PAPER_SEARCH_RAW.json').read_text()).values() for r in rows],
    })
    (REVIEW / 'README_zh.md').write_text(
        '# L1 V1中断任务接续审核包\n\n'
        '本包封存边界合同失败、两参考权重退化和两次构建失败。气体前向0、定位goal0，主创新尚未成立。\n\n'
        '先读 L1_QUALIFICATION_REPORT_zh.md、L1_GO_STOP.json 和 L1_FINAL_BUDGET_LEDGER.json。'
        '追加修复的可审查范围见 L1_REPAIR_AMENDMENT_PROPOSAL.json；该文件只是方案，尚未冻结或执行。\n\n'
        '离线复核：`python source/l1_verify_sealed_review.py .`；需NumPy，不调用ROS或生成风/气体。'
        '独立脚本验证文件SHA、18,377个OOB面、原GADEN边界源码、ESS、观察矩阵秩及依赖拒绝记录。\n\n'
        '155.8MB完整基底保留在原共享目录，位置与SHA见 L1_SHARED_ASSET_MANIFEST.json。'
        '小包包含全部OOB面值、合法历史局部风、公开几何和未合格的两条潜变量路径。'
        '这些不是真实测试CFD或测试羽流，不能用作已资格化概率参考。\n\n'
        '原始第三方论文摘要仅在本地保留；审核包提供元数据、链接与SHA。'
        '未修改旧plant、源、种子、CFD、PMFS或任何旧结果。\n', encoding='utf8')
    preserved = all(sha(OUT / n) == h for n, h in before.items())
    assert preserved
    dump(REVIEW / 'L1_CONTINUATION_SEAL_RECEIPT.json', {
        'UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'original_output_files_preserved': preserved, 'original_output_count': len(before),
        'checked_preparation_and_isolated_source_hashes': len(prepared) + len(isolated),
        'new_flow_or_path_generation': 0, 'new_builds': 0, 'new_gas_calls': 0, 'new_goals': 0,
        'active_seal_s_before_archive': time.monotonic() - start,
    })
    manifest = {p.relative_to(REVIEW).as_posix(): sha(p) for p in sorted(REVIEW.rglob('*')) if p.is_file()}
    dump(REVIEW / 'L1_SHA256.json', manifest)
    archive = REVIEW.with_suffix('.zip')
    assert not archive.exists()
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(REVIEW.rglob('*')):
            if p.is_file(): z.write(p, p.relative_to(REVIEW).as_posix())
    archive.with_suffix('.zip.sha256').write_text(sha(archive) + '  ' + archive.name + '\n', encoding='ascii')
    shutil.copytree(REVIEW, RECORD)
    (RECORD / '.gitattributes').write_bytes(b'* -text\n')
    print(json.dumps({'review': str(REVIEW), 'ZIP': str(archive), 'ZIP_bytes': archive.stat().st_size,
                      'ZIP_SHA256': sha(archive), 'manifest_members': len(manifest),
                      'seal_wall_s': time.monotonic() - start, 'remaining_conservative_s': 9426.578,
                      'new_gas_calls': 0, 'new_goals': 0}, indent=2))


if __name__ == '__main__':
    main()
