"""Read-only RK1 + frozen RK0/PRO review-bundle verifier.

Every file except the new root manifest must be covered by its SHA256.
The renamed original RK0 root manifest is separately locked byte-for-byte;
all 1848 original members are checked against that immutable manifest.
--deep invokes only the RK1 independent cache-only arithmetic checker.
--parent-deep invokes the preserved RK0 checker and, with an explicit external
--out, the saved-field PRO scalar checker in a new external scratch directory.
No producer, new particle readout, simulation, ROS, SSH or forward is invoked.
"""
import sys
sys.dont_write_bytecode = True
import argparse, contextlib, hashlib, importlib.util, io, json, os, re, stat, time
from pathlib import Path, PurePosixPath

HEX = re.compile(r'^[0-9a-fA-F]{64}$')
MEMBER_MANIFEST_NAMES = {'SHA256SUMS.json', 'SHA256_MANIFEST.json', 'SHA256.json', 'SCORING_CONTRACT_SHA256.json'}
RK0_MANIFEST = 'RK0_ROOT_MANIFEST_FROZEN.json'
RK0_MANIFEST_SHA256 = 'c808546bc326cd0e2a35ed28e212b4bb98922bae66b7ba1a8017f8982d501b0b'
RK0_MEMBER_COUNT = 1848
REQUIRED_DIRECTORIES = ('PARENT_M2M3_FROZEN', 'PRO_REVIEW', 'RK0_NEW', 'RK1_NEW')


def absolute_path(path, strict=False):
    """Use one canonical representation for Win32 files and containment checks."""
    candidate = Path(path)
    if os.name == 'nt':
        name = os.path.abspath(os.fspath(candidate))
        if not name.startswith('\\\\?\\'):
            name = '\\\\?\\UNC\\' + name[2:] if name.startswith('\\\\') else '\\\\?\\' + name
        candidate = Path(name)
    return candidate.resolve(strict=strict)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + str(key))
        result[key] = value
    return result


def read_json(path):
    with path.open(encoding='utf-8-sig') as stream:
        return json.load(stream, object_pairs_hook=no_duplicate_keys)


def normalized_relative(name):
    if not isinstance(name, str) or not name:
        raise ValueError('Empty/non-string manifest path')
    if '\x00' in name or any(ord(c) < 32 for c in name):
        raise ValueError('Control character in manifest path')
    normalized = name.replace('\\', '/')
    if normalized.startswith('/') or ':' in normalized:
        raise ValueError('Absolute/drive/URI path prohibited: ' + name)
    parts = normalized.split('/')
    if any(p in ('', '.', '..') for p in parts):
        raise ValueError('Non-canonical/traversing manifest path: ' + name)
    if any(p.endswith((' ', '.')) for p in parts):
        raise ValueError('Windows-ambiguous trailing dot/space path: ' + name)
    if any(any(c in p for c in '<>|?*') for p in parts):
        raise ValueError('Unsafe filename character: ' + name)
    if PurePosixPath(normalized).is_absolute():
        raise ValueError('Absolute path prohibited: ' + name)
    return normalized


def reject_link(path):
    info = path.lstat()
    reparse = bool(getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))
    if stat.S_ISLNK(info.st_mode) or reparse:
        raise ValueError('Symlink/junction/reparse entry prohibited: ' + str(path))


def safe_member(base, name):
    normalized = normalized_relative(name)
    base = absolute_path(base, strict=True)
    target = base.joinpath(*normalized.split('/'))
    for parent in (target, *target.parents):
        if parent == base:
            break
        if parent.exists():
            reject_link(parent)
    resolved = target.resolve(strict=True)
    if not resolved.is_relative_to(base):
        raise ValueError('Resolved path escapes manifest scope: ' + name)
    if not resolved.is_file():
        raise ValueError('Manifest member is not a regular file: ' + name)
    return normalized, resolved


def inventory(root):
    actual = {}
    folded = set()
    for current, dirs, files in os.walk(root, followlinks=False):
        folder = Path(current)
        for name in dirs:
            reject_link(folder / name)
        for name in files:
            path = folder / name
            reject_link(path)
            if not path.is_file():
                raise ValueError('Non-regular member: ' + str(path))
            relative = normalized_relative(path.relative_to(root).as_posix())
            if relative.casefold() in folded:
                raise ValueError('Case-alias/duplicate actual member: ' + relative)
            folded.add(relative.casefold())
            actual[relative] = path
    return actual


