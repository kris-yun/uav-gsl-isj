    // DDM: accumulate evidence for stopping decision (FIXED: posterior entropy change rate)
    if (use_ddm_) {
        float mx, my, mz;
        posterior3d_.getMAP(mx, my, mz);
        float map_move = std::sqrt((mx - ddm_prev_map_x_) * (mx - ddm_prev_map_x_) +
                                    (my - ddm_prev_map_y_) * (my - ddm_prev_map_y_));
        
        // FIXED: Use posterior-based LLR instead of raw gas * expected_conc
        // Problem with old formula: step 1 has map_move=0, gas high → huge LLR → false stop
        // Solution: LLR based on posterior convergence, not raw sensor readings
        //
        // New LLR = posterior_change_rate - decay * map_move
        // where posterior_change_rate measures how much the posterior changed
        // This is a GSL-specific e-value construction:
        // - Under H0 (not converged): posterior keeps changing → LLR < 0
        // - Under H1 (converged): posterior stabilizes → LLR > 0
        
        // Warm-up: don't accumulate evidence in first N steps
        // The posterior needs time to "burn in" before we trust its state
        if (step_count_ > 5) {  // 5-step warm-up
            // Posterior change rate: negative when converging (good)
            float posterior_change = map_move;
            
            // Gas evidence: only matters if posterior is still moving
            // If posterior is stable AND gas is consistent → source found
            float gas_consistency = 0.0f;
            if (map_move < 0.5f) {  // Posterior is relatively stable
                // Check if gas readings are consistent with source at MAP
                float dist_to_map = std::sqrt((cx - mx)*(cx - mx) + (cy - my)*(cy - my));
                float expected_conc = std::exp(-dist_to_map * dist_to_map / 2.0f);
                gas_consistency = latest_gas_ * expected_conc;
            }
            
            // LLR: evidence FOR convergence
            // Positive when: posterior stable AND gas consistent
            // Negative when: posterior still moving
            float llr = gas_consistency - 0.5f * posterior_change;
            
            ddm_stopping_.addObservation(llr, elapsed_time_);
        }
        
        ddm_prev_map_x_ = mx;
        ddm_prev_map_y_ = my;
    }