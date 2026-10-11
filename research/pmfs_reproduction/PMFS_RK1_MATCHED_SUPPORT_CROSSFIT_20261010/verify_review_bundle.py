"""Read-only self-contained PRO/RK0 review bundle verifier.

Default hashes every declared member and recognized nested member manifest.
--deep calls RK0_NEW/verify_rk0_independent.py:verify(root,m2).
With explicit external --out, --deep also runs the saved-field PRO scalar
recomputation in a new external scratch directory; without --out it skips PRO.
No producer, simulation, old verify_combined or CLI experiment is invoked.
An optional JSON output must be outside the bundle and must be a new file.
"""
import sys
sys.dont_write_bytecode=True
import argparse,contextlib,hashlib,importlib.util,io,json,os,re,stat,time
from pathlib import Path,PurePosixPath

HEX=re.compile(r'^[0-9a-fA-F]{64}$')
MEMBER_MANIFEST_NAMES={'SHA256SUMS.json','SHA256_MANIFEST.json','SHA256.json','SCORING_CONTRACT_SHA256.json'}
REQUIRED_DIRECTORIES=('PARENT_M2M3_FROZEN','PRO_REVIEW','RK0_NEW')

def absolute_path(path,strict=False):
    """Canonical absolute Path; use extended Win32 names for all file operations.

    Main, nested and external paths must use the same representation so that
    containment checks do not compare a normal drive path with its extended
    spelling. Prefix before resolve, allowing strict checks beyond MAX_PATH.
    """
    candidate=Path(path)
    if os.name=='nt':
        name=os.path.abspath(os.fspath(candidate))
        if not name.startswith('\\\\?\\'):
            name='\\\\?\\UNC\\'+name[2:] if name.startswith('\\\\') else '\\\\?\\'+name
        candidate=Path(name)
    return candidate.resolve(strict=strict)

def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()

def no_duplicate_keys(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate JSON key: '+str(key))
        result[key]=value
    return result

def read_json(path):
    with path.open(encoding='utf-8-sig') as stream:
        return json.load(stream,object_pairs_hook=no_duplicate_keys)

def normalized_relative(name):
    if not isinstance(name,str) or not name:raise ValueError('Empty/non-string manifest path')
    if '\x00' in name or any(ord(c)<32 for c in name):raise ValueError('Control character in manifest path')
    normalized=name.replace('\\','/')
    if normalized.startswith('/') or ':' in normalized:raise ValueError('Absolute/drive/URI path prohibited: '+name)
    parts=normalized.split('/')
    if any(p in ('','.','..') for p in parts):raise ValueError('Non-canonical/traversing manifest path: '+name)
    if any(p.endswith((' ','.')) for p in parts):raise ValueError('Windows-ambiguous trailing dot/space path: '+name)
    if any(any(c in p for c in '<>|?*') for p in parts):raise ValueError('Unsafe filename character: '+name)
    if PurePosixPath(normalized).is_absolute():raise ValueError('Absolute path prohibited: '+name)
    return normalized

def reject_link(path):
    info=path.lstat()
    reparse=bool(getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400))
    if stat.S_ISLNK(info.st_mode) or reparse:raise ValueError('Symlink/junction/reparse entry prohibited: '+str(path))

def safe_member(base,name):
    normalized=normalized_relative(name);base=absolute_path(base,strict=True)
    target=base.joinpath(*normalized.split('/'))
    for parent in (target,*target.parents):
        if parent==base:break
        if parent.exists():reject_link(parent)
    resolved=target.resolve(strict=True)
    if not resolved.is_relative_to(base):raise ValueError('Resolved path escapes manifest scope: '+name)
    if not resolved.is_file():raise ValueError('Manifest member is not a regular file: '+name)
    return normalized,resolved

def inventory(root):
    actual={}
    for current,dirs,files in os.walk(root,followlinks=False):
        folder=Path(current)
        for name in dirs:reject_link(folder/name)
        for name in files:
            path=folder/name;reject_link(path)
            if not path.is_file():raise ValueError('Non-regular member: '+str(path))
            relative=normalized_relative(path.relative_to(root).as_posix())
            if relative in actual:raise ValueError('Duplicate actual normalized member: '+relative)
            actual[relative]=path
    return actual

