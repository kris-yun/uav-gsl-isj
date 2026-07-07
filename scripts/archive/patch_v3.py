#!/usr/bin/env python3
"""Patch: EIG-MAP Arbitration in sdnbvStep() STABLE branch"""
import re

f = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(f, 'r') as fh:
    code = fh.read()

old_block = """        if (sbd_stable_count_ >= 5) {
            GSL_INFO("SBD: Posterior STABLE (kl={:.6f} stable_count={} > 5), moving to MAP",
                     kl_change, sbd_stable_count_);
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            best_x = map_x;
            best_y = map_y;
            clipToMapBounds(best_x, best_y);
            return;
        }"""

new_block = """        if (sbd_stable_count_ >= 5) {
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

if old_block in code:
    code = code.replace(old_block, new_block)
    with open(f, 'w') as fh:
        fh.write(code)
    print('PATCH V3 APPLIED: EIG-MAP Arbitration in STABLE branch')
else:
    print('ERROR: old block not found')
    # Try to find partial match
    if 'sbd_stable_count_ >= 5' in code:
        idx = code.find('sbd_stable_count_ >= 5')
        print('Found stable check at pos', idx)
        print('Context:', repr(code[idx:idx+200]))