#include "NeuralEvidenceClient.hpp"
#include <iostream>
int main(int argc,char**argv){
 if(argc!=11){std::cerr<<"port bankhash S N x y z c time event\n";return 2;}
 try{pmfs_brg::Client c(std::stoi(argv[1]),argv[2],std::stoul(argv[3]),std::stoul(argv[4]));c.reset("compiled_cpp_smoke");
 auto r=c.observe(std::stoull(argv[10]),std::stod(argv[9]),std::stod(argv[5]),std::stod(argv[6]),std::stod(argv[7]),std::stod(argv[8]));std::cout<<"OK "<<r.q.size()<<' '<<r.sourceMap.size()<<' '<<std::accumulate(r.q.begin(),r.q.end(),0.)<<'\n';return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
