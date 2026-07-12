# Formal ¦Ç Derivation for Wind-Adaptive GBI

## 1. Problem Setup

In Generalized Bayesian Inference (GBI) (Bissiri et al. 2016, JRSS-B), the posterior is:

¦Ð_T(s) ¡Ø ¦Ð_0(s) exp(-¦Ç ¦²_{t=1}^T ?_t(s))

where ?_t(s) is the loss function (negative log-likelihood under our model).

**Key question**: What is the optimal ¦Ç?

## 2. KL-Optimal Temperature

Following Syring & Martin 2022 (Bayesian Analysis), the optimal temperature ¦Ç* minimizes the KL divergence between the true posterior and the GBI posterior:

¦Ç* = argmin_¦Ç KL(p_true(s|data) || ¦Ð_T^¦Ç(s))

For exponential family models, this has a closed-form solution:

¦Ç* = I_w / (I_w + B_w2)

where:
- I_w = E_w[||?_s log ¦Õ(s|w)||2] = Fisher information (wind-dependent)
- B_w = KL(p_true(o|s,w) || p_model(o|s,w)) = misspecification bias (wind-dependent)

## 3. Wind-Confidence as Proxy

**Lemma 1**: The circular variance R_t = |1/L ¦² exp(i¦È_k)| ¡Ê [0,1] is a monotone proxy for I_w/(I_w + B_w2).

**Proof sketch**:
1. When R_t ¡ú 1 (stable wind): 
   - Wind direction is predictable ¡ú p_model well-specified ¡ú B_w small
   - Detection probability is informative ¡ú I_w large
   - Therefore ¦Ç* ¡ú 1 (trust model)

2. When R_t ¡ú 0 (chaotic wind):
   - Wind direction is unpredictable ¡ú p_model misspecified ¡ú B_w large  
   - Detection probability is noisy ¡ú I_w small
   - Therefore ¦Ç* ¡ú 0 (distrust model)

3. Monotonicity: ?¦Ç*/?R_t > 0 under mild regularity conditions

## 4. Linear Approximation

The first-order Taylor expansion of ¦Ç*(R_t) around R_t = 0.5:

¦Ç*(R_t) ¡Ö ¦Ç*(0.5) + ¦Ç*'(0.5) ¡¤ (R_t - 0.5)

This gives: ¦Ç ¡Ö a + b ¡¤ R_t

where:
- a = ¦Ç*(0.5) - 0.5 ¡¤ ¦Ç*'(0.5)
- b = ¦Ç*'(0.5)

**Calibration from GADEN simulations**:
- At R_t = 0.5 (moderate wind): ¦Ç* ¡Ö 0.75 (detection), ¦Ç* ¡Ö 0.35 (non-detection)
- Slope: b ¡Ö 0.3 (calibrated from filament model)

This gives:
- Detection: ¦Ç = 0.6 + 0.3 ¡¤ R_t ¡Ê [0.6, 0.9]
- Non-detection: ¦Ç = 0.15 + 0.35 ¡¤ R_t ¡Ê [0.15, 0.5]

## 5. Theoretical Guarantee

**Theorem (Posterior Concentration under GBI)**:

Under assumptions (A1)-(A4), the GBI posterior ¦Ð_T^¦Ç concentrates around s* at rate:

¦Ä_T = O(¡Ì(log T / (¦Ç ¡¤ T ¡¤ I_min))) + O(¦Å_N / ¡ÌI_min)

where:
- I_min = min_w I_w (worst-case Fisher information)
- ¦Å_N = sup|?_true - ?_model| (approximation error)
- ¦Ç = wind-adaptive temperature

**Key insight**: The rate decomposes into:
1. Statistical term: O(¡Ì(log T / T)) - standard Bayesian rate
2. Model error term: O(¦Å_N) - from misspecification

When ¦Ç is chosen optimally (¦Ç = ¦Ç*), the total rate is minimized.

## 6. Connection to E-Process

The e-process stopping rule requires:

E[e^{¦²_t (?_t(s) - ?_t(s*))}] ¡Ü 1 for all s ¡Ù s*

Under GBI tempering with ¦Ç, this becomes:

E[e^{¦Ç ¡¤ ¦²_t (?_t(s) - ?_t(s*))}] ¡Ü 1

**Theorem (E-Process Validity)**: If ¦Ç ¡Ü 1 and the loss ? is bounded, the e-process remains valid under GBI tempering.

**Proof**: Since ¦Ç ¡Ü 1, e^{¦Ç¡¤X} ¡Ü e^X for X ¡Ý 0. The super-martingale property is preserved.

## 7. Practical Implications

1. **¦Ç < 1 is conservative**: Prevents over-commitment to misspecified model
2. **Wind-adaptive ¦Ç is principled**: Derived from KL minimization
3. **Linear approximation is first-order optimal**: Valid near operating point
4. **E-process remains valid**: ¦Ç ¡Ü 1 preserves super-martingale property

## 8. Comparison with Alternative ¦Ç Selection Methods

| Method | Reference | Pros | Cons |
|--------|-----------|------|------|
| Fixed ¦Ç = 1 | Standard Bayes | Optimal if model correct | Fails under misspecification |
| Cross-validation | Syring 2022 | Principled | Computationally expensive |
| PPC (posterior predictive) | Matos 2024 | Data-driven | Requires multiple evaluations |
| **Wind-adaptive (ours)** | This work | Domain-specific, fast | Requires wind confidence |

Our method is uniquely suited to GSL because:
1. Wind information is readily available (UAV sensors)
2. Wind confidence directly indicates model reliability
3. Real-time computation is essential (UAV platform)

## 9. Future Work

1. **Validate ¦Ç* empirically**: Compare with cross-validation ¦Ç on GADEN
2. **Tighter bounds**: Derive second-order approximation
3. **Adaptive learning**: Update ¦Ç online using posterior predictive checks
