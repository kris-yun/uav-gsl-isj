import os
d = "/tmp/uav_gsl_dqa/incremental"
print("=== HOUSE01: BASELINE vs CFAR vs SDR ===")
print(f"{'Seed':>4} {'Baseline':>10} {'BL_st':>5} {'CFAR':>10} {'CF_st':>5} {'SDR':>10} {'SD_st':>5} {'CFAR_delta':>10} {'SDR_delta':>10}")
bl_mean = cfar_mean = sdr_mean = 0.0
bl_ok = cfar_ok = sdr_ok = 0
n = 0
for s in range(10):
    bl_f = os.path.join(d, f"House01_baseline_s{s}.csv")
    cfar_f = os.path.join(d, f"House01_cfar_s{s}.csv")
    sdr_f = os.path.join(d, f"House01_sdr_s{s}.csv")
    
    def parse(f):
        if not os.path.exists(f): return None, "?"
        with open(f) as fh:
            lines = [l.strip() for l in fh.readlines() if l.strip()]
            if not lines: return None, "?"
            last = lines[-1]
            parts = last.split()
            if last.startswith("FAILED"):
                return float(parts[4]), "FAIL"
            else:
                return float(parts[3]), "OK"
    
    bl_e, bl_s = parse(bl_f)
    cf_e, cf_s = parse(cfar_f)
    sd_e, sd_s = parse(sdr_f)
    
    cf_d = f"{(cf_e-bl_e)/bl_e*100:+.1f}%" if bl_e and cf_e else "?"
    sd_d = f"{(sd_e-bl_e)/bl_e*100:+.1f}%" if bl_e and sd_e else "?"
    
    print(f"{s:>4} {bl_e:>10.3f} {bl_s:>5} {cf_e:>10.3f} {cf_s:>5} {sd_e:>10.3f} {sd_s:>5} {cf_d:>10} {sd_d:>10}")
    
    if bl_e: bl_mean += bl_e; n += 1
    if cf_e: cfar_mean += cf_e
    if sd_e: sdr_mean += sd_e
    if bl_s == "OK": bl_ok += 1
    if cf_s == "OK": cfar_ok += 1
    if sd_s == "OK": sdr_ok += 1

if n > 0:
    print(f"\nMean:  BL={bl_mean/n:.3f}m  CFAR={cfar_mean/n:.3f}m  SDR={sdr_mean/n:.3f}m")
    print(f"Success@3m: BL={bl_ok}/10  CFAR={cfar_ok}/10  SDR={sdr_ok}/10")
