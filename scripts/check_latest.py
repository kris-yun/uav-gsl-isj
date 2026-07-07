import csv
f='/tmp/gsl_runs_v4/results/raw/M7_full_saisc_pf_VGR_House01_house01_A_s0_20260704T133531421678_fd1ba48_record.csv'
with open(f) as fh:
    r=csv.DictReader(fh).__next__()
    print("Error: %s" % r['final_error_m'])
    print("Min_dist: %s" % r['min_distance_m'])
    print("Success@2m: %s" % r['localized_success_2m'])
    print("Term: %s" % r['termination_reason'])
    print("Time: %s" % r['search_time_s'])