def manifest_entries(path):
    data = read_json(path)
    entries = []
    if isinstance(data, dict):
        if not all(isinstance(value, str) and HEX.fullmatch(value) for value in data.values()):
            raise ValueError('Unsupported member-manifest mapping schema: ' + str(path))
        entries = [(name, digest, None) for name, digest in data.items()]
    elif isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                raise ValueError('Non-object manifest list entry: ' + str(path))
            name = row.get('path', row.get('file'))
            digest = row.get('sha256', row.get('SHA256'))
            size = row.get('size_bytes', row.get('bytes'))
            if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size < 0):
                raise ValueError('Invalid declared byte count: ' + str(path))
            entries.append((name, digest, size))
    else:
        raise ValueError('Unsupported member-manifest JSON schema: ' + str(path))
    seen = set()
    normalized = []
    for name, digest, size in entries:
        rel = normalized_relative(name)
        if rel.casefold() in seen:
            raise ValueError('Case-alias/duplicate normalized manifest path: ' + rel)
        seen.add(rel.casefold())
        if not isinstance(digest, str) or not HEX.fullmatch(digest):
            raise ValueError('Invalid SHA256: ' + rel)
        normalized.append((rel, digest.lower(), size))
    return normalized


def verify_manifest(path, root, hash_cache):
    entries = manifest_entries(path)
    for name, expected, size in entries:
        _, target = safe_member(path.parent, name)
        if not target.is_relative_to(root):
            raise ValueError('Nested manifest escapes bundle: ' + name)
        digest = hash_cache.get(target)
        if digest is None:
            digest = sha(target)
            hash_cache[target] = digest
        if digest != expected:
            raise AssertionError('SHA256 mismatch: ' + str(path.relative_to(root)) + ' -> ' + name)
        if size is not None and target.stat().st_size != size:
            raise AssertionError('Byte-size mismatch: ' + name)
    return dict(manifest=path.relative_to(root).as_posix(), declared_members=len(entries), all_declared_hashes_match=True)


def is_member_manifest(path):
    return path.name in MEMBER_MANIFEST_NAMES or path.name.endswith('_SHA256SUMS.json')


def check_all_hashes(root):
    actual = inventory(root)
    main = root / 'SHA256SUMS.json'
    if not main.is_file():
        raise FileNotFoundError('Main SHA256SUMS.json missing')
    entries = manifest_entries(main)
    declared = {name for name, _, _ in entries}
    expected = set(actual) - {'SHA256SUMS.json'}
    if 'SHA256SUMS.json' in declared:
        raise ValueError('Main manifest must exclude only itself, not self-hash')
    if declared != expected:
        raise AssertionError('Main manifest coverage mismatch; undeclared=' + repr(sorted(expected-declared)) + '; missing=' + repr(sorted(declared-expected)))
    hashes = {}
    main_result = verify_manifest(main, root, hashes)
    frozen = root / RK0_MANIFEST
    if not frozen.is_file() or sha(frozen) != RK0_MANIFEST_SHA256:
        raise AssertionError('Frozen RK0 root manifest bytes changed or missing')
    frozen_entries = manifest_entries(frozen)
    if len(frozen_entries) != RK0_MEMBER_COUNT:
        raise AssertionError('Frozen RK0 manifest member count mismatch')
    frozen_result = verify_manifest(frozen, root, hashes)
    frozen_result['manifest_SHA256'] = RK0_MANIFEST_SHA256
    frozen_result['all_original_1848_members_preserved_bytewise'] = True
    nested = []
    for name in sorted(actual):
        path = actual[name]
        if path in (main, frozen) or not is_member_manifest(path):
            continue
        nested.append(verify_manifest(path, root, hashes))
    return dict(main_manifest=main_result, actual_files_including_main=len(actual), main_members_checked=len(entries), main_exclusion='SHA256SUMS.json only', frozen_RK0=frozen_result, nested_member_manifests=nested, nested_manifests_checked=len(nested), nested_declared_members_checked=sum(r['declared_members'] for r in nested), unique_file_hashes_computed=len(hashes))


