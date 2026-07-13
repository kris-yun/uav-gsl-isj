#!/usr/bin/env python3
import re, sys

filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
backup = filepath + '.pre_cleanup2'
import shutil
shutil.copy2(filepath, backup)

with open(filepath, 'r') as f:
    lines = f.readlines()

result = []
i = 0

def skip_block(lines, i):
    depth = 0
    started = False
    while i < len(lines):
        if '{' in lines[i]: depth += lines[i].count('{'); started = True
        if '}' in lines[i]: depth -= lines[i].count('}')
        i += 1
        if started and depth <= 0: break
    return i

removed = []
while i < len(lines):
    line = lines[i]
    s = line.strip()
    
    # Patterns to skip entirely
    skip_patterns = [
        'use_bhex_ = getParam', 'use_waz_ = getParam', 'use_sc_ = getParam',
        'use_edpa_ = getParam', 'use_sbd_ = getParam', 'use_ddm_ = getParam',
        'use_wraig_ = getParam', 'DDM::DDMConfig', 'ddm_cfg.',
        'ddm_stopping_ = DDM', 'wraig_cfg_.beta = getParam',
        'wraig_cfg_.n_ensemble', 'wraig_.init', 'eig_threshold_ = getParam',
        'cusum_threshold_ = getParam', 'cusum_drift_ = getParam',
        'SBD DEBUG', 'use_eig_height_ = false', 'eig_height_posterior_[',
        'eig_selected_height_', 'eig_height_update_count_',
    ]
    
    if any(p in s for p in skip_patterns):
        removed.append(f'L{i+1}: {s[:60]}')
        i += 1
        continue
    
    # DDM/WRAIG combined log line
    if 'GSL_INFO' in s and 'DDM' in s and 'W-RAIG' in s:
        i += 1; continue
    
    # SBD init block
    if '// SBD initialization' in s:
        i += 1; continue
    if 'if (use_sbd_)' in s and 'eig_field_' in s:
        i = skip_block(lines, i); continue
    
    # BH-EX + WAZ init combined line
    if 'bhex_stagnation_count_ = 0' in s and 'waz_phase_' in s:
        i += 1; continue
    if 'bhex_temperature_ = 2.0f' in s and 'bhex_best_conc_' in s:
        i += 1; continue
    if 'bhex_jump_pending_ = false' in s:
        i += 1; continue
    
    # SC init combined line
    if 'sc_mode_ = 0' in s and 'sc_cast_dir_' in s:
        i += 1; continue
    if 'sc_consecutive_hits_ = 0' in s:
        i += 1; continue
    if 'sc_source_est_count_' in s:
        i += 1; continue
    
    # Full functions to remove
    fn_patterns = [
        'void OPGSL::updatePosteriorEventDriven',
        'OPGSL::AdaptiveEIGResult OPGSL::computeAdaptiveEIG',
        'float OPGSL::computeEIGGlobal',
        'float OPGSL::computeEIGLocal',
        'float OPGSL::computeCredibleRegionRadius',
        'void OPGSL::computeEIGField',
        'void OPGSL::computeWRAIGField',
        'float OPGSL::computePosteriorKL',
        'void OPGSL::bhexCheckStagnation',
        'void OPGSL::wazExplore',
        'void OPGSL::scStep',
        'void OPGSL::updateHeightPosterior',
        'float OPGSL::selectBestHeight',
    ]
    
    matched = False
    for p in fn_patterns:
        if p in s:
            i = skip_block(lines, i)
            removed.append(f'FN: {p}')
            matched = True
            break
    if matched:
        continue
    
    # Inline block patterns to skip
    inline_patterns = [
        ('if (use_ddm_)', 0),
        ('// DDM', 0),
        ('if (use_bhex_)', 0),
        ('bhexCheckStagnation', 0),
        ('if (use_waz_)', 0),
        ('wazExplore', 0),
        ('if (use_sc_)', 0),
        ('scStep(', 0),
        ('if (!use_wraig_', 0),
        ('computeWRAIGField', 0),
        ('wraig_field_', 0),
        ('if (use_sbd_)', 0),
        ('edpa_should_stop_', 0),
        ('use_event_driven_posterior_', 0),
        ('updatePosteriorEventDriven', 0),
        ('computeAdaptiveEIG', 0),
        ('cr_stopping_', 0),
        ('computeCredibleRegionRadius', 0),
        ('use_eig_height_', 0),
        ('updateHeightPosterior', 0),
        ('selectBestHeight', 0),
        ('eig_selected_height_', 0),
        ('DDM-STOP', 0),
    ]
    
    matched2 = False
    for p, _ in inline_patterns:
        if p in s and '{' in s:
            i = skip_block(lines, i)
            removed.append(f'INLINE: {p}')
            matched2 = True
            break
        elif p in s:
            i += 1
            removed.append(f'LINE: {p}')
            matched2 = True
            break
    if matched2:
        continue
    
    result.append(line)
    i += 1

with open(filepath, 'w') as f:
    f.writelines(result)

print(f'Cleaned: {len(lines)} -> {len(result)} lines')
print(f'Removed {len(removed)} items')
for r in removed[:20]:
    print(f'  {r}')
if len(removed) > 20:
    print(f'  ... and {len(removed)-20} more')
