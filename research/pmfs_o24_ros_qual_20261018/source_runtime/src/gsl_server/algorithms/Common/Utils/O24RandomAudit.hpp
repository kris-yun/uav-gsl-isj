#pragma once
#include <cstdint>
#include <string>
namespace GSL::Utils {
struct O24Snapshot { bool ui=false,ci=false;uint32_t seed=0,state=65535;uint64_t uc=0,uh=1469598103934665603ULL,gc=0,gh=1469598103934665603ULL,nc=0,nh=1469598103934665603ULL,tid=0;int size=0,index=-1,initial=-1;std::string engine,distribution;std::string json()const;};
void O24NoteUniform(uint32_t*seed,uint32_t*state);
void O24NoteNormal(void*distribution,double value);
void O24NoteCache(uint16_t*index,const float*table,int size);
void O24NoteCacheNext(float value);
O24Snapshot O24Capture();
void O24WriteCache(const std::string&prefix);
}
