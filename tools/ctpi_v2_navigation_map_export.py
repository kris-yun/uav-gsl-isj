"""Export the already-declared flight-height map, no gas field or source access."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
import yaml


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--occupancy', type=Path, required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--flight-height', type=float, required=True)
    p.add_argument('--wind', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    raw = args.occupancy.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != args.expected_sha256:
        raise ValueError('occupancy differs from archived R4 input identity')
    meta, values = {}, []
    for text in raw.decode().splitlines():
        line = text.strip()
        if not line or line == ';':
            continue
        if line.startswith('#'):
            parts = line.split()
            meta[parts[0].split('(')[0]] = parts[1:]
        else:
            values.extend(map(int, line.split()))
    nx,ny,nz = map(int, meta['#num_cells'])
    origin = list(map(float, meta['#env_min']))
    size = float(meta['#cell_size'][0])
    if len(values) != nx*ny*nz or not set(values) <= {0,1,2}:
        raise ValueError('invalid occupancy array')
    grid = (np.array(values, dtype=np.uint8).reshape(nz,nx,ny) != 0)
    zi = max(0, min(int((args.flight_height-origin[2])/size), nz-1))
    layer = grid[zi]
    # Same x/y convention as bridge occupancy_2d.T.flatten(), then image Y flip.
    image = np.flipud(np.where(layer.T, 0, 255).astype(np.uint8))
    occupied_steps = []
    with args.wind.open() as f:
        rows = [row for row in csv.DictReader(f) if float(row['t_sim_s']) <= 240]
    for row in rows:
        x, y = float(row['x']), float(row['y'])
        ix,iy = int((x-origin[0])/size),int((y-origin[1])/size)
        if not 0<=ix<nx or not 0<=iy<ny or layer[ix,iy]:
            occupied_steps.append(int(row['step']))
    args.out.mkdir()
    image_path=args.out/'navigation_slice.pgm'
    if not cv2.imwrite(str(image_path), image):
        raise IOError('map image export failed')
    mapping={'image':image_path.name, 'resolution':size, 'origin':origin[:2]+[0],
             'negate':0, 'occupied_thresh':.9, 'free_thresh':.1}
    (args.out/'navigation_slice.yaml').write_text(yaml.safe_dump(mapping))
    # Re-read exported map, so the consumer's image path has an exact parity check.
    recovered = np.flipud(cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)).T == 0
    if not np.array_equal(recovered,layer):
        raise ValueError('export changes occupancy')
    report={'status':'ARCHIVED_NAVIGATION_MAP_IDENTITY_AND_EXPORT_PARITY',
            'occupancy_sha256':digest, 'flight_height':args.flight_height,'z_index':zi,
            'nx':nx,'ny':ny,'free':int((~layer).sum()),'occupied':int(layer.sum()),
            'wind_rows':len(rows),'wind_points_blocked_by_navigation_map':occupied_steps,
            'export_sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),
            'wind_sha256':hashlib.sha256(args.wind.read_bytes()).hexdigest(),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'limitations':['No inference about wind validity away from this height.',
                           'No gas payload, bank, source truth or fresh experiment.',
                           'No wind solver origin/occupancy rule changed.']}
    (args.out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
