"""Compare full 3D map parsing against frozen geometry-only candidate slices."""
import csv
import json
from pathlib import Path
from m1_causal.occupancy3d import Occupancy3D


def main():
    root=Path(__file__).resolve().parents[2]
    geom=root/'evidence/cstar_environment_20260906/maps_v1'
    manifests=json.loads((geom/'geometry_manifest.json').read_text())
    report={'contract':'M1_REAL_MAP3D_ALIGNMENT_V1','houses':{},
            'scope':'map/hash/index/candidate support only; no transport, LOS, boundary or wind validation'}
    for house in ('H01','H02','H03'):
        m=manifests[house]
        grid=Occupancy3D.read(root/f'evidence/cstar_m1_maps3d_20260910/{house}.csv')
        assert grid.sha256==m['occupancy_sha256']
        assert grid.dimensions[:2]==(m['expected_width_px'],m['expected_height_px'])
        z=m['z_index']
        count=int((grid.cells[z]==0).sum())
        assert count==m['free_cell_count']
        with (geom/house/'candidate.csv').open() as f:
            points=[(float(r['x']),float(r['y']),m['navigation_height_m']) for r in csv.DictReader(f)]
        indices=[grid.index(p) for p in points]
        assert len(points)==count and len(set(indices))==count
        assert all(grid.is_free(p) and grid.index(p)[2]==z for p in points)
        assert grid.state(tuple(v-1 for v in grid.minimum))==3
        report['houses'][house]={'map_sha256':grid.sha256,'dimensions':grid.dimensions,
            'nav_free_cells':count,'checked_candidates':len(points),'pass':True}
    out=root/'evidence/cstar_m1_real_maps3d_alignment_20260910.json'
    if out.exists():
        raise FileExistsError('refuse to overwrite evidence')
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
