#!/usr/bin/env python3
"""Materialize RCEC V13 on top of the frozen V11/CTT checkpoint source.

This patch intentionally changes only ME-ACI source-state fusion.  It does not
change the 54-member inverse-transport family, temporal/spatial identifiability,
planner, PMFS measurement update, or CTT checkpoint code.

Ablation arm is selected at runtime through RCEC_V13_ARM:
  v11_stouffer  -> frozen V11 behavior (default, parity arm)
  crei_latest   -> V11 causal views + native PMFS increment conjunctive consensus
  rcec_full     -> crei_latest + temporal median evidence memory
"""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib

ROOT = Path(__file__).resolve().parents[1]
HPP = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp"
CPP = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"

MARKER = "RCEC_V13_FROZEN_CANDIDATE_20260826"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def patch_hpp() -> None:
    text = HPP.read_text(encoding="utf-8")
    if MARKER in text:
        return
    text = replace_once(
        text,
        '#include "gsl_server/algorithms/PMFS/internal/CTTTransportTrace.hpp"\n',
        '#include "gsl_server/algorithms/PMFS/internal/CTTTransportTrace.hpp"\n'
        '#include "gsl_server/algorithms/PMFS/internal/RCECV13.hpp"\n',
        "hpp include",
    )
    text = replace_once(
        text,
        "        std::vector<PCAciEvent> meAciEvidenceReservoir;\n",
        "        std::vector<PCAciEvent> meAciEvidenceReservoir;\n"
        "        // RCEC_V13_FROZEN_CANDIDATE_20260826: candidate-aligned history of\n"
        "        // truth-blind cross-view consensus scores.  History is appended only\n"
        "        // on the same V11 spatiotemporally identifiable updates.\n"
        "        std::vector<std::string> rcecV13CandidateIds;\n"
        "        std::vector<std::vector<double>> rcecV13ConsensusHistory;\n",
        "hpp state",
    )
    HPP.write_text(text, encoding="utf-8")


