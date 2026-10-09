#pragma once
#include <fstream>
#include <iomanip>
#include <cstdlib>
namespace R5Trace {
inline std::ofstream& stream(){static std::ofstream f; if(!f.is_open()){auto p=std::getenv("PMFS_R5_CONSUMERS");if(p){f.open(p);f<<"kind,receipt_ns,stamp_ns,frame,value,speed,direction,map_yaw,map_x,map_y,map_z\n"<<std::setprecision(17);}}return f;}
template<class T> inline void write(const T& m,int64_t now,const char* kind,double value,double speed,double direction,double yaw,double x,double y,double z){auto& f=stream();if(f){f<<kind<<","<<now<<","<<int64_t(m.header.stamp.sec)*1000000000LL+m.header.stamp.nanosec<<","<<m.header.frame_id<<","<<value<<","<<speed<<","<<direction<<","<<yaw<<","<<x<<","<<y<<","<<z<<"\n";f.flush();}}
}
