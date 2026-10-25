#include <bits/stdc++.h>
#include <gaden/Environment.hpp>
#include <gaden/internal/WindSequence.hpp>
#include <nlohmann/json.hpp>
using json=nlohmann::json;
int main(int argc,char**argv){try{
 if(argc!=5)throw std::runtime_error("export_wind scene map originalWind outputDir");
 std::ifstream in(argv[1]);json scene;in>>scene;gaden::Environment env;
 if(env.ReadFromFile(argv[2])!=gaden::ReadResult::OK)throw std::runtime_error("bad map");
 gaden::WindSequence seq;seq.Initialize({std::filesystem::path(argv[3])},env.numCells(),{});
 std::filesystem::path out(argv[4]);std::ofstream table(out/"REFERENCE_WIND_SAMPLING.csv");
 table<<"flat,col,row,x,y,z,voxel_i,voxel_j,voxel_k,voxel_flat,native3D_cell_state,PMFS_occupancy,reference_u,reference_v,reference_w,GMRF_u,GMRF_v\n"<<std::setprecision(17);
 int nx=scene["nx"],ny=scene["ny"];float ox=scene["origin"][0],oy=scene["origin"][1],cs=scene["cell_size"];int mismatch=0;
 for(int y=0;y<ny;y++)for(int x=0;x<nx;x++){
  int flat=x+nx*y;gaden::Vector3 p(ox+(x+.5f)*cs,oy+(y+.5f)*cs,.7f);auto idx=env.coordsToIndices(p);
  if(!env.IsInBounds(idx))throw std::runtime_error("coarse center outside physical grid");auto k=env.indexFrom3D(idx);auto v=seq.GetCurrent().at(k);int state=(int)env.at(idx);int occ=scene["occupancy"][flat];
  if(occ==0&&state!=0)mismatch++;
  table<<flat<<','<<x<<','<<y<<','<<p.x<<','<<p.y<<','<<p.z<<','<<idx.x<<','<<idx.y<<','<<idx.z<<','<<k<<','<<state<<','<<occ<<','<<v.x<<','<<v.y<<','<<v.z<<','<<scene["wind_xy"][flat][0].get<float>()<<','<<scene["wind_xy"][flat][1].get<float>()<<'\n';
  scene["wind_xy"][flat]=json::array({v.x,v.y});
 }
 std::ofstream(out/"E3_ORACLE_scene.json")<<std::setw(2)<<scene<<'\n';
 json result={{"numCells",env.numCells()},{"dimensions",{env.description.dimensions.x,env.description.dimensions.y,env.description.dimensions.z}},{"fine_cell_size",env.description.cellSize},{"fine_min_coord",{env.description.minCoord.x,env.description.minCoord.y,env.description.minCoord.z}},{"projection_z_query",.7f},{"coarse_cells",nx*ny},{"native3D_nonfree_centers_with_PMFS_free",mismatch},{"actual_parser","GADEN WindSequence::Initialize/GetCurrent and Environment::coordsToIndices/indexFrom3D"}};
 std::ofstream(out/"NATIVE_WIND_EXPORT_QA.json")<<std::setw(2)<<result<<'\n';std::cout<<result<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}}