def patch_cpp() -> None:
    text = CPP.read_text(encoding="utf-8")
    if MARKER in text:
        return

    text = replace_once(
        text,
        '        const bool inject = pfdiMode == "me_aci";\n',
        '        const bool inject = pfdiMode == "me_aci";\n'
        '        // RCEC_V13_FROZEN_CANDIDATE_20260826.  The environment selects a\n'
        '        // preregistered ablation arm without changing the binary.  Absence of\n'
        '        // the variable is exact frozen-V11 behavior.\n'
        '        const char* rcecArmEnvironment = std::getenv("RCEC_V13_ARM");\n'
        '        const std::string rcecArm = rcecArmEnvironment == nullptr\n'
        '            ? "v11_stouffer" : std::string(rcecArmEnvironment);\n'
        '        const bool rcecCreiArm = rcecArm == "crei_latest";\n'
        '        const bool rcecFullArm = rcecArm == "rcec_full";\n'
        '        if (rcecArm != "v11_stouffer" && !rcecCreiArm && !rcecFullArm)\n'
        '        {\n'
        '            GSL_ERROR("RCEC V13 unknown RCEC_V13_ARM={}", rcecArm);\n'
        '            return false;\n'
        '        }\n',
        "cpp arm selector",
    )

    old_score_block = '''        const std::vector<double> evenRanks = normalRanks(evenLogEvidence);\n        const std::vector<double> oddRanks = normalRanks(oddLogEvidence);\n        for (size_t s = 0; s < candidateCount; ++s)\n        {\n            logEvidence[s] = (evenRanks[s] + oddRanks[s]) / std::sqrt(2.0);\n            crossFitBlockScores[s] = {evenLogEvidence[s], oddLogEvidence[s],\n                                      evenRanks[s], oddRanks[s], logEvidence[s]};\n        }\n        const double simulationWallSeconds = std::chrono::duration<double>(\n            std::chrono::steady_clock::now() - simulationStart).count();\n'''

    new_score_block = '''        const std::vector<double> evenRanks = normalRanks(evenLogEvidence);\n        const std::vector<double> oddRanks = normalRanks(oddLogEvidence);\n        std::vector<double> v11Scores(candidateCount, 0.0);\n        for (size_t s = 0; s < candidateCount; ++s)\n        {\n            v11Scores[s] = (evenRanks[s] + oddRanks[s]) / std::sqrt(2.0);\n            crossFitBlockScores[s] = {evenLogEvidence[s], oddLogEvidence[s],\n                                      evenRanks[s], oddRanks[s], v11Scores[s]};\n        }\n\n        // RCEC M2 uses the current native PMFS *increment* rather than the\n        // absolute PMFS posterior.  beginTADMUpdate() froze the normalized\n        // pre-native source state; sourceProbInternal is the post-native state\n        // at this point, before ME-ACI/RCEC injection.  The same observations\n        // therefore are not multiplied as an independent likelihood: only a\n        // rank-consensus constraint is formed.\n        std::vector<std::string> rcecCandidateIds(candidateCount);\n        std::vector<double> rcecNativeBeforeMass(candidateCount, 0.0);\n        std::vector<double> rcecNativeAfterMass(candidateCount, 0.0);\n        std::vector<double> rcecNativeIncrement(candidateCount, 0.0);\n        std::vector<double> rcecNativeRanks(candidateCount, 0.0);\n        std::vector<double> rcecCreiScores(candidateCount, 0.0);\n        std::vector<double> rcecTemporalScores(candidateCount, 0.0);\n        std::vector<double> activeScores = v11Scores;\n        std::size_t rcecHistoryCount = 0;\n\n        if (rcecCreiArm || rcecFullArm)\n        {\n            if (pcAciIncomingNativePriorSnapshot.size() != sourceProbInternal.size())\n            {\n                GSL_ERROR("RCEC V13 pre-native snapshot shape mismatch");\n                return false;\n            }\n            long double nativeAfterTotal = 0.0L;\n            for (size_t cellIndex = 0; cellIndex < sourceProbInternal.size(); ++cellIndex)\n                if (measuredHitProb.occupancy[cellIndex] == Occupancy::Free &&\n                    std::isfinite(sourceProbInternal[cellIndex]) && sourceProbInternal[cellIndex] > 0.0)\n                    nativeAfterTotal += static_cast<long double>(sourceProbInternal[cellIndex]);\n            if (!(nativeAfterTotal > 0.0L) || !std::isfinite(static_cast<double>(nativeAfterTotal)))\n            {\n                GSL_ERROR("RCEC V13 native post-update source mass is invalid");\n                return false;\n            }\n\n            for (size_t s = 0; s < candidateCount; ++s)\n            {\n                rcecCandidateIds[s] = p2LastEvaluatedCandidates[s].stableID;\n                const auto& rect = p2LastEvaluatedCandidates[s].rect;\n                long double before = 0.0L;\n                long double after = 0.0L;\n                for (int x = rect[0]; x < rect[0] + rect[2]; ++x)\n                    for (int y = rect[1]; y < rect[1] + rect[3]; ++y)\n                    {\n                        if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x ||\n                            y >= measuredHitProb.metadata.dimensions.y)\n                            continue;\n                        const size_t cellIndex = measuredHitProb.metadata.indexOf({x, y});\n                        if (measuredHitProb.occupancy[cellIndex] != Occupancy::Free)\n                            continue;\n                        before += std::max(pcAciIncomingNativePriorSnapshot[cellIndex], 0.0L);\n                        after += std::max(static_cast<long double>(sourceProbInternal[cellIndex]), 0.0L) / nativeAfterTotal;\n                    }\n                constexpr long double rcecMassFloor = 1e-300L;\n                rcecNativeBeforeMass[s] = static_cast<double>(before);\n                rcecNativeAfterMass[s] = static_cast<double>(after);\n                rcecNativeIncrement[s] =\n                    std::log(static_cast<double>(std::max(after, rcecMassFloor))) -\n                    std::log(static_cast<double>(std::max(before, rcecMassFloor)));\n            }\n            rcecNativeRanks = rcec_v13::normalRanks(rcecNativeIncrement, rcecCandidateIds);\n            rcecCreiScores = rcec_v13::conjunctiveConsensus(rcecNativeRanks, evenRanks, oddRanks);\n            activeScores = rcecCreiScores;\n\n            if (rcecFullArm)\n            {\n                if (rcecV13CandidateIds.empty())\n                    rcecV13CandidateIds = rcecCandidateIds;\n                else if (rcecV13CandidateIds != rcecCandidateIds)\n                {\n                    GSL_ERROR("RCEC V13 candidate identity/order drift; temporal consensus is undefined");\n                    return false;\n                }\n                rcecV13ConsensusHistory.push_back(rcecCreiScores);\n                rcecTemporalScores = rcec_v13::temporalMedian(rcecV13ConsensusHistory);\n                activeScores = rcecTemporalScores;\n                rcecHistoryCount = rcecV13ConsensusHistory.size();\n            }\n            else\n            {\n                rcecTemporalScores = rcecCreiScores;\n                rcecHistoryCount = 1;\n            }\n        }\n\n        logEvidence = activeScores;\n        const double simulationWallSeconds = std::chrono::duration<double>(\n            std::chrono::steady_clock::now() - simulationStart).count();\n'''
    text = replace_once(text, old_score_block, new_score_block, "cpp score block")

    audit_anchor = '''        std::ofstream scoreFile(tadmDirectory + "/meaci_candidate_scores_update_" + tag + ".csv");\n'''
    audit_insert = '''        if (rcecCreiArm || rcecFullArm)\n        {\n            std::ofstream rcecFile(tadmDirectory + "/rcec_v13_scores_update_" + tag + ".csv");\n            rcecFile << "source_update_id,candidate_id,native_before_mass,native_after_mass,native_log_increment,native_normal_rank,even_normal_rank,odd_normal_rank,v11_stouffer_score,crei_score,temporal_median_score,active_score,history_count,arm\\n";\n            for (size_t s = 0; s < candidateCount; ++s)\n                rcecFile << tadmSourceUpdateId << ',' << p2LastEvaluatedCandidates[s].stableID << ','\n                         << std::setprecision(17) << rcecNativeBeforeMass[s] << ',' << rcecNativeAfterMass[s] << ','\n                         << rcecNativeIncrement[s] << ',' << rcecNativeRanks[s] << ',' << evenRanks[s] << ','\n                         << oddRanks[s] << ',' << v11Scores[s] << ',' << rcecCreiScores[s] << ','\n                         << rcecTemporalScores[s] << ',' << activeScores[s] << ',' << rcecHistoryCount << ','\n                         << rcecArm << '\\n';\n            rcecFile.flush();\n            std::ofstream rcecSummary(tadmDirectory + "/rcec_v13_update_summary.csv", std::ios::out | std::ios::app);\n            if (rcecSummary.tellp() == 0)\n                rcecSummary << "run_uuid,source_update_id,arm,event_count,candidate_count,history_count,inject,formula_marker\\n";\n            rcecSummary << tadmRunUUID << ',' << tadmSourceUpdateId << ',' << rcecArm << ','\n                        << pcAciActiveEvents.size() << ',' << candidateCount << ',' << rcecHistoryCount << ','\n                        << (inject ? 1 : 0) << ",rcec_v13_acit_crei_tmem_v1\\n";\n            rcecSummary.flush();\n        }\n\n        std::ofstream scoreFile(tadmDirectory + "/meaci_candidate_scores_update_" + tag + ".csv");\n'''
    text = replace_once(text, audit_anchor, audit_insert, "cpp audit insert")

    CPP.write_text(text, encoding="utf-8")


def main() -> None:
    global ROOT, HPP, CPP
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    ROOT = args.root.resolve()
    HPP = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp"
    CPP = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"
    before_hpp = sha256(HPP)
    before_cpp = sha256(CPP)
    patch_hpp()
    patch_cpp()
    hpp = HPP.read_text(encoding="utf-8")
    cpp = CPP.read_text(encoding="utf-8")
    required = [
        MARKER,
        'RCEC_V13_ARM',
        'rcec_v13::conjunctiveConsensus',
        'rcec_v13::temporalMedian',
        'rcec_v13_scores_update_',
    ]
    for marker in required:
        if marker not in hpp + cpp:
            raise SystemExit(f"missing RCEC marker after patch: {marker}")
    print("RCEC_V13_SOURCE_PATCH=PASS")
    print(f"Simulations.hpp_before_sha256={before_hpp}")
    print(f"Simulations.hpp_after_sha256={sha256(HPP)}")
    print(f"Simulations.cpp_before_sha256={before_cpp}")
    print(f"Simulations.cpp_after_sha256={sha256(CPP)}")


if __name__ == "__main__":
    main()
