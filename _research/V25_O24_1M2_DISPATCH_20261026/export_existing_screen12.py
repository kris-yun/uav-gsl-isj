#!/usr/bin/env python3
"""Verify and copy existing exact SCREEN12 archives to a new replay directory.

No ROS, no new measurements, no candidate truncation, no modification of inputs.
Each archive must match its registered outer SHA-256 before any member is read.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import stat
import sys
import zipfile
from export_o24_protocol import digest, require, write_new, load_json


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive-root', required=True, help='Folder containing the existing full_runs ZIPs')
    ap.add_argument('--out-root', required=True, help='New directory; fails if it exists')
    ap.add_argument('--all-roles', action='store_true', help='Also export excluded-source diagnostics, kept separately')
    args = ap.parse_args()
    protocol = load_json(pathlib.Path(__file__).with_name('O24_BASELINE_PROTOCOL_LOCK.json'))
    legal = set(protocol['actual_baseline_lock']['legal_source_roles'])
    source, target = pathlib.Path(args.archive_root).resolve(), pathlib.Path(args.out_root).resolve()
    require(source not in target.parents and source != target, 'Output must be outside input archive directory')
    require(not target.exists(), 'Output already exists; choose a new receipt directory')
    original_by_role = {r['role']:r for r in protocol['frozen_cases']}
    plan = []
    for r in protocol['existing_run_archive_index']:
        if not args.all_roles and r['role'] not in legal:
            continue
        names = [pathlib.PurePosixPath(r['archive_in_bundle']).name,
                 pathlib.PureWindowsPath(original_by_role[r['role']]['full_original_archive']['archive']).name]
        candidates = [source/n for n in dict.fromkeys(names)]
        candidates += [source/pathlib.PurePosixPath(r['archive_in_bundle'])]
        p = next((p for p in candidates if p.is_file()), None)
        require(p is not None, r['role'] + ': missing registered archive, first recover from existing local package')
        require(digest(p) == r['archive_sha256'], r['role'] + ': archive hash mismatch')
        with zipfile.ZipFile(p) as z:
            seen = set()
            total = 0
            for info in z.infolist():
                n = pathlib.PurePosixPath(info.filename)
                require(not n.is_absolute() and '..' not in n.parts and '\\' not in info.filename and ':' not in info.filename,
                        r['role'] + ': unsafe archive path')
                require(not stat.S_ISLNK(info.external_attr >> 16), 'Symlink archive entry rejected')
                require(info.filename not in seen, 'Duplicate archive member rejected')
                seen.add(info.filename)
                total += info.file_size
            require(total <= 16 * 1024**3, 'Archive exceeds lightweight dispatch extraction limit')
        plan.append((r,p,total))
    target.mkdir(parents=True, exist_ok=False)
    receipt = {'status':'EXACT_EXISTING_ARCHIVES_EXPORTED_NO_NEW_RUN', 'new_ROS_runs':0,
               'truth_visibility':'Original evidence includes evaluation truth; consumers must construct a causal input view before fitting/inference', 'roles':[]}
    for r,p,total in plan:
        role_root = target / ('legal' if r['role'] in legal else 'excluded_diagnostic') / r['role']
        role_root.mkdir(parents=True, exist_ok=False)
        members = []
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                dst = role_root / pathlib.PurePosixPath(info.filename)
                if info.is_dir():
                    dst.mkdir(parents=True, exist_ok=True)
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as sf, dst.open('xb') as df:
                    shutil.copyfileobj(sf,df,length=1024*1024)
                members.append({'path':dst.relative_to(role_root).as_posix(),'bytes':dst.stat().st_size,'sha256':digest(dst)})
        receipt['roles'].append({'role':r['role'],'source_domain':r['source_domain'],'archive_sha256':r['archive_sha256'],
                                 'uncompressed_bytes':total,'files':members})
    write_new(target/'REPLAY_EXPORT_RECEIPT.json', receipt)
    print(json.dumps({'status':receipt['status'],'roles':len(plan),'out_root':str(target),'new_ROS_runs':0},ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as e:
        print(json.dumps({'status':'REJECT_NO_NEW_RUN','error':str(e)},ensure_ascii=False),file=sys.stderr)
        sys.exit(2)
