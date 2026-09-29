#!/usr/bin/env python3
"""Read-only final S1 preflight before the source-blind runlist is frozen."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

from run_s1_vm import BINARY, EXPECTED_BINARY_SHA, ROOT, TOOLS, sha, verify_assets


def main():
    assert sha(BINARY) == EXPECTED_BINARY_SHA
    configs = json.loads((TOOLS / 'OCB_R2_S1_FROZEN_CONFIGS.json').read_text())
    audit = json.loads((TOOLS / 'static_asset_audit/S1_STATIC_ASSET_AUDIT.json').read_text())
    assert len(configs) == 8 and len(audit) == 12
    assert not ROOT.exists() or not any(ROOT.iterdir()), 'S1 outputs exist before freeze'
    for run_id, config in configs.items():
        entry = audit[int(config['config_index'])]
        assert entry['house'] in ('House01','House02')
        verify_assets(entry, config)
        assert config['parameters']['results_location'] == str(ROOT / run_id)
    print(json.dumps({'configs_preflight_pass':len(configs),'h03_status':'SEALED_NOT_RUN',
                      'binary_sha256':sha(BINARY),'root_free_bytes':shutil.disk_usage('/').free}))


if __name__ == '__main__':
    main()
