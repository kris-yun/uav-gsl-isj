#pragma once
// Linux/POSIX, C++17. Localhost only. This is an independently written bridge.
// Exceptions must abort/mark the NEW arm invalid, not silently fall back to native.
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cerrno>
#include <cstdint>
#include <cmath>
#include <cstring>
#include <iomanip>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace pmfs_brg {
struct Result { std::vector<double> q,sourceMap,hitVariance; };
class Client {
 int fd_=-1; std::string buffer_,bank_,run_; size_t sources_=0,cells_=0; int nx_=0,ny_=0; double dx_=0,ox_=0,oy_=0;
 void sendLine(const std::string& s) {
  size_t n=0; while(n<s.size()) {ssize_t k=::send(fd_,s.data()+n,s.size()-n,MSG_NOSIGNAL);if(k<=0)throw std::runtime_error("BRG send failed");n+=size_t(k);}
 }
 std::string line() {
  for(;;){auto p=buffer_.find('\n');if(p!=std::string::npos){auto s=buffer_.substr(0,p);buffer_.erase(0,p+1);if(s.rfind("ERROR",0)==0)throw std::runtime_error(s);return s;}
   char a[8192];auto k=::recv(fd_,a,sizeof(a),0);if(k<=0)throw std::runtime_error("BRG receive timeout/closed");buffer_.append(a,size_t(k));if(buffer_.size()>4*1024*1024)throw std::runtime_error("BRG oversized response");}
 }
 static std::vector<double> vector(const std::string& s,size_t n) {
  std::istringstream in(s);std::vector<double> v(n);for(auto &x:v)if(!(in>>x)||!std::isfinite(x)||x<0)throw std::runtime_error("BRG invalid vector");std::string extra;if(in>>extra)throw std::runtime_error("BRG wrong vector length");return v;
 }
public:
 Client(int port,const std::string& expectedBank,size_t sources,size_t cells):bank_(expectedBank),sources_(sources),cells_(cells) {
  if(port<=0||port>65535)throw std::runtime_error("invalid TCP port");
  fd_=::socket(AF_INET,SOCK_STREAM,0);if(fd_<0)throw std::runtime_error("socket failed");
  timeval t{5,0};setsockopt(fd_,SOL_SOCKET,SO_RCVTIMEO,&t,sizeof(t));setsockopt(fd_,SOL_SOCKET,SO_SNDTIMEO,&t,sizeof(t));
  sockaddr_in a{};a.sin_family=AF_INET;a.sin_port=htons(port);inet_pton(AF_INET,"127.0.0.1",&a.sin_addr);
  if(::connect(fd_,reinterpret_cast<sockaddr*>(&a),sizeof(a))<0){::close(fd_);fd_=-1;throw std::runtime_error("BRG connect failed");}
  try{sendLine("HELLO\n");std::istringstream in(line());std::string tag,b;size_t s,c;if(!(in>>tag>>b>>s>>c>>nx_>>ny_>>dx_>>ox_>>oy_)||tag!="HELLO"||b!=bank_||s!=sources_||c!=cells_)throw std::runtime_error("BRG handshake mismatch");}
  catch(...){::close(fd_);fd_=-1;throw;}
 }
 Client(const Client&)=delete;Client& operator=(const Client&)=delete;
 ~Client(){if(fd_>=0)::close(fd_);}
 void validateGrid(int nx,int ny,double dx,double ox,double oy) const {
  if(nx!=nx_||ny!=ny_||std::abs(dx-dx_)>1e-7||std::abs(ox-ox_)>1e-5||std::abs(oy-oy_)>1e-5)throw std::runtime_error("BRG/native grid geometry mismatch");
 }
 void reset(const std::string& run) {
  if(run.empty()||run.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")!=std::string::npos)throw std::runtime_error("invalid run token");
  sendLine("RESET "+run+" "+bank_+"\n");if(line()!="RESET "+bank_)throw std::runtime_error("BRG reset failed");run_=run;
 }
 Result observe(uint64_t event,double time,double x,double y,double z,double ppm) {
  if(run_.empty())throw std::runtime_error("reset first");
  std::ostringstream out;out<<std::setprecision(17)<<"STEP "<<run_<<' '<<event<<' '<<time<<' '<<x<<' '<<y<<' '<<z<<' '<<ppm<<' '<<bank_<<'\n';sendLine(out.str());
  std::istringstream in(line());std::string tag,b;uint64_t eid;size_t s,c;
  if(!(in>>tag>>eid>>b>>s>>c)||tag!="OK"||eid!=event||b!=bank_||s!=sources_||c!=cells_)throw std::runtime_error("BRG response mismatch");
  Result r;r.q=vector(line(),sources_);r.sourceMap=vector(line(),cells_);r.hitVariance=vector(line(),cells_);
  if(std::abs(std::accumulate(r.q.begin(),r.q.end(),0.)-1)>1e-6||std::abs(std::accumulate(r.sourceMap.begin(),r.sourceMap.end(),0.)-1)>1e-6)throw std::runtime_error("BRG mass error");
  for(auto v:r.hitVariance) { if(v>0.250001)throw std::runtime_error("BRG variance range error"); }
  return r;
 }
};
// Apply after native simulation bookkeeping and BEFORE chooseGoalAndMove().
// Native mode never calls this function. No posterior multiplication here.
inline void apply(const Result& r,std::vector<double>& sourceProbability,std::vector<double>& varianceOfHitProb) {
 if(r.sourceMap.size()!=sourceProbability.size()||r.hitVariance.size()!=varianceOfHitProb.size())throw std::runtime_error("native grid size mismatch");
 sourceProbability=r.sourceMap;varianceOfHitProb=r.hitVariance;
}
}
