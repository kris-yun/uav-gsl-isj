#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
#include <DDA/Vectors.h>
#define ZoneScoped
#define GSL_ASSERT(x) assert(x)
using Vector2=DDA::Vector2; using Vector2Int=DDA::Vector2Int;
enum class Occupancy {Obstacle=0,Free=1};
struct Grid2DMetadata {Vector2 origin;float cellSize;Vector2Int dimensions;
size_t indexOf(const Vector2Int& v) const
        {
            return v.x + v.y * dimensions.x;
        }
Vector2 indexToCoordinates(int i, int j, bool centerOfCell = true) const
        {
            float offset = centerOfCell ? 0.5 : 0;
            return Vector2(origin.x + (i + offset) * cellSize, origin.y + (j + offset) * cellSize);
        }
};
template<class T> struct Grid2D { std::vector<T>&data;std::vector<Occupancy>&occupancy;Grid2DMetadata metadata; };
struct HitProbability {double logOdds=0,confidence=0,omega=0;};
namespace GSL::Utils {
double lerp(double start, double end, double proportion)
    {
        if (proportion < 0 || std::isnan(proportion))
            return start;

        return start + (end - start) * std::min(1.0, proportion);
    }
double logOddsToProbability(double lo)
    {
        return 1.0 - 1.0 / (1 + std::exp(lo));
    }
void NormalizeDistribution(Grid2D<double> variable)
    {
        // we account for the possibility of having positive and negative values by offsetting everything by the value of the minimum (capped at 0)
        // so, [-1, -0.5, 1, 2] would become [0, 0.5, 2, 3] before the normalization happens
        double total = 0;
        int count = 0;
        for (int i = 0; i < variable.data.size(); i++)
        {
            if (variable.occupancy[i] == Occupancy::Free)
            {
                total += variable.data[i];
                count++;
            }
        }

        #pragma omp parallel for
        for (int i = 0; i < variable.data.size(); i++)
        {
            if (variable.occupancy[i] == Occupancy::Free)
            {
                variable.data[i] = variable.data[i] / total;
            }
        }
    }
}
namespace Utils=GSL::Utils;
struct Simulations {struct Settings{double sourceDiscriminationPower=.2;}settings;
double sourceProbFromMaps(const Grid2D<HitProbability>&,const std::vector<float>&)const;};
double Simulations::sourceProbFromMaps(const Grid2D<HitProbability>& measuredHitProb, const std::vector<float>& hitMap) const
    {
        ZoneScoped;
        double total = 1;
        for (int i = 0; i < measuredHitProb.data.size(); i++)
        {
            if (measuredHitProb.occupancy[i] != Occupancy::Free)
                continue;
            double measured = Utils::logOddsToProbability(measuredHitProb.data[i].logOdds);
            const double& simulated = hitMap[i];
            double val =
                Utils::lerp(1, (1 - std::abs(measured - simulated) * settings.sourceDiscriminationPower), measuredHitProb.data[i].confidence);
            total *= val;
            GSL_ASSERT(!std::isnan(total));
        }
        return total;
    }
