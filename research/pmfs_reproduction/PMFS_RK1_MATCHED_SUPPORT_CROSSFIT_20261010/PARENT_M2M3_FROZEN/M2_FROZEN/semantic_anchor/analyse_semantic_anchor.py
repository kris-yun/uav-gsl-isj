"""Read-only native outputs -> formula/native comparisons and exact binomial sums."""
import sys
sys.dont_write_bytecode=True
import csv,hashlib,json,math,struct
from decimal import Decimal,localcontext
from fractions import Fraction
from pathlib import Path
WORK=Path(__file__).resolve().parent
ROOT=WORK.parents[2]

def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def logit(x):return math.log(x)-math.log1p(-x)
def sigmoid(x):
    if x>=0:return 1/(1+math.exp(-x))
    e=math.exp(x);return e/(1+e)
def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def decimal_fraction(v):
    with localcontext() as c:
        c.prec=50
        return str(Decimal(v.numerator)/Decimal(v.denominator))
def exact_weight(n,k):return Fraction(math.comb(n,k)*3**k*2**(n-k),5**n)

def analyse():
    originals=rows(WORK/'vm_evidence/native/native_counts.csv')
    step_path=WORK/'vm_evidence/native/native_steps.csv'
    grouped={(int(r['n']),int(r['total_hits']),r['ordering']):r for r in originals}
    counts=json.loads((WORK/'vm_evidence/native/native_execution.json').read_text())
    assert counts['candidate_forward_calls']==counts['source_posterior_updates']==counts['ROS_nodes']==counts['GADEN_realizations']==0
    prior=.3;ph=f32(.6);pm=f32(.1);D=.4;l0=logit(prior)
    ah=logit(ph)-l0;am=logit(pm)-l0
    # Native applyFalloffLogOdds: prob is float and the ratio prob/(1-prob)
    # is computed in float; std::log(float) also returns float. It is only then
    # widened to double as applyFalloffLogOdds's return value.
    nh=f32(math.log(f32(ph/f32(1-ph))))-math.log(prior/(1-prior))
    nm=f32(math.log(f32(pm/f32(1-pm))))-math.log(prior/(1-prior))
    max_lo_error=max_p_error=max_native_expression_error=0.;native_zero=native_one=0
    paired=WORK/'native_formula_steps.csv'
    with step_path.open(encoding='utf-8',newline='') as inp,paired.open('w',encoding='utf-8',newline='') as out:
        reader=csv.DictReader(inp);writer=None
        for row in reader:
            n=int(row['n']);k=int(row['total_hits']);j=int(row['step']);hits=min(j,k)
            lo=l0+hits*ah+(j-hits)*am;p=sigmoid(lo)
            native_lo=float(row['logOdds']);native_p=float(row['probability'])
            expression=math.log(prior/(1-prior))+hits*nh+(j-hits)*nm
            max_lo_error=max(max_lo_error,abs(native_lo-lo));max_p_error=max(max_p_error,abs(native_p-p))
            max_native_expression_error=max(max_native_expression_error,abs(native_lo-expression))
            native_zero+=native_p==0.;native_one+=native_p==1.
            row.update(formula_logOdds=lo,formula_probability=p,native_minus_formula_logOdds=native_lo-lo,native_minus_formula_probability=native_p-p,
                       float_expression_logOdds=expression,native_minus_float_expression_logOdds=native_lo-expression)
            if writer is None:writer=csv.DictWriter(out,fieldnames=list(row));writer.writeheader()
            writer.writerow(row)
    summary=[];order_diff=0;max_order_lo_error=0.;max_order_score_error=0.;min_threshold_margin=math.inf
    for n in [5,10,20,50,100,200]:
        map_wrong=Fraction();formula_wrong=Fraction();raw_wrong=Fraction();weighted_map_p=0.;expected_native_gap=0.;expected_raw_gap=0.
        ranking_same=True
        for k in range(n+1):
            a=grouped[n,k,'hit_first'];b=grouped[n,k,'miss_first'];w=exact_weight(n,k)
            assert len(str(a['probability']))>0
            st=float(a['source_score_true']);sw=float(a['source_score_wrong'])
            wrong=sw>st;wrong_b=float(b['source_score_wrong'])>float(b['source_score_true'])
            ranking_same &= wrong==wrong_b;order_diff+=wrong!=wrong_b
            max_order_lo_error=max(max_order_lo_error,abs(float(a['logOdds'])-float(b['logOdds'])))
            max_order_score_error=max(max_order_score_error,abs(st-float(b['source_score_true'])),abs(sw-float(b['source_score_wrong'])))
            min_threshold_margin=min(min_threshold_margin,abs(float(a['logOdds'])-logit(.75)))
            p=sigmoid(l0+k*ah+(n-k)*am)
            formula_wrong+=w*((1-D*abs(p-.9))>(1-D*abs(p-.6)))
            map_wrong+=w*wrong
            # Exact rational comparison of raw likelihoods: (2/3)^k*4^(n-k).
            raw_wrong+=w*((2**k)*(4**(n-k))<3**k)
            weighted_map_p+=float(w)*float(a['probability'])
            expected_native_gap+=float(w)*(math.log(st)-math.log(sw))
            expected_raw_gap+=float(w)*(k*math.log(2/3)+(n-k)*math.log(4))
        ex=grouped[n,round(.6*n),'hit_first']
        summary.append(dict(n=n,example_hits=round(.6*n),example_logOdds=float(ex['logOdds']),example_native_probability=float(ex['probability']),
          example_confidence=float(ex['confidence']),example_native_true_score=float(ex['source_score_true']),example_native_wrong_score=float(ex['source_score_wrong']),
          example_unit_confidence_true_score=float(ex['unit_confidence_score_true']),example_unit_confidence_wrong_score=float(ex['unit_confidence_score_wrong']),
          formula_exact_binomial_wrong_probability=float(formula_wrong),native_canonical_order_binomial_wrong_probability=float(map_wrong),
          native_canonical_order_binomial_wrong_probability_decimal=decimal_fraction(map_wrong),
          raw_Bernoulli_exact_binomial_wrong_probability=float(raw_wrong),raw_Bernoulli_exact_binomial_wrong_probability_decimal=decimal_fraction(raw_wrong),
          native_vs_formula_ranking_agree=map_wrong==formula_wrong,hit_first_miss_first_rankings_agree=ranking_same,
          native_binomial_weighted_mean_map_probability=weighted_map_p,
          expected_native_log_score_true_minus_wrong=expected_native_gap,expected_raw_log_likelihood_true_minus_wrong=expected_raw_gap))
    with (WORK/'semantic_summary.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    critical=-am/(ah-am)
    supplied=json.loads((ROOT/'work/pmfs_m2_observation_discrimination_20261010/handoff/probability_semantics_counterexample.json').read_text(encoding='utf-8'))
    supplied_rows={r['n']:r for r in supplied['rows']};max_supplied_error=max(abs(row['formula_exact_binomial_wrong_probability']-supplied_rows[row['n']]['exact_probability_map_similarity_selects_wrong']) for row in summary)
    result=dict(verdict='SOURCE_LEVEL_COUNTEREXAMPLE_SUPPORTED_NOT_B4_ROOT_CAUSE',
      actually_completed=['fresh compile of frozen PMFSLib.cpp','calls to native EstimateHitProbabilities','calls to native sourceProbFromMaps/probabilityFromSingleCell/probabilitySingleFrequency',
                          'all hit counts at each frozen n','hit-first and miss-first native ordering checks','step-by-step primary ordering record','exact rational binomial summation over count decisions'],
      constants=dict(prior=prior,hit_float32=ph,miss_float32=pm,discrimination=D,true_candidate_float32=f32(.6),wrong_candidate_float32=f32(.9),
                     true_physical_Bernoulli_rate=.6,confidenceMeasurementWeight=1,confidenceSigmaSpatial=1,kernelSigma=1.5,kernelStretchConstant=1.5),
      native_update_formula=dict(hit_increment=nh,miss_increment=nm,real_formula_hit_increment=ah,real_formula_miss_increment=am,real_formula_critical_frequency=critical),
      floating_point_comparison=dict(max_logOdds_native_vs_real_formula=max_lo_error,max_probability_native_vs_real_formula=max_p_error,
                                    max_logOdds_native_vs_float_expression=max_native_expression_error,hit_first_vs_miss_first_max_logOdds_difference=max_order_lo_error,
                                    hit_first_vs_miss_first_max_score_difference=max_order_score_error,ordering_rank_disagreements=order_diff,
                                    native_zero_probability_step_rows=native_zero,native_one_probability_step_rows=native_one,
                                    minimum_final_logOdds_distance_from_ranking_threshold=min_threshold_margin),
      formula_handoff_max_abs_wrong_probability_difference=max_supplied_error,
      confidence=['Native confidence uses omega += 1/sqrt(2*pi) at zero offset and confidence=1-exp(-omega).',
                  'Finite positive common confidence changes score magnitudes, but preserves non-tied candidate ranking; unit-confidence scores are separately recorded.'],
      initialization_and_clipping=['Native HitProbability::setProbability(0.3) called on fresh zero-confidence cell before each sequence.',
                                  'applyFalloffLogOdds clamps inverse probability to [0.001,0.999]; 0.6f and 0.1f are inside and no clipping changes them.',
                                  'There is no logOdds clipping; native conversion is 1-1/(1+exp(logOdds)), allowing finite-float probability saturation.'],
      binomial_scope=['Formula wrong-selection probability uses exact Binomial(n,3/5) weights and formula decisions.',
                      'Native wrong-selection probability uses exact same weights with executed canonical hit-first floating-point decisions. No Monte Carlo samples.',
                      'Miss-first decisions agree for every enumerated n,k. Intermediate permutations were not all enumerated, so no unqualified bitwise claim for all iid native event orderings.'],
      nonclaims=['Not a B4 observation replay or diagnosis of B4 cause.','Not a transport or candidate-forward simulation.','Not evidence for a new method or localization improvement.',
                 'The synthetic iid Bernoulli-frequency interpretation is an explicit test assumption; it does not refute binary filtering for a truly static binary latent variable.',
                 'No display-grid replication or kernel-width test was performed; physical kernel-width invariance remains outside this experiment.'],
      execution_counters=counts,summary=summary)
    (WORK/'SEMANTIC_ANCHOR_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert all(r['native_vs_formula_ranking_agree'] and r['hit_first_miss_first_rankings_agree'] for r in summary)
    assert max_supplied_error<1e-12
    print(json.dumps(dict(verdict=result['verdict'],floating=result['floating_point_comparison'],summary=summary),ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':analyse()
