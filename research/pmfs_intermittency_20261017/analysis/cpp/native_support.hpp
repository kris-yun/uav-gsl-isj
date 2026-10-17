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
#include <stdexcept>
#include <cassert>
#include <DDA/Vectors.h>
#include <DDA/2D/RayCast.h>
#define GSL_ASSERT(x) assert(x)
#define GSL_ASSERT_MSG(x,...) assert(x)
#define GSL_ERROR(...) throw std::runtime_error("native diagnostic assertion")
namespace angles {inline double normalize_angle(double a){double r=fmod(a+M_PI,2*M_PI);return r<=0?r+M_PI:r-M_PI;}}
namespace GSL {
using Vector2=DDA::Vector2;using Vector2Int=DDA::Vector2Int;
namespace vmath {template<class V>float length(const V&v){return v.norm();} template<class V>V normalized(const V&v){return v.normalized();} template<class V>V rotate(const V&v,float a){return v.rotate(a);}}
enum class Occupancy {Obstacle=0,Free=1};
struct Grid2DMetadata {
 Vector2 origin;float cellSize;Vector2Int dimensions;uint16_t scale;size_t numFreeCells;
 Vector2Int coordinatesToIndices(float x,float y)const{return {(x-origin.x)/cellSize,(y-origin.y)/cellSize};}
 Vector2 indicesToCoordinates(Vector2Int v)const{return {origin.x+(v.x+.5f)*cellSize,origin.y+(v.y+.5f)*cellSize};}
 Vector2 indicesToCoordinates(int x,int y)const{return indicesToCoordinates(Vector2Int(x,y));}
 Vector2 indexToCoordinates(size_t i)const{return indicesToCoordinates(i%dimensions.x,i/dimensions.x);}
 size_t indexOf(size_t x,size_t y)const{return x+y*dimensions.x;}
 size_t indexOf(Vector2Int v)const{return indexOf(v.x,v.y);}
 bool indicesInBounds(Vector2Int v)const{return v.x>=0&&v.x<dimensions.x&&v.y>=0&&v.y<dimensions.y;}
};
template<class T>struct Grid2D {
 std::vector<T>&data;std::vector<Occupancy>&occupancy;Grid2DMetadata&metadata;
 T&dataAt(size_t x,size_t y)const{return data[metadata.indexOf(x,y)];}
 bool freeAt(size_t x,size_t y)const{return occupancy[metadata.indexOf(x,y)]==Occupancy::Free;}
};
namespace Utils {double lerp(double,double,double);double clamp(double,double,double);double evaluate1DGaussian(double,double);double evaluate2DGaussian(const Vector2&,const Vector2&,float);}
namespace Utils {Vector2 ExpectedValue(Grid2D<double>,double);double Variance(Grid2D<double>);}
namespace PMFS_internal {
struct HitProbability {double logOdds=0,auxWeight=0;Vector2 originalPropagationDirection;double omega=0,confidence=0,distanceFromRobot=0;};
struct HitProbKernel {double angle;Vector2 sigma;float valueAt1;};
struct HitProbabilitySettings {double prior=.3,kernelSigma=1.5,kernelStretchConstant=1.5,confidenceSigmaSpatial=1,confidenceMeasurementWeight=1;int localEstimationWindowSize=2;};
}
}
#include "visibility.hpp"
namespace GSL {class PMFSLib {using HashSet=std::unordered_set<Vector2Int>;using HitProbability=PMFS_internal::HitProbability;using HitProbKernel=PMFS_internal::HitProbKernel;
public:
static void EstimateHitProbabilities(Grid2D<HitProbability>&,const VisibilityMap&,PMFS_internal::HitProbabilitySettings&,bool,double,double,Vector2Int);
static double PropagateProbabilities(Grid2D<HitProbability>&,const PMFS_internal::HitProbabilitySettings&,HashSet&,HashSet&,HashSet&,const HitProbKernel&);
static double applyFalloffLogOdds(Vector2,const HitProbKernel&,const PMFS_internal::HitProbabilitySettings&);
};}
