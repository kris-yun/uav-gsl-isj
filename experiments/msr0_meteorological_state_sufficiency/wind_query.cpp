#include <gaden/Environment.hpp>
#include <gaden/internal/WindSequence.hpp>
#include <fstream>
#include <sstream>
#include <iostream>
#include <iomanip>
// Wind-only executable: never opens a gas iteration, source manifest or source truth.
int main(int argc,char**argv){
 if(argc!=5)return 2;
 gaden::Environment e;e.ReadFromFile(argv[1]);gaden::WindSequence seq;
 std::vector<std::filesystem::path> files;
 for(int i=0;i<=10;i++)files.push_back(std::string(argv[2])+"/wind_iteration_"+std::to_string(i));
 seq.Initialize(files,e.numCells(),{false,0,0});
 std::ifstream in(argv[3]);std::ofstream out(argv[4]);std::string line;getline(in,line);
 struct P{int id;gaden::Vector3 q;};std::vector<P> points;
 while(getline(in,line)){for(auto&c:line)if(c==',')c=' ';std::istringstream s(line);P p;s>>p.id>>p.q.x>>p.q.y>>p.q.z;points.push_back(p);}
 out<<std::setprecision(9)<<"state,point_id,valid,u,v,w\n";
 for(size_t state=0;state<=10;state++){
  seq.SetCurrentIndex(state);
  for(auto&p:points){auto ix=e.coordsToIndices(p.q);bool ok=e.at(ix)==gaden::Environment::CellState::Free;
   auto w=ok?seq.GetCurrent().at(e.indexFrom3D(ix)):gaden::Vector3{0,0,0};
   out<<state<<','<<p.id<<','<<ok<<','<<w.x<<','<<w.y<<','<<w.z<<'\n';}
 }
 out.flush();if(!out)return 5;
}