namespace upstream {
struct PMFS {Grid2DMetadata gridMetadata;std::vector<Occupancy>occupancy;std::vector<double>sourceProbability;
Vector2 expectedValueSource(double);double varianceSourcePosition();};
Vector2 PMFS::expectedValueSource(double proportionBest)
    {
        struct CellData
        {
            Vector2Int indices;
            double probability;
            CellData(Vector2Int ind, double prob)
            {
                indices = ind;
                probability = prob;
            }
        };
        std::vector<CellData> data;
        for (int i = 0; i < gridMetadata.dimensions.x; i++)
        {
            for (int j = 0; j < gridMetadata.dimensions.x; j++)
            {
                if (occupancy[gridMetadata.indexOf({i, j})] == Occupancy::Free)
                {
                    CellData cd(Vector2Int(i, j), sourceProbability[gridMetadata.indexOf({i, j})]);
                    data.push_back(cd);
                }
            }
        }

        std::sort(data.begin(), data.end(), [](const CellData & a, const CellData & b)
        {
            return a.probability > b.probability;
        });

        double averageX = 0, averageY = 0;
        double sum = 0;

        for (int i = 0; i < data.size() * proportionBest; i++)
        {
            CellData& cd = data[i];
            Vector2 coord = gridMetadata.indexToCoordinates(cd.indices.x, cd.indices.y);
            averageX += cd.probability * coord.x;
            averageY += cd.probability * coord.y;
            sum += cd.probability;
        }
        return Vector2(averageX / sum, averageY / sum);
    }
double PMFS::varianceSourcePosition()
    {
        Vector2 expected = expectedValueSource(1);
        double x = 0, y = 0;
        for (int i = 0; i < gridMetadata.dimensions.x; i++)
        {
            for (int j = 0; j < gridMetadata.dimensions.x; j++)
            {
                if (occupancy[gridMetadata.indexOf({i, j})] == Occupancy::Free)
                {
                    Vector2 coords = gridMetadata.indexToCoordinates(i, j);
                    double p = sourceProbability[gridMetadata.indexOf({i, j})];
                    x += pow(coords.x - expected.x, 2) * p;
                    y += pow(coords.y - expected.y, 2) * p;
                }
            }
        }
        return x + y;
    }
}
namespace ported {
struct PMFS {Grid2DMetadata gridMetadata;std::vector<Occupancy>occupancy;std::vector<double>sourceProbability;
Vector2 expectedValueSource(double);double varianceSourcePosition();};
Vector2 PMFS::expectedValueSource(double proportionBest)
    {
        struct CellData
        {
            Vector2Int indices;
            double probability;
            CellData(Vector2Int ind, double prob)
            {
                indices = ind;
                probability = prob;
            }
        };
        std::vector<CellData> data;
        for (int i = 0; i < gridMetadata.dimensions.x; i++)
        {
            for (int j = 0; j < gridMetadata.dimensions.y; j++)
            {
                if (occupancy[gridMetadata.indexOf({i, j})] == Occupancy::Free)
                {
                    CellData cd(Vector2Int(i, j), sourceProbability[gridMetadata.indexOf({i, j})]);
                    data.push_back(cd);
                }
            }
        }

        std::sort(data.begin(), data.end(), [](const CellData & a, const CellData & b)
        {
            return a.probability > b.probability;
        });

        double averageX = 0, averageY = 0;
        double sum = 0;

        for (int i = 0; i < data.size() * proportionBest; i++)
        {
            CellData& cd = data[i];
            Vector2 coord = gridMetadata.indexToCoordinates(cd.indices.x, cd.indices.y);
            averageX += cd.probability * coord.x;
            averageY += cd.probability * coord.y;
            sum += cd.probability;
        }
        return Vector2(averageX / sum, averageY / sum);
    }
double PMFS::varianceSourcePosition()
    {
        Vector2 expected = expectedValueSource(1);
        double x = 0, y = 0;
        for (int i = 0; i < gridMetadata.dimensions.x; i++)
        {
            for (int j = 0; j < gridMetadata.dimensions.y; j++)
            {
                if (occupancy[gridMetadata.indexOf({i, j})] == Occupancy::Free)
                {
                    Vector2 coords = gridMetadata.indexToCoordinates(i, j);
                    double p = sourceProbability[gridMetadata.indexOf({i, j})];
                    x += pow(coords.x - expected.x, 2) * p;
                    y += pow(coords.y - expected.y, 2) * p;
                }
            }
        }
        return x + y;
    }
}
double alpha_native(double omega) { struct {double omega;}cell{omega};struct {double confidenceMeasurementWeight=1.;}settings;
double exponent = -cell.omega / std::pow(settings.confidenceMeasurementWeight, 2);
return 1-std::exp(exponent);}
double alpha_p24(double omega) {return 1-std::exp(-omega*omega);}
template<class T>T get(std::ifstream&f){T v{};f.read(reinterpret_cast<char*>(&v),sizeof(v));if(!f)throw std::runtime_error("Truncated input");return v;}
struct Call {int x,y,sx,sy;double saved;std::vector<float>hit;};
int main(int argc,char**argv){try{
 if(argc!=2)return 2;std::ifstream f(argv[1],std::ios::binary);if(get<uint32_t>(f)!=0x1234abcd)return 3;int groups=get<int32_t>(f);
 // Exact native readout on a rectangle demonstrates the audited domain repair.
 upstream::PMFS old;ported::PMFS fixed;old.gridMetadata={{0,0},1,{3,5}};old.occupancy.assign(15,Occupancy::Free);old.sourceProbability.assign(15,1./15);fixed.gridMetadata=old.gridMetadata;fixed.occupancy=old.occupancy;fixed.sourceProbability=old.sourceProbability;
 if(std::abs(old.varianceSourcePosition()-.8)>1e-12||std::abs(fixed.varianceSourcePosition()-8./3)>1e-12)return 4;
 if(alpha_native(0)!=0||std::abs(alpha_native(1)-(1-std::exp(-1.)))>1e-15)return 5;
 std::cout<<std::setprecision(17)<<"group,calls,max_saved_score_relative_error,official_normalized_mass,official_variance_m2,official_top5_error_m,official_mean_error_m,p24_variance_m2,p24_posterior_max_abs_error\n";
 for(int g=0;g<groups;++g){
  int nx=get<int32_t>(f),ny=get<int32_t>(f),nf=get<int32_t>(f),nc=get<int32_t>(f);float ox=get<float>(f),oy=get<float>(f),cs=get<float>(f);double truthx=get<double>(f),truthy=get<double>(f);int n=nx*ny;
  ported::PMFS official,paper;official.gridMetadata={{ox,oy},cs,{nx,ny}};official.occupancy.assign(n,Occupancy::Obstacle);official.sourceProbability.assign(n,0);paper=official;
  std::vector<HitProbability>m(n);std::vector<double>reference(n);std::vector<int>legal;
  for(int i=0;i<nf;++i){int x=get<int32_t>(f),y=get<int32_t>(f),idx=x+nx*y;m[idx].logOdds=get<double>(f);m[idx].omega=get<double>(f);reference[idx]=get<double>(f);official.occupancy[idx]=paper.occupancy[idx]=Occupancy::Free;legal.push_back(idx);}
  std::vector<Call>calls;for(int i=0;i<nc;++i){Call c;c.x=get<int32_t>(f);c.y=get<int32_t>(f);c.sx=get<int32_t>(f);c.sy=get<int32_t>(f);c.saved=get<double>(f);if(get<int32_t>(f)!=n)return 6;c.hit.resize(n);f.read(reinterpret_cast<char*>(c.hit.data()),n*sizeof(float));if(!f)return 7;calls.push_back(c);}
  std::stable_sort(calls.begin(),calls.end(),[](const Call&a,const Call&b){return a.sx*a.sy>b.sx*b.sy;});Simulations calc;Grid2D<HitProbability>measured{m,official.occupancy,official.gridMetadata};double maxrel=0;
  for(auto&c:calls){for(auto&i:legal)m[i].confidence=alpha_p24(m[i].omega);calc.settings.sourceDiscriminationPower=1;double p=calc.sourceProbFromMaps(measured,c.hit);maxrel=std::max(maxrel,std::abs(p-c.saved)/std::max(std::abs(c.saved),1e-280));for(auto&i:legal)m[i].confidence=alpha_native(m[i].omega);calc.settings.sourceDiscriminationPower=.2;double q=calc.sourceProbFromMaps(measured,c.hit);
   for(int x=c.x;x<c.x+c.sx;++x)for(int y=c.y;y<c.y+c.sy;++y){official.sourceProbability[x+nx*y]=q;paper.sourceProbability[x+nx*y]=p;}}
  Utils::NormalizeDistribution(Grid2D<double>{official.sourceProbability,official.occupancy,official.gridMetadata});Utils::NormalizeDistribution(Grid2D<double>{paper.sourceProbability,paper.occupancy,paper.gridMetadata});double sum=0,maxdiff=0;for(int i:legal){sum+=official.sourceProbability[i];maxdiff=std::max(maxdiff,std::abs(paper.sourceProbability[i]-reference[i]));}if(std::abs(sum-1)>1e-12||maxrel>1e-10||maxdiff>1e-10)return 8;
  auto top=official.expectedValueSource(.05),mean=official.expectedValueSource(1);std::cout<<g<<','<<nc<<','<<maxrel<<','<<sum<<','<<official.varianceSourcePosition()<<','<<std::hypot(top.x-truthx,top.y-truthy)<<','<<std::hypot(mean.x-truthx,mean.y-truthy)<<','<<paper.varianceSourcePosition()<<','<<maxdiff<<'\n';
 }
 return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 9;}}
