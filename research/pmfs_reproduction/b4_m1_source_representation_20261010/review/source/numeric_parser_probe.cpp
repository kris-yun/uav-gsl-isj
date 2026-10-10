#include <map>
#include <string>
#include <stdexcept>
#include <cmath>
#include <cerrno>
#include <cstdlib>
#include <iostream>
using Row=std::map<std::string,std::string>;
double checkedDouble(const Row& row,const char* key) {
    const auto& text=row.at(key);char* end=nullptr;errno=0;
    double value=std::strtod(text.c_str(),&end);
    if(end==text.c_str()||*end!='\0'||!std::isfinite(value))
        throw std::runtime_error(std::string("invalid finite numeric field ")+key);
    return value;
}


int main(){
 for(auto s:{"3.1908919011361254e-312","4.4673415696965513e-319"}) {
  bool failed=false;try{std::stod(s);}catch(const std::out_of_range&){failed=true;}
  if(!failed)return 2;
  std::cout<<s<<","<<std::hexfloat<<checkedDouble(Row{{"x",s}},"x")<<"\n";
 }
 for(auto s:{"","nan","inf","1.2garbage"}) {
  bool rejected=false;try{checkedDouble(Row{{"x",s}},"x");}catch(const std::runtime_error&){rejected=true;}
  if(!rejected)return 3;
 }
}
