// Native-core, fixed-route diagnostic; NOT ROS scheduling parity or 3-D wind.
#include <gmrf_wind_core/gmrf_map.h>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <map>
int main(int argc, char** argv) {
  try {
    if(argc<4 || argc>6) throw std::runtime_error("usage: replay map.txt observations.txt output.txt [iterations] [aligned-geometry|aligned-field]");
    const int iterations=argc>=5?std::stoi(argv[4]):1;
    const bool geometry_only=argc==6 && std::string(argv[5])=="aligned-geometry";
    const bool latest_per_cell=argc==6 && std::string(argv[5])=="aligned-latest-per-cell";
    const bool aligned=geometry_only || latest_per_cell || (argc==6 && std::string(argv[5])=="aligned-field");
    if(argc==6&&!aligned) throw std::runtime_error("unknown mode");
    if(iterations<1||iterations>50) throw std::runtime_error("iterations outside 1..50");
    std::ifstream mapin(argv[1]), obs(argv[2]);
    gmrfw::TOccupancyMap map;
    if(!(mapin>>map.width>>map.height>>map.resolution>>map.origin_x>>map.origin_y)) throw std::runtime_error("map header");
    for(size_t i=0;i<map.width*map.height;++i){int v; if(!(mapin>>v)||(v!=0&&v!=100)) throw std::runtime_error("map cell"); map.data.push_back(v);}
    // Optional geometry audit: coordinate translation, not snapping observations.
    // Match map resolution and anchor local origin to zero to avoid global rounding.
    const double offset_x=aligned?map.origin_x:0, offset_y=aligned?map.origin_y:0;
    if(aligned){map.origin_x=0;map.origin_y=0;}
    gmrfw::CGMRF_map::Parameters p;
    // Explicit gmrf_node defaults, not presumed historic launch parameters.
    p.cell_size=.5; p.lambdaPrior_advection=100; p.lambdaPrior_mass_conservation=100;
    p.lambdaPrior_diffusion=100; p.lambdaPrior_obstacles=10;
    if(aligned) p.cell_size=map.resolution;
    gmrfw::CGMRF_map field(map,p,false,false);
    std::ofstream out(argv[3]); if(!out) throw std::runtime_error("output");
    std::ofstream rejected_out(std::string(argv[3])+".rejected");
    out.exceptions(std::ios::badbit|std::ios::failbit);
    rejected_out.exceptions(std::ios::badbit|std::ios::failbit);
    rejected_out<<std::setprecision(17);
    out<<std::setprecision(17)<<"# diagnostic available_s x y estimated_u estimated_v\n";
    double t,x,y,u,v,last=0,next=2; size_t accepted=0,rejected=0,frames=0;
    while(obs>>t>>x>>y>>u>>v){
      if(!std::isfinite(t+x+y+u+v)||t<=last) throw std::runtime_error("observation clock/value");
      last=t;
      if(field.insertObservation_GMRF(std::hypot(u,v),std::atan2(v,u),.0001,.0001,x-offset_x,y-offset_y)) ++accepted;
      else {++rejected; rejected_out<<t<<' '<<x<<' '<<y<<'\n';}
      if(geometry_only) continue;
      if(t+1e-8<next) continue;
      if(latest_per_cell){
        // Source-blind diagnostic intervention on observation retention only.
        // No gas/true source, time-window fitting, or observation relocation.
        std::map<size_t,gmrfw::TobservationGMRF> latest;
        for(const auto& observation:field.getObservations_GMRF()) latest[observation.cell_idx]=observation;
        std::vector<gmrfw::TobservationGMRF> retained;
        for(const auto& entry:latest) retained.push_back(entry.second);
        field.setObservations_GMRF(retained);
        std::cout<<"retained t="<<t<<" cells="<<retained.size()<<'\n';
      }
      field.MAP_estimation_GMRF(iterations);
      const auto size=field.map_size();
      for(int i=0;i<size.x()*size.y();++i) if(field.is_cell_free(i)){
        double gx,gy; field.id2xy_public(i,gx,gy); auto w=field.getEstimation(i);
        if(!std::isfinite(w.x+w.y)) throw std::runtime_error("nonfinite estimate");
        out<<t<<' '<<gx+offset_x<<' '<<gy+offset_y<<' '<<w.x<<' '<<w.y<<'\n';
      }
      ++frames; next+=2;
    }
    if(!obs.eof()||(!frames&&!geometry_only)||!accepted) throw std::runtime_error("incomplete input");
    out.flush(); rejected_out.flush();
    std::cout<<"frames="<<frames<<" accepted="<<accepted<<" rejected="<<rejected<<" final_s="<<last<<std::endl;
  } catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}
}
