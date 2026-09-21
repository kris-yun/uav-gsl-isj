"""Aggregate the preregistered necessary gate; never grant ROS permission."""
import csv,json,pathlib,sys
import numpy as np

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
results=[];summaries=[]
for p in sorted(root.glob('House??_seed?/evaluation.json')):
    e=json.loads(p.read_text());s=json.loads(p.with_name('selection.json').read_text())
    with p.with_name('timing.csv').open() as f:timing=[float(r['seconds']) for r in csv.DictReader(f)]
    diag=s['diagnostics'];frac=[x['confounding_fraction'] for x in diag if x['confounding_fraction'] is not None]
    mean=lambda k:float(np.mean(e['strategies'][k]['heldout_min_separation']))
    row={'case':e['case'],'source_MI_min_separation':mean('one_step_source_MI'),
         'two_step_min_separation':mean('two_step_deconfounding'),'passing_worlds':e['passing_heldout_worlds'],
         'gate_pass':e['necessary_case_gate'],'representative_distance_m':e['true_representative_distance_m'],
         'confounding_median_nonzero_contrasts':float(np.median(frac)) if frac else None,
         'zero_source_contrasts':sum(x['contrast_energy']<=1e-20 for x in diag),
         'total_source_leaves':len(diag),'source_vs_fixed_false_residual':e['true_vs_native_false_residual_fraction'],
         'forward_seconds':sum(timing),'selection_seconds':s['selection_seconds'],'forward_calls':len(timing)}
    summaries.append(row);results.append(e)
assert len(results)==6,'six complete evaluations required'
passes=sum(e['necessary_case_gate'] for e in results)
by_house={h:any(e['necessary_case_gate'] for e in results if e['house']==h) for h in ['House01','House02','House03']}
numerical=passes>=4 and all(by_house.values()) and not any(e['case_mean_degradation'] for e in results)
gate={'verdict':'SURROGATE_NUMERICAL_SIGNAL_REVIEW_REQUIRED' if numerical else 'NO_GO_WITHIN_FROZEN_OFFLINE_SCREEN',
      'numerical_gate_pass':numerical,'passing_cases':passes,'house_coverage':by_house,'ROS_promotion':False,
      'independent_response_model_qualified':False,'TNQC_V5':'FROZEN_HOLD','tuning_or_expansion_authorized':False,
      'case_summary':summaries,'scope':'development, fixed-context native point-source / Bernoulli surrogate; no 300-s localization claim'}
(out/'FINAL_GATE.json').write_text(json.dumps(gate,indent=2,allow_nan=False)+'\n')
with (out/'CASE_SUMMARY.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
lines=['# Active source–transport deconfounding V1 — frozen development screen','',f"**{gate['verdict']}**",'',
       'V5 remains HOLD; FUSED closed loop and online planner edits were not performed.','',
       '| Case | Greedy source-MI separation | Two-step separation | Passing held-out worlds | Representative offset m |',
       '|---|---:|---:|---:|---:|']
for r in summaries:lines.append(f"| {r['case']} | {r['source_MI_min_separation']:.6g} | {r['two_step_min_separation']:.6g} | {r['passing_worlds']}/8 | {r['representative_distance_m']:.4f} |")
lines+=['',f'Necessary case gate: {passes}/6; House coverage: {by_house}. No ROS promotion.','',
        '## Interpretation','',
        'Separation is squared Hellinger distance between two-observation source response sets, with one nuisance world shared across both observations. A 0 means a false source can match the true representative at the selected action pair under at least one allowed alternative world.',
        '', 'The nuisance bank was fixed and pushed before new responses. All four strategies share candidate positions, feasible path budget and two observations. Greedy strategies are evaluated with two actions; gains are not created by giving the new method an extra sample.',
        '', 'These are already-seen six development contexts. Grid-off nuisance and a separate simulator replica test interpolation/randomness robustness inside the same native model; they do not establish external model validity or unseen-seed localization.',
        '', 'The source truth is used only after action files are written and hashed. The metric uses the native leaf representative covering truth, not a new forward run at the exact true continuous location. Offsets are disclosed above.',
        '', 'The native baseline reproduces the variance-confidence-visibility objective with regenerated point responses and original first-level weights. It does not reproduce region-source sampling, navigation state or exploration RNG; grid paths certify only point-robot connectivity. This limits positive claims.',
        '', 'Local confidence-weighted nuisance projection is a sensitivity diagnostic, not a calibrated Fisher information calculation. Zero source contrast is separately reported, never scored as successful deconfounding.',
        '', '## Failure details','']
for e,r in zip(results,summaries):
    far=e['strategies']['two_step_deconfounding']['rival_distance_to_truth_m']
    lines += [f"- {e['case']}: {'; '.join(e['reasons']) or 'Necessary numerical gate passed; independent model qualification still absent'}. Zero nominal source contrasts {r['zero_source_contrasts']}/{r['total_source_leaves']}; fixed native-false rival `{e['fixed_native_false_rival']}`. Indistinguishable selected-pair rivals are {min(far):.3f}–{max(far):.3f} m from truth; true-response zeros over all candidate action/world combinations: {e['true_response_at_all_action_worlds_zero_count']}/{e['true_response_at_all_action_worlds_count']}."]
lines += ['', 'The selected two-step pair predicts zero hits for the true representative in all 8 held-out worlds in every case. Wrong sources several metres away can also predict zero hits. Thus the chosen pairs do not break this no-hit ambiguity. Other candidate actions do predict some true-source hits in five cases; this is not a claim that every possible action is uninformative.',
          '', 'Local source-vs-fixed-native-false contrast retains about 92–100% of its weighted energy after projection against the three nuisance columns. These diagnostics do not establish broad local transport-span confounding as the cause of the historical failures. They are consistent with a failure of the selected finite-budget actions and/or of the response representation, without uniquely identifying the cause.']
lines+=['','## Compute and reproducibility','',f"Forward calls: {sum(r['forward_calls'] for r in summaries)}; summed measured forward compute: {sum(r['forward_seconds'] for r in summaries):.2f} s; action scoring: {sum(r['selection_seconds'] for r in summaries):.2f} s.",
        '', 'The complete raw bank, paths, per-world comparisons, source confounding rows, executable/library hashes and input SHA256 records are retained in the evidence archive. These costs are offline preparation costs; no real-time planner feasibility is claimed.',
        '', 'Provenance limit: the first House01/seed0 wrapper executable hash was not retained before the obstacle-only validation correction. Its wrapper source commit and response hash are retained. The frozen native library hashes are recorded; the later five cases have the standalone executable hash as well. This limitation is not a reason to promote or rerun the study.',
        '', 'Stop here. Do not alter the nuisance range, rescue the same screen with a new gate, or open ROS experiments.']
(out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(gate,indent=2))
