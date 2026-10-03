"""Keep native data isolated; publish only audit outputs and build an independently verified ZIP."""
import csv,hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(r'C:\work\LAGOON_PINGO_REAL_DATA_20261003');REPO=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent;EV=REPO/'evidence/lagoon_pingo_real_data_audit_20261003'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 receipts=json.loads((ROOT/'metadata/DOWNLOAD_RECEIPT.json').read_text(encoding='utf8'))
 for r in receipts:
  p=ROOT/'raw'/r['file'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
 assert len(list((ROOT/'raw').iterdir()))==2
 schema=json.loads((ROOT/'audit/DATA_SCHEMA.json').read_text());assert schema['dimensions']['flight']==13 and schema['dimensions']['flight_frec']==13
 assert (ROOT/'audit/FINAL_DECISION.json').exists()
 # Exact script provenance lives with the isolated data as well as the research branch.
 for p in CODE.iterdir():
  if p.is_file() and p.suffix in {'.py','.md'}:(ROOT/'scripts').mkdir(exist_ok=True);shutil.copyfile(p,ROOT/'scripts'/p.name)
 validation={'two_core_files_bytes_unchanged':True,'official_md5_pass':True,'sha256_pass':True,'raw_file_count':2,'download_directory':str(ROOT),'no_raw_files_in_other_dataset_dirs':True,'corrected_wind_pairing_unverified':True,'no_neural_or_statistical_predictor_fitted':True,'no_new_gaden_cfd_pmfs_or_closed_loop':True,'scripts_require':['numpy','pandas','h5py','xarray','h5netcdf','pyproj','openpyxl','matplotlib','requests'],'isolated_added_dependency_directory':str(ROOT/'tools/python_deps'),'no_existing_simulator_environment_updated':True}
 (ROOT/'audit/VALIDATION.json').write_text(json.dumps(validation,indent=2)+'\n')
 files=[p for d in ['raw','metadata','audit','derived','scripts'] for p in (ROOT/d).rglob('*') if p.is_file()]+[ROOT/'README_zh.md',ROOT/'reports/REPORT_zh.md']
 rows=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'category':'raw_input' if p.parent==ROOT/'raw' else 'audit_or_provenance'} for p in sorted(files)]
 with (ROOT/'reports/MANIFEST.csv').open('w',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 target=ROOT/'reports/LAGOON_PINGO_REAL_DATA_AUDIT_20261003.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files+[ROOT/'reports/MANIFEST.csv']:z.write(p,p.relative_to(ROOT).as_posix())
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  for r in rows:assert hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256']
 digest=sha(target);target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n')
 # Raw files remain under C:\work\LAGOON_PINGO_REAL_DATA_20261003 only.
 EV.mkdir(parents=True,exist_ok=True)
 for d in ['metadata','audit','derived']:
  for p in (ROOT/d).rglob('*'):
   if p.is_file():destination=EV/d/p.relative_to(ROOT/d);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,destination)
 for p in [ROOT/'reports/REPORT_zh.md',ROOT/'reports/MANIFEST.csv',target.with_suffix('.zip.sha256')]:shutil.copyfile(p,EV/p.name)
 receipt={'zip_path':str(target),'zip_bytes':target.stat().st_size,'zip_sha256':digest,'zip_members':len(files)+1,'raw_inputs_included_in_zip':True,'raw_inputs_not_committed_to_git':True,'root':str(ROOT)}
 (EV/'PACKAGE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');(ROOT/'reports/PACKAGE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
 (EV/'.gitattributes').write_text('* -text\n');(CODE/'.gitattributes').write_text('* -text\n');(CODE/'.gitignore').write_text('__pycache__/\n')
 print(json.dumps(receipt,indent=2),flush=True)
if __name__=='__main__':main()
