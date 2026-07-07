#!/usr/bin/env python3
"""Patch V4: Stronger decay (0.99) + Phase 1 no-update"""
f = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(f, 'r') as fh:
    code = fh.read()

# 1. Revert EIG-MAP arbitration back to simple MAP
old_arb = """        if (sbd_stable_count_ >= 5) {
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);

            // EIG-MAP Arbitration (Ge 2014 + BOED theory):
            // Posterior STABLE means KL change is low, NOT that MAP is correct.
            // Under model misspecification (Poisson approximates GADEN), MAP can lock
            // to a wrong mode while EIG-max still points to the correct region.
            // Navigate to EIG-max when MAP and EIG-max disagree.
            int eig_max_i, eig_max_j;
            float max_eig_val = eig_field_.maxCoeff(&eig_max_i, &eig_max_j);
            float eig_x = eig_max_i * resolution_ - map_half_size_;
            float eig_y = eig_max_j * resolution_ - map_half_size_;
            float map_eig_dist = std::sqrt((map_x - eig_x) * (map_x - eig_x) +
                                            (map_y - eig_y) * (map_y - eig_y));

            if (map_eig_dist > 2.0f && max_eig_val > eig_threshold_) {
                best_x = eig_x;
                best_y = eig_y;
                GSL_INFO("SBD: STABLE MAP-EIG conflict (d={:.2f}m), EIG-max ({:.2f},{:.2f}) eig={:.5f} > MAP ({:.2f},{:.2f})",
                         map_eig_dist, eig_x, eig_y, max_eig_val, map_x, map_y);
            } else {
                best_x = map_x;
                best_y = map_y;
                GSL_INFO("SBD: Posterior STABLE, MAP-EIG consistent (d={:.2f}m), MAP ({:.2f},{:.2f})",
                         map_eig_dist, map_x, map_y);
            }
            clipToMapBounds(best_x, best_y);
            return;
        }"""

new_simple = """        if (sbd_stable_count_ >= 5) {
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            GSL_INFO("SBD: Posterior STABLE, moving to MAP ({:.2f},{:.2f})", map_x, map_y);
            best_x = map_x;
            best_y = map_y;
            clipToMapBounds(best_x, best_y);
            return;
        }"""

# 2. Change decay from 0.999 to 0.99
old_decay = "    float decay = 0.999f;"
new_decay = "    float decay = 0.99f;  // V4: stronger forgetting (half-life ~69 steps)"

changes = 0
if old_arb in code:
    code = code.replace(old_arb, new_simple)
    changes += 1
    print('Reverted EIG-MAP arbitration to simple MAP')
if old_decay in code:
    code = code.replace(old_decay, new_decay)
    changes += 1
    print('Changed decay from 0.999 to 0.99')
else:
    print('Looking for decay...')
    idx = code.find('float decay = ')
    if idx >= 0:
        print('Found at:', repr(code[idx:idx+30]))

if changes > 0:
    with open(f, 'w') as fh:
        fh.write(code)
    print(f'PATCH V4 APPLIED ({changes} changes)')
else:
    print('ERROR: no changes made')