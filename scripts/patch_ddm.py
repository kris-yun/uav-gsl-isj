import re

filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(filepath, 'r') as f:
    content = f.read()

# Find the DDM section to replace
old_ddm = '''    // DDM: accumulate evidence for stopping decision
    if (use_ddm_) {
        float mx, my, mz;
        posterior3d_.getMAP(mx, my, mz);
        float map_move = std::sqrt((mx - ddm_prev_map_x_) * (mx - ddm_prev_map_x_) +
                                    (my - ddm_prev_map_y_) * (my - ddm_prev_map_y_));
        // Log-likelihood ratio: evidence FOR source at MAP vs null
        // Use gas reading + distance to MAP as evidence
        float dist_to_map = std::sqrt((cx - mx)*(cx - mx) + (cy - my)*(cy - my));
        float expected_conc = std::exp(-dist_to_map * dist_to_map / 2.0f);
        float llr = latest_gas_ * expected_conc - 0.1f * map_move;
        ddm_stopping_.addObservation(llr, elapsed_time_);
        ddm_prev_map_x_ = mx;
        ddm_prev_map_y_ = my;
    }'''

new_ddm = '''    // DDM: accumulate evidence for stopping decision (FIXED: posterior entropy change rate)
    // Fix: old formula had step-1 false positive (map_move=0, gas high -> huge LLR)
    // New: posterior-based LLR with warm-up period
    if (use_ddm_) {
        float mx, my, mz;
        posterior3d_.getMAP(mx, my, mz);
        float map_move = std::sqrt((mx - ddm_prev_map_x_) * (mx - ddm_prev_map_x_) +
                                    (my - ddm_prev_map_y_) * (my - ddm_prev_map_y_));

        // Warm-up: don't accumulate evidence in first 5 steps
        // The posterior needs time to burn in before we trust its state
        if (step_count_ > 5) {
            // Posterior change rate: negative when converging (good)
            float posterior_change = map_move;

            // Gas evidence: only matters if posterior is still moving
            // If posterior is stable AND gas is consistent -> source found
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
    }'''

if old_ddm in content:
    content = content.replace(old_ddm, new_ddm)
    with open(filepath, 'w') as f:
        f.write(content)
    print("DDM section patched successfully")
else:
    # Try with slightly different whitespace
    print("WARNING: Exact match not found, trying fuzzy match...")
    # Find the DDM block by markers
    start_marker = "// DDM: accumulate evidence for stopping decision"
    end_marker = "// Update altitude posterior"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx >= 0 and end_idx > start_idx:
        content = content[:start_idx] + new_ddm + "\n\n    " + content[end_idx:]
        with open(filepath, 'w') as f:
            f.write(content)
        print("DDM section patched via fuzzy match")
    else:
        print("ERROR: Could not find DDM section")