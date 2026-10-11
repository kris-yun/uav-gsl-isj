import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent
s=(W/'Simulations_boundary_diagnostic.cpp').read_text(encoding='utf-8');s=s.replace('#include "M3Audit.hpp"','#include "M3Audit.hpp"\n#include "GasDomain.hpp"',1)
s=s.replace('        M3Audit::movement(before,filament.position,indices,afterIndices,blockedBefore);','        M3Audit::movement(before,filament.position,indices,afterIndices,blockedBefore);\n        GasDomain::movement(measuredHitProb,before,filament.position);',1)
s=s.replace('                // mark as updated so it doesn\'t count multiple filaments in the same timestep','                if(GasDomain::enabled && !measuredHitProb.freeAt(indices.x,indices.y))GasDomain::navObstacleRecordedParticles++;\n                // mark as updated so it doesn\'t count multiple filaments in the same timestep',1)
s=s.replace('                hitMap[i] = hitMap[i] / timesteps;\n        }','                hitMap[i] = hitMap[i] / timesteps;\n            else if(GasDomain::enabled)hitMap[i]=0.f;\n        }',1)
for pattern in ['measuredHitProb.freeAt(indexOrigin.x, indexOrigin.y)','measuredHitProb.freeAt(indexEnd.x, indexEnd.y)','measuredHitProb.freeAt(pair.x, pair.y)']:
 assert pattern in s;s=s.replace(pattern,'GasDomain::freeAt(measuredHitProb,'+pattern.split('freeAt(')[1],1)
e=(W/'candidate_forward.cpp').read_text(encoding='utf-8');e=e.replace('#include "M3Audit.hpp"','#include "M3Audit.hpp"\n#include "GasDomain.hpp"',1)
e=e.replace('        M3Audit::finish(output);','        M3Audit::finish(output);\n        GasDomain::finish(output);',1)
old='''    simulation.visibilityMap=&visibility;'''
# Keep the candidate/image/score space nav-based; only gas visibility gets the new occupancy domain.
new='''    GasDomain::enabled=job.at("gas_domain")=="column_union";
    if(!(GasDomain::enabled||job.at("gas_domain")=="native_nav"))throw std::runtime_error("gas domain");
    GasDomain::nav=occupancy;GasDomain::occupancy=occupancy;
    if(GasDomain::enabled) {
        const auto gasRows=csv(snapshot/"gas_mask.csv");
        if(gasRows.size()!=count)throw std::runtime_error("gas mask length");
        for(size_t i=0;i<count;i++) {
            if(integer(gasRows[i],"cell_index")!=i)throw std::runtime_error("gas mask cell ordering");
            GasDomain::occupancy[i]=integer(gasRows[i],"gas_transport_free")==1?Occupancy::Free:Occupancy::Obstacle;
            if(occupancy[i]==Occupancy::Free&&GasDomain::occupancy[i]!=Occupancy::Free)throw std::runtime_error("gas domain excludes original nav support");
            if(occupancy[i]!=Occupancy::Free&&GasDomain::occupancy[i]==Occupancy::Free)GasDomain::columnFreeOutsideNavCells++;
        }
    }
    VisibilityMap gasVisibility(meta.dimensions.x,meta.dimensions.y,5);
    if(GasDomain::enabled)for(int x=0;x<meta.dimensions.x;x++)for(int y=0;y<meta.dimensions.y;y++) {
        Vector2Int ij(x,y);std::vector<Vector2Int> visible;
        if(GasDomain::occupancy[meta.indexOf(ij)]==Occupancy::Free)for(int j=std::max(0,y-5);j<=std::min(meta.dimensions.y-1,y+5);j++)for(int i=std::max(0,x-5);i<=std::min(meta.dimensions.x-1,x+5);i++) {
            Vector2Int z(i,j);
            if(z==ij||GridUtils::PathFree(meta,GasDomain::occupancy,meta.indicesToCoordinates(ij),meta.indicesToCoordinates(z)))visible.push_back(z);
        }
        gasVisibility.emplace(ij,visible);
    }
    simulation.visibilityMap=GasDomain::enabled?&gasVisibility:&visibility;'''
assert old in e;e=e.replace(old,new,1)
e=e.replace('    M3Audit::wallSlide=job.at("boundary")=="slide";', '    M3Audit::wallSlide=job.at("boundary")=="slide";\n    if(M3Audit::wallSlide)throw std::runtime_error("domain test forbids slide change");',1)
e=e.replace('    const long double score=simulation.one(node,output,pointMode,exactPoint);','    if(!pointMode)throw std::runtime_error("domain test requires exactpoint");\n    const long double score=simulation.one(node,output,pointMode,exactPoint);',1)
for n,v in [('Simulations_gas_domain.cpp',s),('candidate_domain.cpp',e)]:
 p=W/n;assert not p.exists();p.write_text(v,encoding='utf-8',newline='\n')
print(json.dumps({n:hashlib.sha256((W/n).read_bytes()).hexdigest() for n in ['Simulations_gas_domain.cpp','candidate_domain.cpp','GasDomain.hpp']},indent=2))
