import csv
f='/tmp/gsl_runs_v4/results/raw/M7_full_saisc_pf_VGR_House01_house01_A_s0_20260704T135706571684_fd1ba48_record.csv'
with open(f) as fh:
    r=csv.DictReader(fh).__next__()
    print("Error: %s" % r['final_error_m'])
    print("Min_dist: %s" % r['min_distance_m'])
    print("Est: (%s, %s)" % (r['final_estimate_x'], r['final_estimate_y']))
    print("Src: (%s, %s)" % (r['ground_truth_x'], r['ground_truth_y']))
    print("Term: %s" % r['termination_reason'])
    print("Hits: %s" % r.get('raw_hit_count','?'))
    print("Time: %s" % r['search_time_s'])