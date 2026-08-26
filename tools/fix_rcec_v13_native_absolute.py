#!/usr/bin/env python3
"""Materialize the audited RCEC V13 native-view correction.

This is a scientific contract correction, not performance tuning.

Problem in the first materialized candidate:
  native_increment_t = log(native_after_t) - log(pre_native_source_state_t)
The pre-native source state is the previously injected ME-ACI/RCEC state, so
M2 fed RCEC's own previous output back into its supposedly native view. The
revealed-data replay also used the previous V11 state, whereas a true RCEC
closed loop would use the previous RCEC state. That makes the increment view
both feedback-coupled and not dynamically replay-equivalent.

Correction:
  z_native,t = normal_rank(M_native,t)
where M_native,t is the normalized candidate mass of the current native PMFS
source update *before* ME-ACI/RCEC injection. CREI remains
  min(z_native,t, z_even,t, z_odd,t).
This is a conjunctive rank-veto, not a Bayesian product, so no independence or
double-counting claim is made.

The script also explicitly clears RCEC temporal history at map initialization.
All changes are constructed in memory and written only after postconditions.
"""
from __future__ import annotations

from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"

MARKER = "RCEC_V13_NATIVE_ABSOLUTE_V2_20260826"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    original = CPP.read_text(encoding="utf-8")
    before = sha256(CPP)
    if MARKER in original:
        print("RCEC_V13_NATIVE_ABSOLUTE_PATCH=ALREADY_APPLIED")
        print(f"Simulations.cpp_sha256={before}")
        return

    text = original

    old_comment = '''        // RCEC M2 uses the current native PMFS *increment* rather than the
        // absolute PMFS posterior.  beginTADMUpdate() froze the normalized
        // pre-native source state; sourceProbInternal is the post-native state
        // at this point, before ME-ACI/RCEC injection.  The same observations
        // therefore are not multiplied as an independent likelihood: only a
        // rank-consensus constraint is formed.
'''
    new_comment = '''        // RCEC_V13_NATIVE_ABSOLUTE_V2_20260826.
        // M2 uses the CURRENT native PMFS candidate ordering before RCEC
        // injection. It deliberately does not subtract the pre-native source
        // state: that state contains the previous injected RCEC/V11 output and
        // would create a feedback-coupled pseudo-increment.  Native/even/odd
        // views are combined only by a lower-envelope rank consensus; they are
        // not multiplied as independent likelihoods.
'''
    text = replace_once(text, old_comment, new_comment, "M2 explanatory comment")

    old_decl = '''        std::vector<std::string> rcecCandidateIds(candidateCount);
        std::vector<double> rcecNativeBeforeMass(candidateCount, 0.0);
        std::vector<double> rcecNativeAfterMass(candidateCount, 0.0);
        std::vector<double> rcecNativeIncrement(candidateCount, 0.0);
        std::vector<double> rcecNativeRanks(candidateCount, 0.0);
'''
    new_decl = '''        std::vector<std::string> rcecCandidateIds(candidateCount);
        std::vector<double> rcecNativeMass(candidateCount, 0.0);
        std::vector<double> rcecNativeRanks(candidateCount, 0.0);
'''
    text = replace_once(text, old_decl, new_decl, "native-view declarations")

    old_shape = '''            if (pcAciIncomingNativePriorSnapshot.size() != sourceProbInternal.size())
            {
                GSL_ERROR("RCEC V13 pre-native snapshot shape mismatch");
                return false;
            }
'''
    text = replace_once(text, old_shape, "", "feedback snapshot check")

    old_loop = '''            for (size_t s = 0; s < candidateCount; ++s)
            {
                rcecCandidateIds[s] = p2LastEvaluatedCandidates[s].stableID;
                const auto& rect = p2LastEvaluatedCandidates[s].rect;
                long double before = 0.0L;
                long double after = 0.0L;
                for (int x = rect[0]; x < rect[0] + rect[2]; ++x)
                    for (int y = rect[1]; y < rect[1] + rect[3]; ++y)
                    {
                        if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x ||
                            y >= measuredHitProb.metadata.dimensions.y)
                            continue;
                        const size_t cellIndex = measuredHitProb.metadata.indexOf({x, y});
                        if (measuredHitProb.occupancy[cellIndex] != Occupancy::Free)
                            continue;
                        before += std::max(pcAciIncomingNativePriorSnapshot[cellIndex], 0.0L);
                        after += std::max(static_cast<long double>(sourceProbInternal[cellIndex]), 0.0L) / nativeAfterTotal;
                    }
                constexpr long double rcecMassFloor = 1e-300L;
                rcecNativeBeforeMass[s] = static_cast<double>(before);
                rcecNativeAfterMass[s] = static_cast<double>(after);
                rcecNativeIncrement[s] =
                    std::log(static_cast<double>(std::max(after, rcecMassFloor))) -
                    std::log(static_cast<double>(std::max(before, rcecMassFloor)));
            }
            rcecNativeRanks = rcec_v13::normalRanks(rcecNativeIncrement, rcecCandidateIds);
'''
    new_loop = '''            for (size_t s = 0; s < candidateCount; ++s)
            {
                rcecCandidateIds[s] = p2LastEvaluatedCandidates[s].stableID;
                const auto& rect = p2LastEvaluatedCandidates[s].rect;
                long double nativeMass = 0.0L;
                for (int x = rect[0]; x < rect[0] + rect[2]; ++x)
                    for (int y = rect[1]; y < rect[1] + rect[3]; ++y)
                    {
                        if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x ||
                            y >= measuredHitProb.metadata.dimensions.y)
                            continue;
                        const size_t cellIndex = measuredHitProb.metadata.indexOf({x, y});
                        if (measuredHitProb.occupancy[cellIndex] != Occupancy::Free)
                            continue;
                        nativeMass += std::max(
                            static_cast<long double>(sourceProbInternal[cellIndex]), 0.0L) /
                            nativeAfterTotal;
                    }
                rcecNativeMass[s] = static_cast<double>(nativeMass);
            }
            rcecNativeRanks = rcec_v13::normalRanks(rcecNativeMass, rcecCandidateIds);
'''
    text = replace_once(text, old_loop, new_loop, "native feedback block")

    old_header = '            rcecFile << "source_update_id,candidate_id,native_before_mass,native_after_mass,native_log_increment,native_normal_rank,even_normal_rank,odd_normal_rank,v11_stouffer_score,crei_score,temporal_median_score,active_score,history_count,arm\\n";\n'
    new_header = '            rcecFile << "source_update_id,candidate_id,native_absolute_mass,native_normal_rank,even_normal_rank,odd_normal_rank,v11_stouffer_score,crei_score,temporal_median_score,active_score,history_count,arm\\n";\n'
    text = replace_once(text, old_header, new_header, "RCEC score CSV header")

    old_row = '''                rcecFile << tadmSourceUpdateId << ',' << p2LastEvaluatedCandidates[s].stableID << ','
                         << std::setprecision(17) << rcecNativeBeforeMass[s] << ',' << rcecNativeAfterMass[s] << ','
                         << rcecNativeIncrement[s] << ',' << rcecNativeRanks[s] << ',' << evenRanks[s] << ','
                         << oddRanks[s] << ',' << v11Scores[s] << ',' << rcecCreiScores[s] << ','
'''
    new_row = '''                rcecFile << tadmSourceUpdateId << ',' << p2LastEvaluatedCandidates[s].stableID << ','
                         << std::setprecision(17) << rcecNativeMass[s] << ',' << rcecNativeRanks[s] << ',' << evenRanks[s] << ','
                         << oddRanks[s] << ',' << v11Scores[s] << ',' << rcecCreiScores[s] << ','
'''
    text = replace_once(text, old_row, new_row, "RCEC score CSV row")

    text = replace_once(
        text,
        'rcec_v13_acit_crei_tmem_v1',
        'rcec_v13_acit_crei_native_absolute_tmem_v2',
        "formula marker",
    )

    reset_anchor = '''        pcAciIncomingNativePriorSnapshot.assign(sourceProb.data.size(), 0.0L);
        pcAciCausalStateAvailable = false;
'''
    reset_replacement = '''        pcAciIncomingNativePriorSnapshot.assign(sourceProb.data.size(), 0.0L);
        // RCEC_V13_NATIVE_ABSOLUTE_V2_20260826: map/run state boundary.
        // A repeated map initialization must never inherit candidate IDs or
        // temporal consensus snapshots from the previous map instance.
        rcecV13CandidateIds.clear();
        rcecV13ConsensusHistory.clear();
        pcAciCausalStateAvailable = false;
'''
    text = replace_once(text, reset_anchor, reset_replacement, "RCEC map-reset anchor")

    # Postconditions are checked before the only write.
    required = (
        MARKER,
        'rcec_v13::normalRanks(rcecNativeMass, rcecCandidateIds)',
        'rcecV13CandidateIds.clear();',
        'rcecV13ConsensusHistory.clear();',
        'native_absolute_mass,native_normal_rank',
        'rcec_v13_acit_crei_native_absolute_tmem_v2',
    )
    for token in required:
        if token not in text:
            raise SystemExit(f"native-absolute patch missing postcondition: {token}")

    forbidden_in_rcec = (
        'rcecNativeBeforeMass',
        'rcecNativeAfterMass',
        'rcecNativeIncrement',
        'RCEC V13 pre-native snapshot shape mismatch',
    )
    for token in forbidden_in_rcec:
        if token in text:
            raise SystemExit(f"feedback-coupled RCEC token remains: {token}")

    CPP.write_text(text, encoding="utf-8")
    print("RCEC_V13_NATIVE_ABSOLUTE_PATCH=PASS")
    print(f"Simulations.cpp_before_sha256={before}")
    print(f"Simulations.cpp_after_sha256={sha256(CPP)}")
    print("native_view=current_post_native_absolute_rank")
    print("previous_injected_state_used_by_CREI=false")


if __name__ == "__main__":
    main()
