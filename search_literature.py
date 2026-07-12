import json, urllib.request, time, os

output_file = r"D:\ZYC\A-gas\literature_search_results.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("=== Literature Search Results ===\n")
    f.write(f"Date: 2026-07-11\n\n")

queries = [
    # 1. GBI核心理论
    ("generalized bayesian inference learning rate posterior", "GBI Core Theory"),
    ("safebayes safe bayesian misspecification posterior", "SafeBayes"),
    ("tempered posterior robust inference misspecification 2024", "Tempered Posterior Robust"),
    # 2. 学习率/温度选择
    ("posterior predictive learning rate selection calibration", "Learning Rate Selection"),
    ("adaptive temperature bayesian inference machine learning", "Adaptive Temperature"),
    # 3. E-process / anytime valid
    ("anytime valid inference e-process stopping rule", "E-process Stopping"),
    ("sequential hypothesis testing e-value martingale", "Sequential E-value"),
    # 4. 气体溯源
    ("gas source localization robot mobile sensor", "GSL Robot"),
    ("olfactory navigation bayesian information gathering", "Olfactory Navigation"),
    ("plume tracking UAV unmanned aerial vehicle gas", "UAV Plume"),
    # 5. 信息论探索
    ("information gain adaptive exploration sensor placement 2024", "Info Exploration"),
    ("bayesian optimization sensor path planning 2025", "Bayesian Sensor Planning"),
    # 6. 鲁棒贝叶斯
    ("robust bayesian inference model misspecification divergence", "Robust Bayes Divergence"),
    ("variational inference robust temperature scaling", "VI Robust Temperature"),
    # 7. conformal + UAV
    ("conformal prediction sequential decision stopping", "Conformal Stopping"),
    ("UAV autonomous search rescue indoor 2025", "UAV Search Indoor"),
]

for i, (q, label) in enumerate(queries):
    url = f"https://api.openalex.org/works?search={q.replace(' ', '+')}&sort=publication_year:desc&per_page=6&select=id,display_name,publication_year,cited_by_count,doi"
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        results = data.get("results", [])
        
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{i+1}] {label}: {q}\n")
            f.write(f"{'='*60}\n")
            if results:
                for w in results:
                    y = w.get("publication_year", "?")
                    c = w.get("cited_by_count", 0)
                    n = w.get("display_name", "N/A")
                    doi = w.get("doi", "")
                    f.write(f"  {y} | cit={c} | {n}\n")
                    if doi:
                        f.write(f"    DOI: {doi}\n")
            else:
                f.write("  [NO RESULTS]\n")
        
        print(f"[{i+1}/{len(queries)}] {label}: {len(results)} results")
    except Exception as e:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{i+1}] {label}: ERROR - {e}\n")
        print(f"[{i+1}/{len(queries)}] {label}: ERROR - {e}")
    
    # 每次搜索间隔70秒避免限流
    if i < len(queries) - 1:
        print(f"  Waiting 70s before next search...")
        time.sleep(70)

print("\nDone! Results saved to:", output_file)
