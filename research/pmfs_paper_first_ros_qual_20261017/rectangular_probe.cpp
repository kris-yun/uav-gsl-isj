#include <algorithm>
#include <cmath>
#include <iostream>
#include <vector>
#include <iomanip>
struct Vector2 {float x=0,y=0;Vector2()=default;Vector2(double a,double b):x(a),y(b){}};
struct Vector2Int {int x=0,y=0;Vector2Int()=default;Vector2Int(int a,int b):x(a),y(b){}};
enum class Occupancy {Free};
struct Grid2DMetadata {Vector2Int dimensions{0,0};size_t indexOf(Vector2Int p)const{return p.x+p.y*dimensions.x;}Vector2 indexToCoordinates(int i,int j)const{return Vector2(i+.5,j+.5);}};
namespace native {
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
namespace fixed {
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
int main(){std::cout<<std::setprecision(17);fixed::PMFS b;native::PMFS a;
 a.gridMetadata.dimensions={3,5};a.occupancy.assign(15,Occupancy::Free);a.sourceProbability.assign(15,1./15);b.gridMetadata=a.gridMetadata;b.occupancy=a.occupancy;b.sourceProbability=a.sourceProbability;
 double nativeVariance=a.varianceSourcePosition(),fixedVariance=b.varianceSourcePosition();
 if(std::abs(nativeVariance-.8)>1e-12||std::abs(fixedVariance-8./3)>1e-12)return 1;
 for(Vector2Int d:{Vector2Int(5,3),Vector2Int(3,5),Vector2Int(4,4)}){fixed::PMFS p;p.gridMetadata.dimensions=d;p.occupancy.assign(d.x*d.y,Occupancy::Free);p.sourceProbability.assign(d.x*d.y,1./(d.x*d.y));auto m=p.expectedValueSource(1);double v=p.varianceSourcePosition();double target=(d.x*d.x+d.y*d.y-2)/12.;if(std::abs(m.x-d.x/2.)>1e-7||std::abs(m.y-d.y/2.)>1e-7||std::abs(v-target)>1e-12)return 2;}
 std::cout<<"{\"status\":\"PASS\",\"native_3x5_variance\":"<<nativeVariance<<",\"correct_3x5_variance\":"<<fixedVariance<<",\"changed_loop_bounds\":2}\n";
}
