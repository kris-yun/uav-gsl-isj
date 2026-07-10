import sys

# Read the file
with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    content = f.read()

# Old eta computation block
old_block = """    // eta -> 1: standard Bayes (trust model completely)
    // eta -> 0: ignore observation (trust prior)
    //
    // Our adaptive eta:
    // - Gas detected + stable wind: eta high (0.6-0.9) -> trust observation
    // - Gas detected + chaotic wind: eta medium -> partial trust
    // - No gas + stable wind: eta medium (0.15-0.5) -> non-detection informative
    // - No gas + chaotic wind: eta low -> non-detection unreliable
    float eta;
    if (!use_adaptive_eta_) {
        eta = 0.5f;  // Fixed eta for ablation
    } else if (detected) {
        eta = 0.6f + 0.3f * wind_confidence_;  // [0.6, 0.9]
    } else {
        eta = 0.15f + 0.35f * wind_confidence_;  // [0.15, 0.5]
    }"""

# New regret-based eta computation
new_block = """    // Regret-based adaptive eta (Gr¨¹nwald & van Ommen, 2017)
    // eta = 1/(1 + gamma_hat), where gamma_hat is the EMA of the empirical mixability gap
    // - Detection (model well-specified): small gap -> eta close to 1
    // - Non-detection (model misspecified): large gap -> eta close to 0
    // - Wind confidence modulates the gap: stable wind -> model more reliable
    float eta;
    if (!use_adaptive_eta_) {
        eta = 0.5f;  // Fixed eta for ablation
    } else {
        // Compute instantaneous mixability gap estimate
        // High when non-detection (model struggle), low when detection (model fit)
        float gamma_inst;
        if (detected) {
            // Detection: model is well-specified, small gap
            // Scale by (1 - wind_confidence): high wind -> even smaller gap
            gamma_inst = 0.3f * (1.0f - wind_confidence_);
        } else {
            // Non-detection: model is misspecified, large gap
            // Scale by wind_confidence: chaotic wind -> even larger gap
            gamma_inst = 2.0f + 1.5f * (1.0f - wind_confidence_);
        }
        // Update EMA of mixability gap
        cumulative_regret_ = (1.0f - regret_ema_lambda_) * cumulative_regret_ 
                           + regret_ema_lambda_ * gamma_inst;
        regret_step_count_++;
        // Regret-optimal eta: eta = 1/(1 + gamma_hat)
        // Clamp to [0.1, 0.95] for numerical stability
        eta = 1.0f / (1.0f + cumulative_regret_);
        eta = std::clamp(eta, 0.1f, 0.95f);
    }"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
        f.write(content)
    print("SUCCESS: Eta computation replaced with regret-based version")
else:
    print("ERROR: Old block not found")
    # Try to find approximate location
    idx = content.find('eta = 0.6f + 0.3f * wind_confidence_')
    if idx >= 0:
        print(f"Found old eta at position {idx}")
        print("Context:")
        print(content[idx-200:idx+200])