def load_module(name, source):
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deep_rk1(root):
    source = root / 'RK1_NEW/verify_rk1.py'
    if not source.is_file():
        raise FileNotFoundError('RK1_NEW/verify_rk1.py missing for --deep')
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        module = load_module('review_bundle_rk1_independent', source)
        if not callable(getattr(module, 'verify', None)):
            raise ValueError('Independent RK1 verifier has no verify function')
        result, tables = module.verify(root / 'RK1_NEW', root)
    return dict(call='RK1_NEW/verify_rk1.py:verify(RK1_NEW,bundle_root)', verifier_SHA256=sha(source), result=result, table_row_counts={name:len(rows) for name,rows in tables.items()}, captured_stdout_characters=len(out.getvalue()), captured_stderr_characters=len(err.getvalue()), bytecode_generation=False, producer_and_new_physics_not_called=True)


def deep_parent(root, scratch):
    source = root / 'verify_review_bundle.py'
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        module = load_module('review_bundle_original_rk0_master', source)
        result = module.verify_bundle(root, deep=True, pro_scalar_scratch=scratch)
    return dict(call='Preserved verify_review_bundle.py:verify_bundle(root,deep=True,pro_scalar_scratch=external)', verifier_SHA256=sha(source), result=result, captured_stdout_characters=len(out.getvalue()), captured_stderr_characters=len(err.getvalue()), old_verifier_unchanged=True)


def verify_bundle(package, deep=False, parent_deep=False, pro_scalar_scratch=None):
    started = time.perf_counter()
    root = absolute_path(package, strict=True)
    if not root.is_dir():
        raise ValueError('Bundle path must be a directory')
    for name in REQUIRED_DIRECTORIES:
        folder = root / name
        if not folder.is_dir():
            raise FileNotFoundError('Required bundle directory missing: ' + name)
        reject_link(folder)
    if pro_scalar_scratch is not None:
        scratch = absolute_path(pro_scalar_scratch, strict=False)
        if scratch.is_relative_to(root):
            raise ValueError('PRO scalar scratch must be outside bundle')
        if scratch.exists():
            raise FileExistsError('PRO scalar scratch must be new; refusing overwrite')
    else:
        scratch = None
    integrity = check_all_hashes(root)
    result = dict(status='PASS_SELF_CONTAINED_RK1_REVIEW_BUNDLE', bundle=str(root), integrity=integrity, RK1_deep_requested=bool(deep), parent_deep_requested=bool(parent_deep), new_physics=0, new_particle_readout=0, package_modified=False)
    if deep:
        result['independent_RK1'] = deep_rk1(root)
    if parent_deep:
        result['independent_parent_RK0_PRO'] = deep_parent(root, scratch)
    if deep or parent_deep:
        after = check_all_hashes(root)
        if after != integrity:
            raise AssertionError('Package changed during deep verification')
        result['integrity_after_deep'] = 'PASS_ALL_HASHES_AND_COVERAGE_UNCHANGED'
    result['wall_seconds'] = time.perf_counter() - started
    return result


def output_destination(path, root):
    destination = absolute_path(path, strict=False)
    root = absolute_path(root, strict=True)
    if destination.is_relative_to(root):
        raise ValueError('--out must be outside bundle')
    if destination.exists():
        raise FileExistsError('--out must be a new file; refusing overwrite')
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', '--root', dest='package', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--deep', action='store_true', help='Independently verify new RK1 cached arithmetic')
    parser.add_argument('--parent-deep', action='store_true', help='Also verify original RK0 and PRO cached arithmetic')
    parser.add_argument('--out', type=Path, help='New JSON file outside bundle; enables external PRO scratch with --parent-deep')
    args = parser.parse_args()
    destination = None
    try:
        if args.out:
            destination = output_destination(args.out, args.package)
        scratch = destination.parent / (destination.stem + '_pro_scalar_scratch') if args.parent_deep and destination else None
        result = verify_bundle(args.package, args.deep, args.parent_deep, scratch)
        code = 0
    except Exception as error:
        result = dict(status='FAIL_SELF_CONTAINED_RK1_REVIEW_BUNDLE', error_type=type(error).__name__, error=str(error), package_modified=False, new_physics=0)
        code = 1
    if destination:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
        except Exception as error:
            result['external_output_error'] = str(error)
            code = 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
