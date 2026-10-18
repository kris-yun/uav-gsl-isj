#include "support.hpp"
// This helper generates only native constructor states, not gas trajectories.
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("export_states JOBS ROOT");
 std::ifstream f(argv[1]);std::string s;std::getline(f,s);std::vector<std::string>h;auto split=[](std::string s){std::vector<std::string>a;std::stringstream t(s);std::string v;while(std::getline(t,v,','))a.push_back(v);return a;};if(s.back()=='\r')s.pop_back();h=split(s);
 std::ofstream out(std::filesystem::path(argv[2])/"inputs/CONSTRUCTOR_STATES.csv");out<<"key,seed,rng_before,gaussian_before\n";
 while(std::getline(f,s)){if(!s.empty()&&s.back()=='\r')s.pop_back();auto v=split(s);std::map<std::string,std::string>r;for(size_t i=0;i<h.size();i++)r[h[i]]=v[i];
  GSL::Utils::restore_rng(r.at("seed"));
  GSL::Utils::PrecalculatedGaussian<2500> state;
  std::array<float,2500> table;auto before=state.index();
  // Read values by cycling nextValue, then rotate back to the original index.
  // This consumes no native RNG and restores the exact original cyclic table.
  for(int k=1;k<=2500;k++)table[(before+k)%2500]=state.nextValue(0,1);
  auto p=std::filesystem::path(argv[2])/"inputs"/r.at("key")/("cache_fine_"+r.at("seed")+".f32");std::ofstream b(p,std::ios::binary);b.write(reinterpret_cast<char*>(table.data()),sizeof(table));if(!b)throw std::runtime_error("cache export failed");
  out<<r.at("key")<<","<<r.at("seed")<<","<<GSL::Utils::rng_state()<<","<<before<<"\n";
 }
 return 0;
 }catch(std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
