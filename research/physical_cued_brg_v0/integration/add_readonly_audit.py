#!/usr/bin/env python3
"""Same read-only belief/estimate logging for native and all learned arms."""
import argparse, hashlib, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pmfs-dir',required=True);a=ap.parse_args();r=Path(a.pmfs_dir)
    h=r/'PMFS.hpp';c=r/'PMFS.cpp';u=r/'PMFS_utils.cpp'
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (h,c,u)}
    hs=h.read_text();assert hs.count('        void declareParameters() override;')==1
    hs=hs.replace('        void declareParameters() override;','        void auditBelief(const char* stage);\n        void declareParameters() override;')
    cs=c.read_text();needle='        // the wind estimation stuff requires spinning, so it must be done through the function queue'
    assert cs.count(needle)==1;cs=cs.replace(needle,'        auditBelief("initialized");\n\n'+needle)
    needle='            // Movement\n            movingState->chooseGoalAndMove();'
    assert cs.count(needle)==1;cs=cs.replace(needle,'            auditBelief(timeToSimulate ? "source_update" : "movement");\n'+needle)
    us=u.read_text();needle='        // 1. Search time.'
    assert us.count(needle)==1;us=us.replace(needle,'        auditBelief(result == GSLResult::Success ? "declared_success" : "terminal_failure");\n'+needle)
    us+='''
// Optional output only: never changes source, variance, RNG, planner, or stopping.
namespace GSL {
void PMFS::auditBelief(const char* stage) {
    const char* path = std::getenv("BRG_BELIEF_AUDIT_JSONL");
    if (!path || !*path) return;
    std::ofstream f(path, std::ios::app);
    if (!f) throw std::runtime_error("BRG belief audit cannot open");
    Vector2 estimate = Utils::ExpectedValue(Grid2D<double>(sourceProbability, occupancy, gridMetadata), 0.05);
    f << std::setprecision(17) << "{\\"stage\\":\\"" << stage << "\\",\\"time_s\\":" << node->now().seconds()
      << ",\\"search_time_s\\":" << (node->now()-startTime).seconds()
      << ",\\"iterations_counter\\":" << iterationsCounter
      << ",\\"brg_event_count\\":" << brgEvent << ",\\"width\\":" << gridMetadata.dimensions.x
      << ",\\"height\\":" << gridMetadata.dimensions.y << ",\\"resolution\\":" << gridMetadata.cellSize
      << ",\\"origin_x\\":" << gridMetadata.origin.x << ",\\"origin_y\\":" << gridMetadata.origin.y
      << ",\\"estimate_xy\\":[" << estimate.x << ',' << estimate.y << "],\\"free_cells\\":[";
    bool first=true;
    for(size_t i=0;i<occupancy.size();++i) if(occupancy[i]==Occupancy::Free){if(!first)f<<',';f<<i;first=false;}
    f << "],\\"source_map\\":[";
    for(size_t i=0;i<sourceProbability.size();++i){if(i)f<<',';f<<sourceProbability[i];}
    f << "],\\"variance_map\\":[";
    for(size_t i=0;i<simulations.varianceOfHitProb.size();++i){if(i)f<<',';f<<simulations.varianceOfHitProb[i];}
    f << "]}\\n";
    f.flush(); if(!f)throw std::runtime_error("BRG belief audit write failed");
}
}
'''
    for inc in ['#include <cstdlib>', '#include <iomanip>', '#include <stdexcept>']:
        if inc not in us:us=inc+'\n'+us
    for p,text in [(h,hs),(c,cs),(u,us)]:p.write_text(text)
    report={'read_only':True,'before':before,'after':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (h,c,u)}}
    (r/'READONLY_AUDIT_PATCH.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
