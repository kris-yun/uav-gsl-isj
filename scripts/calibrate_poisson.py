import csv, glob, os, statistics, math

records = []
for f in sorted(glob.glob('/tmp/gsl_runs_v4/results/raw/*_record.csv')):
    with open(f) as fh:
        r = csv.DictReader(fh).__next__()
        src_x = float(r.get('ground_truth_x', 0))
        src_y = float(r.get('ground_truth_y', 0))
        if abs(src_x - 5.0) > 0.1 or abs(src_y - 6.2) > 0.1:
            continue
        min_dist = float(r.get('min_distance_m', 999))
        hit_count = int(r.get('raw_hit_count', 0) or 0)
        sample_count = int(r.get('raw_sample_count', 0) or 0)
        error = float(r.get('final_error_m', 999))
        bout_count = int(r.get('bout_count', 0) or 0)
        if sample_count > 0:
            records.append({
                'min_dist': min_dist,
                'hit_count': hit_count,
                'sample_count': sample_count,
                'error': error,
                'hit_rate': hit_count / sample_count if sample_count > 0 else 0,
                'bouts': bout_count,
            })

print('Total records for (5.0,6.2) scenario: %d' % len(records))
if records:
    for r in records[:15]:
        nd = r['min_dist']
        hc = r['hit_count']
        sc = r['sample_count']
        hr = r['hit_rate']
        er = r['error']
        bo = r['bouts']
        print('  min_d=%.2fm  hits=%d/%d  rate=%.3f  err=%.2fm  bouts=%d' % (nd, hc, sc, hr, er, bo))

    bins = {}
    for r in records:
        d_bin = int(r['min_dist'])
        if d_bin not in bins: bins[d_bin] = []
        bins[d_bin].append(r['hit_rate'])

    print('\nHit rate by distance bin:')
    for d in sorted(bins):
        rates = bins[d]
        print('  d=%d-%dm: N=%d mean_rate=%.3f median=%.3f' % (d, d+1, len(rates), statistics.mean(rates), statistics.median(rates)))

    # Also check: what is the actual detection threshold being used?
    # And what concentration values look like from logs
    print('\nAll hit rates:')
    all_rates = [r['hit_rate'] for r in records]
    print('  Mean=%.3f  Median=%.3f  Min=%.3f  Max=%.3f' % (statistics.mean(all_rates), statistics.median(all_rates), min(all_rates), max(all_rates)))