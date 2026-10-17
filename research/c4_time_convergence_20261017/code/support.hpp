#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <vector>
#include <unordered_set>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <memory>
#include <map>
#include <filesystem>
#include <random>
#include <chrono>
#include <ctime>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <DDA/Vectors.h>
#include <DDA/2D/RayCast.h>
#define GSL_ASSERT(x) do { if(!(x)) throw std::runtime_error("Native assertion: " #x); } while(0)
#define GSL_ASSERT_MSG(x,...) GSL_ASSERT(x)
#define GSL_ERROR(...) throw std::runtime_error("Native visibility error")
#define ZoneScoped
#define ZoneScopedN(x)
namespace GSL {
using Vector2=DDA::Vector2;using Vector2Int=DDA::Vector2Int;
namespace vmath {template<class V>float length(const V&v){return v.norm();}template<class V>V normalized(const V&v){return v.normalized();}template<class V>V rotate(const V&v,float a){return v.rotate(a);}}
enum class Occupancy {Obstacle=0,Free=1};
namespace Utils {
double lerp(double,double,double);double clamp(double,double,double);double logOddsToProbability(double);
double randomFromGaussian(double,double);float uniformRandomF(float,float);double uniformRandom(double,double);
void restore_rng(const std::string&);std::string rng_state();
template<size_t Size>class PrecalculatedGaussian {
 public:
 PrecalculatedGaussian(){m_index=uniformRandom(0,Size);for(size_t i=0;i<Size;i++)m_precalculatedTable[i]=randomFromGaussian(0,1);}
 float nextValue(float mean,float stdev){m_index=(m_index+1)%Size;return mean+stdev*m_precalculatedTable[m_index];}
 void restore(const std::array<float,Size>&t,uint16_t i){m_precalculatedTable=t;m_index=i;}
 uint16_t index()const{return m_index;}
 private:uint16_t m_index;std::array<float,Size>m_precalculatedTable;
};
}
}
#include "grid.hpp"
#include "visibility.hpp"
#include "hit.hpp"
namespace diag {
inline uint64_t moves=0,releases=0;inline bool replay=false;inline size_t offset=0;
inline std::vector<GSL::Vector2>points;
inline GSL::Vector2 source_point(GSL::Vector2 generated){if(!replay)return generated;if(offset>=points.size())throw std::runtime_error("Archived source release exhausted");return points[offset++];}
}
namespace GSL::Utils::NQA {struct Node {Vector2Int origin,size;};}
namespace GSL::PMFS_internal {
struct SimulationSettings {double deltaTime=.1,noiseSTDev=.5;int iterationsToRecord=200,minWarmupIterations=200,maxWarmupIterations=500;double blurSigmaX=1.5,blurSigmaY=1.5,sourceDiscriminationPower=.3;};
struct Filament {Vector2 position;};
struct SimulationSource {
 enum Mode {Quadtree,Point};const Mode mode;const Utils::NQA::Node*nqaNode;const Vector2 point;const Grid2DMetadata&metadata;
 SimulationSource(const Utils::NQA::Node*n,const Grid2DMetadata&m):mode(Quadtree),nqaNode(n),point(0,0),metadata(m){}
 SimulationSource(const Vector2&p,const Grid2DMetadata&m):mode(Point),nqaNode(nullptr),point(p),metadata(m){}
 Vector2 getPoint()const;
};
class Simulations {
 public:
 const SimulationSettings&settings;Grid2D<HitProbability>measuredHitProb;Grid2D<Vector2>wind;
 VisibilityMap*visibilityMap;cv::Mat freeSpaceMask;
 Simulations(const SimulationSettings&s,Grid2D<HitProbability>h,Grid2D<Vector2>w):settings(s),measuredHitProb(h),wind(w){}
 long double sourceProbFromMaps(const Grid2D<HitProbability>&,const std::vector<float>&)const;
 double probabilityFromSingleCell(HitProbability,double)const;double probabilitySingleFrequency(double,double)const;
 void moveFilament(Filament&,Vector2Int&,float,float)const;bool filamentIsOutside(const Filament&)const;
 void simulateSourceInPosition(const SimulationSource&,std::vector<float>&,bool,int,float,float)const;
 bool moveAlongPath(Vector2&,const Vector2&)const;void blurHitMap(cv::Mat&)const;
};
extern thread_local Utils::PrecalculatedGaussian<2500>gaussian;
}
