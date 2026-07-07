import csv, glob, os

# Check what source positions are in the data
for f in sorted(glob.glob('/tmp/gsl_runs_v4/results/raw/*_record.csv')):
    with open(f) as fh:
        r = csv.DictReader(fh).__next__()
        ts = r.get('timestamp','')
        if '2026-07-03' in ts:
            seed = r.get('seed','?')
            err = r.get('final_error_m','?')
            srcx = r.get('ground_truth_x','?')
            srcy = r.get('ground_truth_y','?')
            env = r.get('environment_id','?')
            cfg = r.get('config_id','?')
            print(f'Seed {seed}: src=({srcx},{srcy}) err={err} env={env} cfg={cfg} ts={ts[:19]}')
            break  # just check one

# Check distinct source positions
sources = set()
for f in glob.glob('/tmp/gsl_runs_v4/results/raw/*_record.csv'):
    with open(f) as fh:
        r = csv.DictReader(fh).__next__()
        srcx = r.get('ground_truth_x','?')
        srcy = r.get('ground_truth_y','?')
        sources.add((srcx, srcy))
print(f'\nDistinct source positions: {sources}')
