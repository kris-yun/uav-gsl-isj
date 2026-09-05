"""Read geometry and spent wind positions only; compare actual GMRF support.

The origin-aligned counterfactual is a geometric check, not an adopted solver.
No gas, source coordinate, bank or new simulated world is read/generated.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import struct
import cv2
import yaml


def f32(x):
    return struct.unpack('f', struct.pack('f', x))[0]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--map', type=Path, required=True)
    p.add_argument('--geometry', type=Path, required=True)
    p.add_argument('--wind', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    cfg = yaml.safe_load(args.map.read_text())
    image_path = args.map.parent / cfg['image']
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None or cfg['negate'] != 0 or cfg['origin'][2] != 0:
        raise ValueError('unsupported map')
    h, w = image.shape
    origin_x, origin_y = cfg['origin'][:2]
    resolution = cfg['resolution']

    def pixel_at(x, y):
        ix, iy = math.floor((x-origin_x)/resolution), math.floor((y-origin_y)/resolution)
        if not 0 <= ix < w or not 0 <= iy < h:
            return {'inside': False, 'free': False}
        value = int(image[h-1-iy, ix])
        # Actual backend considers unknown(-1) free too; report raw pixel value.
        return {'inside': True, 'pixel': value, 'free': value/255 >= 1-cfg['occupied_thresh']}

    with args.geometry.open() as f:
        geometry = list(csv.DictReader(f))
    xs = sorted({float(r['x']) for r in geometry})
    ys = sorted({float(r['y']) for r in geometry})
    dx = f32(xs[1]-xs[0])
    xmin, ymin = f32(xs[0]-dx/2), f32(ys[0]-dx/2)
    details = []
    with args.wind.open() as f:
        for row in csv.DictReader(f):
            if float(row['t_sim_s']) > 240:
                break
            x, y = float(row['x']), float(row['y'])
            ix = int(f32(f32(f32(x)-xmin)/dx))
            iy = int(f32(f32(f32(y)-ymin)/dx))
            index = ix+iy*len(xs)
            if not 0 <= ix < len(xs) or not 0 <= iy < len(ys):
                raise ValueError('point outside field')
            center = geometry[index]
            actual_free = bool(int(center['free']))
            cx, cy = float(center['x']), float(center['y'])
            point_pixel, center_pixel = pixel_at(x,y), pixel_at(cx,cy)
            if actual_free != center_pixel['free']:
                raise ValueError('exported geometry and map pixel disagree')
            # Diagnostic ONLY: same .3 spacing anchored on supplied map origin.
            ax = origin_x + (math.floor((x-origin_x)/dx)+.5)*dx
            ay = origin_y + (math.floor((y-origin_y)/dx)+.5)*dx
            aligned = pixel_at(ax,ay)
            details.append({'step': int(row['step']), 't': float(row['t_sim_s']),
                            'xy': [x,y], 'actual_point': point_pixel,
                            'gmrf_index': index, 'gmrf_center': [cx,cy],
                            'gmrf_center_pixel': center_pixel,
                            'gmrf_accept_geometry': actual_free,
                            'origin_aligned_center': [ax,ay],
                            'origin_aligned_pixel': aligned})
    bad = [r for r in details if not r['gmrf_accept_geometry']]
    report = {'status': 'GEOMETRIC_SUPPORT_AUDIT_ONLY', 'observations': len(details),
              'actual_point_occupied_count': sum(not r['actual_point']['free'] for r in details),
              'actual_gmrf_geometry_rejections': len(bad),
              'origin_aligned_center_rejections': sum(not r['origin_aligned_pixel']['free'] for r in details),
              'gmrf_origin': [xmin,ymin], 'map_origin': [origin_x,origin_y],
              'spacing': dx, 'first_rejection': bad[0] if bad else None,
              'all_rejections': bad,
              'hashes': {str(path): sha(path) for path in [args.map,image_path,args.geometry,args.wind,Path(__file__)]},
              'limitations': ['Center occupancy is not occupancy of the actual sensing point.',
                              'Origin alignment alone does not prove full-cell path/connectivity validity.',
                              'Hypothetical aligned support is not a validated replacement or tuned model.',
                              'No gas/source task utility conclusion follows.']}
    with args.out.open('x') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['all_rejections','hashes']}))


if __name__ == '__main__':
    main()
