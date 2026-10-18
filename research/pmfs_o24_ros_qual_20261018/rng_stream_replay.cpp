#include <xxHash/xxhash32.h>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <vector>
uint64_t hs(uint64_t h,uint64_t v){return(h^v)*1099511628211ULL;}
int main(int argc,char**argv){if(argc!=2)return 2;std::ifstream f(argv[1]);int records;f>>records;std::cout<<"record,uniform_draws,cache_draws,normal_draws,pass\n";
for(int r=0;r<records;++r){int ui,ci,index,initial,size,afterindex;uint32_t seed,state,afterstate;uint64_t uc,uh,au,ah,gc,gh,ag,agh,nc,nh,an,anh;std::string path,engine,dist,ae,ad;
 f>>ui>>seed>>state>>uc>>uh>>afterstate>>au>>ah>>ci>>index>>initial>>size>>gc>>gh>>afterindex>>ag>>agh>>nc>>nh>>an>>anh>>std::quoted(path)>>std::quoted(engine)>>std::quoted(dist)>>std::quoted(ae)>>std::quoted(ad);if(!f||au<uc||ag<gc||an<nc)return 3;
 auto olduc=uc,oldgc=gc,oldnc=nc;for(;uc<au;++uc){state=XXHash32::hash(&state,sizeof(state),seed);uh=hs(uh,state);}if(state!=afterstate||uh!=ah)return 4;
 std::vector<float>table;if(size){table.resize(size);std::ifstream t(path,std::ios::binary);t.read(reinterpret_cast<char*>(table.data()),size*4);if(!t)return 5;}
 if(!ci)index=initial;for(;gc<ag;++gc){index=(index+1)%size;uint32_t b;std::memcpy(&b,&table[index],4);gh=hs(gh,b);}if(gh!=agh||(ag>oldgc&&index!=afterindex))return 6;
 std::minstd_rand0 e;std::normal_distribution<>d(0.,1.);std::istringstream eis(engine);eis>>e;if(!eis)return 7;if(!dist.empty()){std::istringstream dis(dist);dis>>d;if(!dis)return 8;}
 for(;nc<an;++nc){double value=0.+d(e);uint64_t b;std::memcpy(&b,&value,8);nh=hs(nh,b);if(!ci&&an-oldnc==uint64_t(size)){float v=float(value);if(std::memcmp(&v,&table[nc-oldnc],4)!=0)return 9;}}
 if(nh!=anh)return 10;std::ostringstream eos,dos;eos<<e;dos<<std::setprecision(17)<<d;
 if(eos.str()!=ae||(!ad.empty()&&dos.str()!=ad))return 11;
 std::cout<<r<<','<<au-olduc<<','<<ag-oldgc<<','<<an-oldnc<<",1\n";
}return 0;}