def manifest_entries(path):
    data=read_json(path);entries=[]
    if isinstance(data,dict):
        # These member manifests use the flat path -> SHA256 schema.
        if not all(isinstance(value,str) and HEX.fullmatch(value) for value in data.values()):
            raise ValueError('Unsupported member-manifest mapping schema: '+str(path))
        entries=[(name,digest,None) for name,digest in data.items()]
    elif isinstance(data,list):
        for row in data:
            if not isinstance(row,dict):raise ValueError('Non-object manifest list entry: '+str(path))
            name=row.get('path',row.get('file'));digest=row.get('sha256',row.get('SHA256'))
            size=row.get('size_bytes',row.get('bytes'))
            if size is not None and (isinstance(size,bool) or not isinstance(size,int) or size<0):
                raise ValueError('Invalid declared byte count: '+str(path))
            entries.append((name,digest,size))
    else:raise ValueError('Unsupported member-manifest JSON schema: '+str(path))
    seen=set();normalized=[]
    for name,digest,size in entries:
        rel=normalized_relative(name)
        if rel in seen:raise ValueError('Duplicate normalized manifest path: '+rel)
        seen.add(rel)
        if not isinstance(digest,str) or not HEX.fullmatch(digest):raise ValueError('Invalid SHA256: '+rel)
        normalized.append((rel,digest.lower(),size))
    return normalized

def verify_manifest(path,root,hash_cache):
    entries=manifest_entries(path);count=0;declared=[]
    for name,expected,size in entries:
        normalized,target=safe_member(path.parent,name)
        if not target.is_relative_to(root):raise ValueError('Nested manifest escapes bundle: '+normalized)
        digest=hash_cache.get(target)
        if digest is None:digest=sha(target);hash_cache[target]=digest
        if digest!=expected:raise AssertionError('SHA256 mismatch: '+str(path.relative_to(root))+' -> '+normalized)
        if size is not None and target.stat().st_size!=size:raise AssertionError('Byte-size mismatch: '+normalized)
        declared.append(normalized);count+=1
    return dict(manifest=path.relative_to(root).as_posix(),declared_members=count,all_declared_hashes_match=True),declared

def is_member_manifest(path):
    return path.name in MEMBER_MANIFEST_NAMES or path.name.endswith('_SHA256SUMS.json')

def check_all_hashes(root):
    actual=inventory(root);main=root/'SHA256SUMS.json'
    if not main.is_file():raise FileNotFoundError('Main SHA256SUMS.json missing')
    main_entries=manifest_entries(main)
    declared={name for name,_,_ in main_entries};expected=set(actual)-{'SHA256SUMS.json'}
    if 'SHA256SUMS.json' in declared:raise ValueError('Main manifest must exclude only itself, not self-hash')
    if declared!=expected:
        raise AssertionError('Main manifest coverage mismatch; undeclared='+repr(sorted(expected-declared))+'; missing='+repr(sorted(declared-expected)))
    hashes={};main_result,_=verify_manifest(main,root,hashes);nested=[]
    for name in sorted(actual):
        path=actual[name]
        if path==main or not is_member_manifest(path):continue
        record,_=verify_manifest(path,root,hashes);nested.append(record)
    return dict(main_manifest=main_result,actual_files_including_main=len(actual),main_members_checked=len(main_entries),main_exclusion='SHA256SUMS.json only; verifier and every nested manifest included',nested_member_manifests=nested,nested_manifests_checked=len(nested),nested_declared_members_checked=sum(r['declared_members'] for r in nested),unique_file_hashes_computed=len(hashes)),actual

def deep_rk0(root):
    rk0=root/'RK0_NEW';m2=root/'PARENT_M2M3_FROZEN/M2_FROZEN';source=rk0/'verify_rk0_independent.py'
    if not source.is_file():raise FileNotFoundError('RK0_NEW/verify_rk0_independent.py missing for --deep')
    if not m2.is_dir():raise FileNotFoundError('PARENT_M2M3_FROZEN/M2_FROZEN missing for --deep')
    captured_out=io.StringIO();captured_err=io.StringIO()
    with contextlib.redirect_stdout(captured_out),contextlib.redirect_stderr(captured_err):
        spec=importlib.util.spec_from_file_location('review_bundle_rk0_independent',source)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        if not callable(getattr(module,'verify',None)):raise ValueError('Independent verifier has no verify(root,m2) function')
        result,tables=module.verify(rk0,m2)
    return dict(call='RK0_NEW/verify_rk0_independent.py:verify(RK0_NEW,PARENT_M2M3_FROZEN/M2_FROZEN)',verifier_SHA256=sha(source),result=result,table_row_counts={name:len(rows) for name,rows in tables.items()},captured_stdout_characters=len(captured_out.getvalue()),captured_stderr_characters=len(captured_err.getvalue()),bytecode_generation=False,producer_and_old_verify_combined_not_called=True)

