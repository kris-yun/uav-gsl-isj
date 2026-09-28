"""Opt-in VGR file route loader for source-blind V1 training coverage only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

TARGET = Path('/home/zyc/brg_closedloop_20260927/vgr_execution_v2/vgr_bridge/vgr_sim_node.py')
EXPECTED = '3c4d4a14d0502655413eae0b6964844b0ad343554b1f1f8b0793d49fdeb0baf0'
BACKUP = TARGET.with_name(TARGET.name + '.pre_brg_v1_coverage_loader_20260928')
FREEZE = Path('/home/zyc/brg_v1_recovery_20260928/coverage_routes/COVERAGE_ROUTE_FREEZE_V2.json')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    original = TARGET.read_bytes()
    if sha(original) != EXPECTED:
        raise RuntimeError('VGR source drift before opt-in coverage loader')
    freeze = json.loads(FREEZE.read_text())
    if freeze['status'] != 'SOURCE_BLIND_COVERAGE_ROUTE_FROZEN_V2':
        raise RuntimeError('coverage route must be frozen before loader installation')
    for record in freeze['records']:
        path = Path(record['route_file'])
        if sha(path.read_bytes()) != record['route_file_sha256']:
            raise RuntimeError('frozen coverage route SHA drift')
    if BACKUP.exists():
        if sha(BACKUP.read_bytes()) != EXPECTED:
            raise RuntimeError('existing VGR backup drift')
    else:
        BACKUP.write_bytes(original)
    text = original.decode('utf-8')
    import_anchor = 'from .mcos_motion_profiles import MotionLimits, generate_profile\n'
    if text.count(import_anchor) != 1:
        raise RuntimeError('VGR motion profile import anchor changed')
    text = text.replace(import_anchor,
        'from .mcos_motion_profiles import MotionLimits, MotionProfile, generate_profile\n'
        'from pathlib import Path\n')
    anchor = '''        profile = generate_profile(
            self.open_loop_profile_name,
            duration_s=self.motion_duration_s,
            dt_s=self.sim_dt_s,
            start_xy_m=(float(self.uav_pos[0]), float(self.uav_pos[1])),
            heading_rad=self.motion_heading_rad,
        )
'''
    replacement = '''        if self.open_loop_profile_name.startswith('brg_v1_file:'):
            route = Path(self.open_loop_profile_name[len('brg_v1_file:'):]).resolve()
            allowed = Path('/home/zyc/brg_v1_recovery_20260928/coverage_routes').resolve()
            if route.parent != allowed or route.name not in {
                'env_0_coverage.npz', 'env_1_coverage.npz', 'env_2_coverage.npz'}:
                raise ValueError('V1 coverage route outside frozen directory')
            with np.load(route, allow_pickle=False) as saved:
                profile = MotionProfile(
                    str(saved['name'].item()), saved['time_s'].copy(),
                    saved['position_xy_m'].copy(), saved['velocity_xy_m_s'].copy(),
                    saved['acceleration_xy_m_s2'].copy(), saved['jerk_xy_m_s3'].copy())
            if (profile.time_s.size != 1501 or
                    abs(profile.time_s[-1] - 300.) > 1e-9 or
                    np.linalg.norm(profile.position_xy_m[0] - self.uav_pos[:2]) > 1e-6):
                raise ValueError('V1 coverage route time/start contract mismatch')
        else:
            profile = generate_profile(
                self.open_loop_profile_name,
                duration_s=self.motion_duration_s,
                dt_s=self.sim_dt_s,
                start_xy_m=(float(self.uav_pos[0]), float(self.uav_pos[1])),
                heading_rad=self.motion_heading_rad,
            )
'''
    if text.count(anchor) != 1:
        raise RuntimeError('VGR motion profile function anchor changed')
    text = text.replace(anchor, replacement)
    compile(text, str(TARGET), 'exec')
    TARGET.write_text(text, encoding='utf-8')
    result = {'status': 'VGR_OPT_IN_COVERAGE_FILE_LOADER_INSTALLED',
              'target': str(TARGET), 'backup': str(BACKUP),
              'original_sha256': EXPECTED, 'patched_sha256': sha(TARGET.read_bytes()),
              'coverage_freeze_sha256': sha(FREEZE.read_bytes()),
              'default_native_profile_branch_changed': False}
    out = Path('/home/zyc/brg_v1_recovery_20260928/VGR_COVERAGE_LOADER_PATCH.json')
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
