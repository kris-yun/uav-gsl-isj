#!/usr/bin/env python3
"""Materialize NACC V14 on top of frozen RCEC V13 source.

Scientific changes are intentionally narrow:
- preserve a native-only PMFS carrier across source updates (cut feedback);
- use r=min(z_even,z_odd) as the replicated causal auxiliary score;
- inject q=normalize(p_native*exp(r)) on identifiable NACC updates;
- do not use RCEC native-rank replacement or TMEM for NACC;
- on NACC abstention, keep the current native PMFS state rather than carrying
  a previous causal posterior.

No truth, House/seed parameter, adaptive weight, temperature, planner change or
new transport heuristic is introduced.
"""
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[1]
CPP=ROOT/'ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp'
HPP=ROOT/'ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp'
MARK='NACC_V14_SEMI_MODULAR_CUT_20260826'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def once(text,old,new,label):
    n=text.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 anchor, found {n}')
    return text.replace(old,new,1)

def main():
    cpp=CPP.read_text(); hpp=HPP.read_text(); cb=sha(CPP); hb=sha(HPP)
    if MARK in cpp and MARK in hpp:
        print('NACC_V14_PATCH=ALREADY_APPLIED'); print('Simulations.cpp_sha256='+cb); print('Simulations.hpp_sha256='+hb); return

    hpp=once(hpp,
        '#include "gsl_server/algorithms/PMFS/internal/RCECV13.hpp"\n',
        '#include "gsl_server/algorithms/PMFS/internal/RCECV13.hpp"\n#include "gsl_server/algorithms/PMFS/internal/NACCV14.hpp"\n',
        'NACC include')
    hpp=once(hpp,
        '        std::vector<std::string> rcecV13CandidateIds;\n        std::vector<std::vector<double>> rcecV13ConsensusHistory;\n',
        '        std::vector<std::string> rcecV13CandidateIds;\n        std::vector<std::vector<double>> rcecV13ConsensusHistory;\n'
        '        // NACC_V14_SEMI_MODULAR_CUT_20260826: native-only PMFS carrier.\n'
        '        // Restored before the next native source update so the suspect\n'
        '        // causal module cannot recursively contaminate native inference.\n'
        '        bool naccV14NativeCarrierAvailable = false;\n'
        '        std::vector<long double> naccV14NativeCarrierGrid;\n',
        'NACC carrier fields')

    cpp=once(cpp,
        '        rcecV13CandidateIds.clear();\n        rcecV13ConsensusHistory.clear();\n',
        '        rcecV13CandidateIds.clear();\n        rcecV13ConsensusHistory.clear();\n'
        '        // NACC_V14_SEMI_MODULAR_CUT_20260826: map/run boundary.\n'
        '        naccV14NativeCarrierAvailable = false;\n'
        '        naccV14NativeCarrierGrid.assign(sourceProb.data.size(), 0.0L);\n',
        'NACC map reset')

    cpp=once(cpp,
        '        const bool rcecCreiArm = rcecArm == "crei_latest";\n        const bool rcecFullArm = rcecArm == "rcec_full";\n        if (rcecArm != "v11_stouffer" && !rcecCreiArm && !rcecFullArm)\n',
        '        const bool rcecCreiArm = rcecArm == "crei_latest";\n        const bool rcecFullArm = rcecArm == "rcec_full";\n'
        '        const bool naccV14Arm = rcecArm == "nacc_v14";\n'
        '        if (rcecArm != "v11_stouffer" && !rcecCreiArm && !rcecFullArm && !naccV14Arm)\n',
        'NACC arm selector')

    # Restore the protected native state before the ordinary PMFS source update.
    anchor='''        tadmSourceUpdateId = sourceUpdateId;\n        tadmSimTime = simTime;\n        std::filesystem::create_directories(tadmDirectory);\n'''
    repl=anchor+'''        // NACC_V14_SEMI_MODULAR_CUT_20260826: cut recursive feedback.\n        const char* naccArmEnvironment = std::getenv("RCEC_V13_ARM");\n        const bool naccV14Requested = naccArmEnvironment != nullptr &&\n            std::string(naccArmEnvironment) == "nacc_v14";\n        if (naccV14Requested && naccV14NativeCarrierAvailable)\n        {\n            if (naccV14NativeCarrierGrid.size() != sourceProb.data.size())\n            {\n                GSL_ERROR("NACC V14 native carrier shape mismatch; disabling carrier restore");\n                naccV14NativeCarrierAvailable = false;\n            }\n            else\n            {\n                for (size_t cell = 0; cell < sourceProb.data.size(); ++cell)\n                    if (sourceProb.occupancy[cell] == Occupancy::Free)\n                        sourceProb.data[cell] = static_cast<double>(\n                            std::max(naccV14NativeCarrierGrid[cell], 0.0L));\n            }\n        }\n'''
    cpp=once(cpp,anchor,repl,'native-carrier restore')

    # On an unidentifiable update NACC leaves the fresh native state untouched
    # and stores it as the next native-only carrier.
    old='''            meAciEvidenceReservoir = pcAciActiveEvents;\n            const bool carryPrevious = inject && pcAciLastAcceptedUpdateId > 0 &&\n                pcAciCausalPosteriorGrid.size() == sourceProbInternal.size();\n'''
    new='''            meAciEvidenceReservoir = pcAciActiveEvents;\n            if (naccV14Arm)\n            {\n                naccV14NativeCarrierGrid.assign(sourceProbInternal.size(), 0.0L);\n                long double total = 0.0L;\n                for (size_t cell = 0; cell < sourceProbInternal.size(); ++cell)\n                    if (measuredHitProb.occupancy[cell] == Occupancy::Free &&\n                        std::isfinite(sourceProbInternal[cell]) && sourceProbInternal[cell] > 0.0)\n                        total += static_cast<long double>(sourceProbInternal[cell]);\n                if (total > 0.0L)\n                {\n                    for (size_t cell = 0; cell < sourceProbInternal.size(); ++cell)\n                        if (measuredHitProb.occupancy[cell] == Occupancy::Free)\n                            naccV14NativeCarrierGrid[cell] = std::max(\n                                static_cast<long double>(sourceProbInternal[cell]), 0.0L) / total;\n                    naccV14NativeCarrierAvailable = true;\n                }\n            }\n            const bool carryPrevious = inject && !naccV14Arm && pcAciLastAcceptedUpdateId > 0 &&\n                pcAciCausalPosteriorGrid.size() == sourceProbInternal.size();\n'''
    cpp=once(cpp,old,new,'NACC abstention semantics')

    # Replicated auxiliary score: current cumulative ACIT history, no second
    # temporal median over nested histories.
    anchor='''        std::vector<double> v11Scores(candidateCount, 0.0);\n        for (size_t s = 0; s < candidateCount; ++s)\n        {\n            v11Scores[s] = (evenRanks[s] + oddRanks[s]) / std::sqrt(2.0);\n            crossFitBlockScores[s] = {evenLogEvidence[s], oddLogEvidence[s],\n                                      evenRanks[s], oddRanks[s], v11Scores[s]};\n        }\n'''
    repl=anchor+'''        const std::vector<double> naccV14Scores =\n            nacc_v14::replicatedLowerEnvelope(evenRanks, oddRanks);\n'''
    cpp=once(cpp,anchor,repl,'NACC replicated score')
    cpp=once(cpp,
        '        logEvidence = activeScores;\n',
        '        if (naccV14Arm)\n            activeScores = naccV14Scores;\n        logEvidence = activeScores;\n',
        'NACC active score')

    # After the native shadow is normalized, preserve it as the trusted carrier
    # and replace the V11/RCEC replacement posterior by the KL-anchored tilt.
    anchor='''        if (nativeShadowTotal > 0.0L)\n            for (size_t cell = 0; cell < nativeShadow.size(); ++cell)\n                if (measuredHitProb.occupancy[cell] == Occupancy::Free)\n                    nativeShadow[cell] = std::max(nativeShadow[cell], 0.0L) / nativeShadowTotal;\n\n'''
    block=anchor+'''        if (naccV14Arm)\n        {\n            if (!(nativeShadowTotal > 0.0L))\n            {\n                GSL_ERROR("NACC V14 native anchor has zero mass");\n                return false;\n            }\n            naccV14NativeCarrierGrid = nativeShadow;\n            naccV14NativeCarrierAvailable = true;\n\n            std::vector<int> naccBestArea(sourceProbInternal.size(), std::numeric_limits<int>::max());\n            std::vector<double> naccCellCorrection(sourceProbInternal.size(), 0.0);\n            size_t naccCoveredCells = 0;\n            for (size_t s = 0; s < candidateCount; ++s)\n            {\n                const auto& rect = p2LastEvaluatedCandidates[s].rect;\n                const int area = rect[2] * rect[3];\n                for (int x = rect[0]; x < rect[0] + rect[2]; ++x)\n                    for (int y = rect[1]; y < rect[1] + rect[3]; ++y)\n                    {\n                        if (x < 0 || y < 0 || x >= measuredHitProb.metadata.dimensions.x ||\n                            y >= measuredHitProb.metadata.dimensions.y)\n                            continue;\n                        const size_t cell = measuredHitProb.metadata.indexOf({x, y});\n                        if (measuredHitProb.occupancy[cell] != Occupancy::Free || area > naccBestArea[cell])\n                            continue;\n                        if (naccBestArea[cell] == std::numeric_limits<int>::max())\n                            ++naccCoveredCells;\n                        naccBestArea[cell] = area;\n                        naccCellCorrection[cell] = naccV14Scores[s];\n                    }\n            }\n            if (naccCoveredCells != measuredHitProb.metadata.numFreeCells)\n            {\n                GSL_ERROR("NACC V14 candidate coverage {}/{}", naccCoveredCells,\n                          measuredHitProb.metadata.numFreeCells);\n                return false;\n            }\n            cellPosterior = nacc_v14::anchoredExponentialTilt(nativeShadow, naccCellCorrection);\n        }\n\n'''
    cpp=once(cpp,anchor,block,'NACC KL anchored tilt')

    # Auditable formula identity in the existing summary without disturbing
    # frozen V11/V13 labels.
    cpp=once(cpp,
        '                << "inverse_transport_sequential_replication_v3" << \'\\n\';\n',
        '                << (naccV14Arm ? "nacc_v14_native_anchored_semi_modular_v1" :\n'
        '                    "inverse_transport_sequential_replication_v3") << \'\\n\';\n',
        'NACC summary marker')

    combined=cpp+hpp
    for token in [MARK,'naccV14Arm','naccV14NativeCarrierGrid','nacc_v14::replicatedLowerEnvelope',
                  'nacc_v14::anchoredExponentialTilt','!naccV14Arm && pcAciLastAcceptedUpdateId']:
        if token not in combined: raise SystemExit('missing NACC postcondition: '+token)
    for token in ['nacc_temperature','nacc_alpha','truth_distance','house_specific_nacc']:
        if token in combined.lower(): raise SystemExit('forbidden adaptive/truth token: '+token)
    CPP.write_text(cpp); HPP.write_text(hpp)
    print('NACC_V14_PATCH=PASS')
    print('Simulations.cpp_before_sha256='+cb); print('Simulations.cpp_after_sha256='+sha(CPP))
    print('Simulations.hpp_before_sha256='+hb); print('Simulations.hpp_after_sha256='+sha(HPP))
    print('native_recursive_feedback=cut')
    print('operator=q_native_times_exp_replicated_lower_envelope')

if __name__=='__main__': main()
