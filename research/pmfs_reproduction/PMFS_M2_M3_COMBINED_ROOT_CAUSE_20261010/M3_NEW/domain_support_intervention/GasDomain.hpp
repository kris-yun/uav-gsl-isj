#pragma once
#include "M3Audit.hpp"
namespace GasDomain {
inline bool enabled=false;
inline std::vector<GSL::Occupancy> occupancy;
inline std::vector<GSL::Occupancy> nav;
inline uint64_t navObstacleStart=0,navObstacleEnd=0,navObstacleSegmentMoves=0,navObstacleRecordedParticles=0;
inline uint64_t columnFreeOutsideNavCells=0;
inline uint64_t auditOutOfBoundsMoves=0;
template<class Grid> inline bool freeAt(const Grid& grid,int x,int y) {
 if(!enabled)return grid.freeAt(x,y);
 const GSL::Vector2Int ij(x,y);
 return grid.metadata.indicesInBounds(ij)&&occupancy[grid.metadata.indexOf(ij)]==GSL::Occupancy::Free;
}
template<class Grid> inline void movement(const Grid& grid,const GSL::Vector2& before,const GSL::Vector2& after) {
 if(!enabled)return;
 auto a=grid.metadata.coordinatesToIndices(before.x,before.y),b=grid.metadata.coordinatesToIndices(after.x,after.y);
 bool start=grid.metadata.indicesInBounds(a)&&!grid.freeAt(a.x,a.y);
 bool end=grid.metadata.indicesInBounds(b)&&!grid.freeAt(b.x,b.y);
 navObstacleStart+=start;navObstacleEnd+=end;
 // With native rollback (no slide), each accepted path is the straight segment from before to after.
 // Use the native nav visibility predicate solely as an audit, never to change gas motion.
 if(grid.metadata.indicesInBounds(a)&&grid.metadata.indicesInBounds(b)) {
   if(!GSL::GridUtils::PathFree(grid.metadata,grid.occupancy,before,after))navObstacleSegmentMoves++;
 } else auditOutOfBoundsMoves++;
}
inline void finish(const std::filesystem::path& output) {
 std::ofstream f(output/"GAS_DOMAIN_COUNTERS.json");f<<"{\"enabled\":"<<(enabled?"true":"false")<<",\"nav_obstacle_start_moves\":"<<navObstacleStart<<",\"nav_obstacle_end_moves\":"<<navObstacleEnd<<",\"native_PathFree_nav_obstacle_segment_moves\":"<<navObstacleSegmentMoves<<",\"recorded_particle_cell_instances_in_nav_obstacles\":"<<navObstacleRecordedParticles<<",\"gas_free_extra_cells\":"<<columnFreeOutsideNavCells<<",\"audit_out_of_bounds_moves_not_raychecked\":"<<auditOutOfBoundsMoves<<"}";
}
}
