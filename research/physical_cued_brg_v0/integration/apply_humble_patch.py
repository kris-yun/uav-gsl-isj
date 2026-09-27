#!/usr/bin/env python3
"""Anchor-checked integration for inspected MAPIRlab humble PMFS layout.
Run --dry-run first. Not tested by compiling the complete ROS workspace here.
If user's frozen fork differs, FAIL; never fuzzy-patch it.
"""
import argparse,shutil,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def once(text,old,new):
    if text.count(old)!=1:raise ValueError(f'Expected one exact anchor: {old[:100]!r}; adapt explicitly to your fork, do not force.')
    return text.replace(old,new,1)

def main():
 p=argparse.ArgumentParser();p.add_argument('--pmfs-dir',required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args();root=Path(a.pmfs_dir)
 paths=[root/'PMFS.hpp',root/'PMFS.cpp',root/'MovingStatePMFS.cpp'];old={p:p.read_text() for p in paths};new=dict(old)
 h=paths[0];c=paths[1];m=paths[2]
 new[h]=once(new[h],'#pragma once','#pragma once\n#include "NeuralEvidenceClient.hpp"\n#include <memory>\n#include <cstdint>')
 block='''protected:
        // BRG v0 sidecar: fixed model-generated bank, one observed event at a time.
        bool brgEnabled = false;
        int brgPort = 17831, brgCandidates = 0;
        double brgSensorOffsetZ = 0.0;
        std::string brgBankHash, brgRunId;
        std::uint64_t brgEvent = 0;
        std::unique_ptr<pmfs_brg::Client> brgClient;
        pmfs_brg::Result brgLatest;
'''
 new[h]=once(new[h],'protected:',block)
 new[c]=once(new[c],'        Algorithm::declareParameters();','''        Algorithm::declareParameters();
        brgEnabled = getParam<bool>("brg_enabled", false);
        brgPort = getParam<int>("brg_port", 17831);
        brgCandidates = getParam<int>("brg_candidates", 0);
        brgSensorOffsetZ = getParam<double>("brg_sensor_offset_z_m", 0.0);
        brgBankHash = getParam<std::string>("brg_bank_sha256", "");
        brgRunId = getParam<std::string>("brg_run_id", "");''')
 new[c]=once(new[c],'        iterationsCounter = 0;','''        iterationsCounter = 0;
        brgEvent = 0; brgClient.reset();''')
 anchor='''        static int number_of_updates = 0;'''
 inject='''        static int number_of_updates = 0;
        if (brgEnabled)
        {
            // Called once per delivered stop-and-measure event, NOT per tick.
            // Timestamp below is receipt / simulation-clock time. The first
            // model uses order, not dt; log acquisition window separately.
            if (!brgClient)
            {
                if (brgCandidates < 2 || brgBankHash.empty() || brgRunId.empty())
                    throw std::runtime_error("Explicit BRG candidate bank and run contract required");
                if (static_cast<size_t>(brgCandidates) != gridMetadata.numFreeCells)
                    throw std::runtime_error("Full-support comparison required; do not deploy six-label demo bank against native full PMFS");
                brgClient = std::make_unique<pmfs_brg::Client>(brgPort, brgBankHash, brgCandidates, sourceProbability.size());
                brgClient->validateGrid(gridMetadata.dimensions.x, gridMetadata.dimensions.y,
                    gridMetadata.cellSize, gridMetadata.origin.x, gridMetadata.origin.y);
                brgClient->reset(brgRunId);
            }
            brgLatest = brgClient->observe(brgEvent++, node->now().seconds(),
                currentRobotPose.pose.pose.position.x, currentRobotPose.pose.pose.position.y,
                currentRobotPose.pose.pose.position.z + brgSensorOffsetZ, concentration);
        }'''
 new[c]=once(new[c],anchor,inject)
 new[c]=once(new[c],'            // Movement\n            movingState->chooseGoalAndMove();','''            // Replace BOTH posterior and planner belief-dependent cache.
            if (brgEnabled && timeToSimulate)
            {
                for (size_t i = 0; i < sourceProbability.size(); ++i)
                    if (brgLatest.sourceMap[i] > 0 && occupancy[i] != Occupancy::Free)
                        throw std::runtime_error("BRG support includes native obstacle cell");
                simulations.varianceOfHitProb.resize(sourceProbability.size());
                pmfs_brg::apply(brgLatest, sourceProbability, simulations.varianceOfHitProb);
            }
            // Movement
            movingState->chooseGoalAndMove();''')
 # This routine's MI values are visualization-only in inspected upstream; native
 # movement uses varianceOfHitProb. Skip stale coarse-simulation visualization in
 # neural mode, preserving original decision formula, reachability and fallback.
 new[m]=once(new[m],'        calculateMutualInformationGas();','        if (!pmfs->brgEnabled) calculateMutualInformationGas();')
 report={str(p.name):{'before':hashlib.sha256(old[p].encode()).hexdigest(),'after':hashlib.sha256(new[p].encode()).hexdigest()} for p in paths}
 print(json.dumps(report,indent=2))
 if a.dry_run:return
 for p in paths:
  b=p.with_suffix(p.suffix+'.pre_brg')
  if b.exists():raise FileExistsError(b)
 for p in paths:
  shutil.copyfile(p,p.with_suffix(p.suffix+'.pre_brg'));p.write_text(new[p])
 shutil.copyfile(HERE/'NeuralEvidenceClient.hpp',root/'NeuralEvidenceClient.hpp')
 (root/'BRG_PATCH_MANIFEST.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
