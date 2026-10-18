#include <DDA/Vectors.h>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <cmath>
#include <vector>
using Vector2=DDA::Vector2;using Vector2Int=DDA::Vector2Int;
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
int main(int argc,char**argv){if(argc!=2)return 2;std::ifstream f(argv[1]);int groups;f>>groups;std::cout<<std::setprecision(17)<<"group,mean_x,mean_y,top5_x,top5_y,variance_m2\n";
for(int group=0;group<groups;++group){PMFS p;int count;f>>p.gridMetadata.dimensions.x>>p.gridMetadata.dimensions.y>>p.gridMetadata.origin.x>>p.gridMetadata.origin.y>>p.gridMetadata.cellSize>>count;int n=p.gridMetadata.dimensions.x*p.gridMetadata.dimensions.y;p.sourceProbability.assign(n,0);p.occupancy.assign(n,Occupancy::Obstacle);
for(int k=0;k<count;++k){int x,y;double q;f>>x>>y>>q;if(!f)return 3;int i=p.gridMetadata.indexOf({x,y});if(i<0||i>=n)return 4;p.sourceProbability[i]=q;p.occupancy[i]=Occupancy::Free;}
auto mean=p.expectedValueSource(1),top=p.expectedValueSource(.05);double variance=p.varianceSourcePosition();std::cout<<group<<','<<mean.x<<','<<mean.y<<','<<top.x<<','<<top.y<<','<<variance<<'\n';}}