def deep_pro_scalar(root,scratch):
    """Pure saved-field arithmetic; any generated audit tables stay outside bundle."""
    root=absolute_path(root,strict=True)
    scratch=absolute_path(scratch,strict=False)
    if scratch.is_relative_to(root):raise ValueError('PRO scalar scratch must be outside bundle')
    if scratch.exists():raise FileExistsError('PRO scalar scratch must be new, not overwritten')
    source=root/'PRO_REVIEW/independent_scalar_readout_check.py'
    if not source.is_file():raise FileNotFoundError('PRO independent scalar verifier missing')
    reference=root/'PRO_REVIEW/handoff/new_diagnostics'
    names=('SAME_BANK_SAME_SCORER_MARGINS.csv','READOUT_MASK_DENOMINATOR_FACTORIAL.csv')
    for name in names:
        if not (reference/name).is_file():raise FileNotFoundError('Canonical PRO scalar reference missing: '+name)
    target=scratch/'handoff/new_diagnostics';target.mkdir(parents=True,exist_ok=False)
    copied=[]
    for name in names:
        data=(reference/name).read_bytes();(target/name).write_bytes(data)
        copied.append(dict(canonical_member=(reference/name).relative_to(root).as_posix(),copied_SHA256=sha(target/name)))
    generated=scratch/'independent_recompute';captured_out=io.StringIO();captured_err=io.StringIO()
    with contextlib.redirect_stdout(captured_out),contextlib.redirect_stderr(captured_err):
        spec=importlib.util.spec_from_file_location('review_bundle_pro_independent_scalar',source)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        if not callable(getattr(module,'run',None)):raise ValueError('PRO scalar verifier has no run(parent,out) function')
        result=module.run(root/'PARENT_M2M3_FROZEN',generated)
    return dict(status='COMPLETED_PRO_INDEPENDENT_SCALAR_RECOMPUTATION',verifier_SHA256=sha(source),scratch=str(scratch),copied_canonical_references=copied,result=result,captured_stdout_characters=len(captured_out.getvalue()),captured_stderr_characters=len(captured_err.getvalue()),package_files_modified=False,new_physics=0)

def verify_bundle(package:Path,deep=False,pro_scalar_scratch=None):
    start=time.perf_counter();root=absolute_path(package,strict=True)
    if not root.is_dir():raise ValueError('Bundle path must be a directory')
    for folder in REQUIRED_DIRECTORIES:
        path=root/folder
        if not path.is_dir():raise FileNotFoundError('Required bundle directory missing: '+folder)
        reject_link(path)
    integrity,_=check_all_hashes(root)
    result=dict(status='PASS_SELF_CONTAINED_REVIEW_BUNDLE',bundle=str(root),integrity=integrity,deep_requested=bool(deep),physical_experiments=0,new_LOS=0,package_modified=False,old_version_literal_not_used=True)
    if deep:
        result['independent_RK0']=deep_rk0(root)
        result['independent_PRO_scalar']=deep_pro_scalar(root,pro_scalar_scratch) if pro_scalar_scratch else dict(status='NOT_RUN_NO_EXPLICIT_EXTERNAL_OUTPUT',reason='PRO scalar verifier emits audit tables; --deep with explicit --out permits outside-bundle scratch only.')
        after,_=check_all_hashes(root)
        if after!=integrity:raise AssertionError('Package changed during deep verification')
        result['integrity_after_deep']='PASS_ALL_DECLARED_HASHES_AND_MEMBER_COVERAGE_UNCHANGED'
    result['wall_seconds']=time.perf_counter()-start
    return result

def output_destination(path,root):
    destination=absolute_path(path,strict=False);root=absolute_path(root,strict=True)
    if destination.is_relative_to(root):raise ValueError('--out must be outside the bundle')
    if destination.exists():raise FileExistsError('--out must be a new file; refusing overwrite')
    return destination

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package','--root',dest='package',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--deep',action='store_true');parser.add_argument('--out',type=Path)
    args=parser.parse_args();destination=None
    try:
        if args.out:destination=output_destination(args.out,args.package)
        scratch=destination.parent/(destination.stem+'_pro_scalar_scratch') if args.deep and destination else None
        result=verify_bundle(args.package,args.deep,scratch);code=0
    except Exception as error:
        result=dict(status='FAIL_SELF_CONTAINED_REVIEW_BUNDLE',error_type=type(error).__name__,error=str(error),package_modified=False,physical_experiments=0)
        code=1
    if destination:
        try:
            destination.parent.mkdir(parents=True,exist_ok=True)
            with destination.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
        except Exception as error:
            result['external_output_error']=str(error);code=1
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return code

if __name__=='__main__':raise SystemExit(main())
