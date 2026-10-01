"""Finish extraction of the successful first run; never executes GADEN."""
import importlib.util
import json
from pathlib import Path
import shutil
root=Path('/mnt/hgfs/workspace/_vm_worktrees/pmfs3d-o0-20261001')
work=Path('/mnt/hgfs/workspace/PMFS3D_O0_PROJECTED2D_20261001')
spec=importlib.util.spec_from_file_location('gate',root/'research/pmfs3d_o0/pmfs3d_o0_projected2d_gate.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
out=work/'projected2d_runs/S1_A'; real=out/'realization'
assert not (out/'run_metadata.json').exists()
assert len(list(real.glob('iteration_*')))==566
assert 'Filament simulator finished correctly!' in (out/'generation.log').read_text()
occ=Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv')
assert m.sha256(occ)==m.EXPECTED_OCC
shutil.copyfile(occ,real/'OccupancyGrid3D.csv')
assert m.sha256(real/'OccupancyGrid3D.csv')==m.EXPECTED_OCC
origin,dims,cell=m.read_occ_header(occ)
extractor=Path('/home/zyc/rmfe_filament_extractor_omp')
assert m.sha256(extractor)==m.EXPECTED_EXTRACTOR
m.run([str(extractor),str(real),str(real),str(out/'concentration.npy'),str(out/'spatial_metadata.json'),
       repr(origin[0]),repr(origin[1]),repr(cell),'1','0.20',str(dims[0]),str(dims[1]),
       *[str(x) for x in m.TIMES]], log=out/'extract.log')
a=m.np.load(out/'concentration.npy',allow_pickle=False)
assert a.shape==(10,83,119) and m.np.isfinite(a).all() and (a>=0).all()
bank=root/'evidence/causal_compositional_plume_world_model_v1/c0_5_real_gaden_bank'
xyz=json.loads((bank/'geometry/context_metadata.json').read_text())['source_maps']['S1']['xyz_m']
seed=int(m.parse_kv_tsv(bank/'bank_contract.tsv')['seed_A'])
wind=work/'projected2d_wind'
record={'source_xyz':[float(x) for x in xyz], 'seed':seed,'wind_dir':str(wind),
        'wind0_sha256':m.sha256(wind/'wind_iteration_0'),
        'cube_sha256':m.sha256(out/'concentration.npy'),'cube_shape':list(a.shape),
        'generation_log_sha256':m.sha256(out/'generation.log'),
        'extract_log_sha256':m.sha256(out/'extract.log')}
(out/'run_metadata.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
shutil.rmtree(real)
assert (out/'raw_retained').is_dir()
print('S1_A_EXTRACTION_RECOVERED_WITHOUT_GADEN_RERUN')
