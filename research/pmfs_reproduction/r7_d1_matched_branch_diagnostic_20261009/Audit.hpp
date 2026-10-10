#pragma once
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#include <fstream>
#include <filesystem>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <array>
#include <unistd.h>

namespace GSL::Utils {
std::string r4_rng_state();
void r4_rng_restore(const std::string&);
}
namespace R4Audit {
namespace fs=std::filesystem;
using GSL::Utils::NQA::Node;
inline fs::path output;
inline std::ofstream candidate_log, point_stream;
inline size_t serial=0,point_count=0;
inline bool cache_ready=false,active=false;
inline uint16_t last_index=0;
inline std::string before_rng;
inline bool before_ready=false;
inline uint16_t before_index=0;
inline std::string id(const Node* n) {
 return "quadtree_"+std::to_string(n->origin.x)+"_"+std::to_string(n->origin.y)+"_"+std::to_string(n->size.x)+"_"+std::to_string(n->size.y);
}
template<class T> void binary(const fs::path& p,const std::vector<T>& a) {
 std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(a.data()),a.size()*sizeof(T));if(!f)throw std::runtime_error("capture write failed "+p.string());
}
inline void initialize(const fs::path& p) {
 if(active)throw std::runtime_error("capture already active");
 output=p;fs::create_directories(output/"maps");fs::create_directories(output/"points");
 candidate_log.open(output/"candidates.csv");candidate_log<<"serial,candidate_id,origin_i,origin_j,size_i,size_j,rng_before,rng_after,gaussian_ready_before,gaussian_index_before,gaussian_index_after,point_count,score,logscore,map_file,points_file\n";
 candidate_log<<std::setprecision(21);candidate_log.flush();active=true;
 if(!candidate_log)throw std::runtime_error("candidate sink unavailable");
}
inline void begin(const Node* n) {
 if(!active)throw std::runtime_error("capture not installed");
 before_rng=GSL::Utils::r4_rng_state();before_ready=cache_ready;before_index=last_index;point_count=0;
 point_stream.open(output/"points"/(id(n)+".f32"),std::ios::binary);
 if(!point_stream)throw std::runtime_error("point sink unavailable");
}
inline void point(const GSL::Vector2& p) {
 float a[2]={p.x,p.y};point_stream.write(reinterpret_cast<const char*>(a),sizeof(a));point_count++;
}
inline void gaussian(const std::array<float,2500>& table,uint16_t index) {
 if(cache_ready)return;
 std::vector<float> data(table.begin(),table.end());binary(output/"gaussian_cache.f32",data);
 std::ofstream f(output/"gaussian_initial.csv");f<<"index,rng_after_initialization\n"<<index<<","<<GSL::Utils::r4_rng_state()<<"\n";
 cache_ready=true;last_index=index;
}
inline void before_blur(const Node* n,const std::vector<float>& map) {
 binary(output/"maps"/(id(n)+"_unblurred.f32"),map);
}
inline void end(const Node* n,const std::vector<float>& map,long double score,uint16_t gaussian_index) {
 point_stream.close();if(!point_stream)throw std::runtime_error("sample sink failed");
 auto name=id(n);last_index=gaussian_index;binary(output/"maps"/(name+".f32"),map);
 candidate_log<<serial++<<","<<name<<","<<n->origin.x<<","<<n->origin.y<<","<<n->size.x<<","<<n->size.y<<","<<before_rng<<","<<GSL::Utils::r4_rng_state()<<","<<before_ready<<","<<before_index<<","<<last_index<<","<<point_count<<","<<score<<","<<std::log(score)<<",maps/"<<name<<".f32,points/"<<name<<".f32\n";candidate_log.flush();
}
inline void write_node(std::ostream& f,const Node* n,const std::string& parent) {
 bool children=false;for(const auto& c:n->children)if(c)children=true;
 f<<id(n)<<","<<parent<<","<<n->origin.x<<","<<n->origin.y<<","<<n->size.x<<","<<n->size.y<<","<<int(n->value)<<","<<children<<"\n";
 for(const auto& c:n->children)if(c)write_node(f,c.get(),id(n));
}
inline void tree(const std::vector<Node>& nodes,const std::string& filename) {
 std::ofstream f(output/filename);f<<"node_id,parent_id,origin_i,origin_j,size_i,size_j,value,has_children\n";
 for(const auto& n:nodes)write_node(f,&n,"ROOT");
}
inline void before_normalize(const std::vector<Node>& nodes,const std::vector<long double>& scores,const std::vector<GSL::Occupancy>& occupancy) {
 tree(nodes,"final_tree.csv");std::ofstream f(output/"raw_cell_scores.csv");f<<std::setprecision(21)<<"cell_index,score\n";
 long double sum=0;for(size_t i=0;i<scores.size();++i){f<<i<<","<<scores[i]<<"\n";if(occupancy[i]==GSL::Occupancy::Free)sum+=scores[i];}
 std::ofstream s(output/"normalization.txt");s<<std::setprecision(21)<<sum<<"\n";
}
inline void finish(const std::vector<double>& posterior) {
 binary(output/"posterior.f64",posterior);candidate_log.close();active=false;
}
}

namespace R4Replay {
inline std::vector<GSL::Vector2> points;
inline size_t offset=0;
inline bool enabled=false;
inline GSL::Vector2 use(const GSL::Vector2& generated) {
 if(!enabled)return generated;
 if(offset>=points.size())throw std::runtime_error("replay used too many points");
 return points[offset++];
}
}
