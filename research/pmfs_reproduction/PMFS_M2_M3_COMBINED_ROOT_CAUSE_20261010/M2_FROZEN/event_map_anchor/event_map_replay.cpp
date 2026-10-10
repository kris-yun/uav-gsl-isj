// Frozen observation-process replay only. No ROS init, candidate transport,
// navigation, source posterior update, or truth metadata is accepted.
#include "Fixture.hpp"
#include <omp.h>
using namespace R4;
int main(int argc,char**argv) {
 try {
  if(argc!=5) throw std::runtime_error("usage: event_map_replay SNAPSHOT COVARIATES LABELS NEW_OUTPUT");
  fs::path snapshot=argv[1],covariates=argv[2],labels=argv[3],out=argv[4];
  if(fs::exists(out))throw std::runtime_error("output must be new");
  if(omp_get_max_threads()!=1)throw std::runtime_error("single OMP thread required");
  Fixture f(snapshot);f.meta.scale=25;
  if(f.meta.dimensions.x!=34||f.meta.dimensions.y!=45||f.meta.numFreeCells!=447||f.meta.cellSize!=.25)
    throw std::runtime_error("frozen B4 support mismatch");
  f.hp.prior=.3;f.hp.kernelSigma=1.5;f.hp.kernelStretchConstant=1.5;
  f.hp.confidenceSigmaSpatial=1;f.hp.confidenceMeasurementWeight=1;f.hp.localEstimationWindowSize=2;f.hp.maxUpdatesPerStop=5;
  auto events=csv(covariates),hits=csv(labels);
  if(events.size()!=50||hits.size()!=50)throw std::runtime_error("exactly 50 blocks required");
  fs::create_directory(out);
  std::ofstream contribution(out/"event_cell_lineage.csv"),ledger(out/"event_replay_ledger.csv");
  contribution<<std::setprecision(17)<<"block_id,cell_index,grid_i,grid_j,robot_i,robot_j,direct_robot_cell,logOdds_delta,omega_delta,logOdds_after,omega_after,confidence_after\n";
  ledger<<std::setprecision(17)<<"block_id,stop_id,update_ros_ns,x,y,robot_i,robot_j,wind_speed,wind_direction_to,event_hit\n";
  for(size_t j=0;j<50;j++) {
   auto& e=events[j];auto& h=hits[j];
   if(integer(e,"block_id")!=j||integer(h,"block_id")!=j)throw std::runtime_error("ordered block IDs required");
   int hit=integer(h,"event_hit");if(hit!=0&&hit!=1)throw std::runtime_error("binary event required");
   Vector2 p(float(d(e,"x")),float(d(e,"y")));Vector2Int ij=f.meta.coordinatesToIndices(p);
   if(!f.meta.indicesInBounds(ij)||!f.hitGrid().freeAt(ij.x,ij.y))throw std::runtime_error("illegal receptor support");
   auto before=f.hit;
   f.measurement(hit!=0,d(e,"wind_direction_to"),d(e,"wind_speed"),ij);
   ledger<<j<<','<<e.at("stop_id")<<','<<e.at("update_ros_ns")<<','<<p.x<<','<<p.y<<','<<ij.x<<','<<ij.y<<','<<d(e,"wind_speed")<<','<<d(e,"wind_direction_to")<<','<<hit<<'\n';
   for(size_t i=0;i<f.hit.size();i++)if(f.occupancy[i]==Occupancy::Free){auto gi=f.meta.indices2D(i);auto& a=f.hit[i];auto& b=before[i];
    contribution<<j<<','<<i<<','<<gi.x<<','<<gi.y<<','<<ij.x<<','<<ij.y<<','<<int(ij==gi)<<','<<a.logOdds-b.logOdds<<','<<a.omega-b.omega<<','<<a.logOdds<<','<<a.omega<<','<<a.confidence<<'\n';
   }
  }
  std::ofstream map(out/"map.csv");map<<std::setprecision(17)<<"cell_index,grid_i,grid_j,occupancy,logOdds,omega,confidence,probability,auxWeight,distanceFromRobot,propagation_x,propagation_y\n";
  for(size_t i=0;i<f.hit.size();i++){auto gi=f.meta.indices2D(i);auto& h=f.hit[i];
   map<<i<<','<<gi.x<<','<<gi.y<<','<<int(f.occupancy[i])<<','<<h.logOdds<<','<<h.omega<<','<<h.confidence<<','<<h.probability()<<','<<h.auxWeight<<','<<h.distanceFromRobot<<','<<h.originalPropagationDirection.x<<','<<h.originalPropagationDirection.y<<'\n';
  }
  std::ofstream result(out/"EXECUTION.json");result<<"{\"EstimateHitProbabilities_calls\":50,\"forward_calls\":0,\"source_posterior_updates\":0,\"ROS_nodes\":0,\"GADEN_realizations\":0,\"number_of_free_cells\":447}\n";
  std::cout<<"FROZEN_EVENT_MAP_REPLAY_COMPLETE\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
