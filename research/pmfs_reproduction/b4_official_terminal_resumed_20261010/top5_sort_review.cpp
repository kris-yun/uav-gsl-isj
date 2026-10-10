// Arithmetic-only extraction of the pinned ExpectedValue sorting/selection rule.
// No ROS, random sampling, propagation model, navigation, or source update.
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
struct Cell { int index; double p; float x,y; };
int main(int argc,char**argv) {
 if(argc!=2)return 2;
 std::ifstream f(argv[1]);std::string line;std::getline(f,line);
 std::vector<Cell> data;
 while(std::getline(f,line)) {
  std::replace(line.begin(),line.end(),',',' ');std::istringstream in(line);
  int index,free;double x,y,p;
  if(!(in>>index>>free>>x>>y>>p))return 3;
  if(free==1)data.push_back({index,p,(float)x,(float)y});
 }
 std::sort(data.begin(),data.end(),[](const Cell&a,const Cell&b){return a.p>b.p;});
 double x=0,y=0,sum=0;int count=0;
 for(int i=0;i<data.size()*.05;i++){x+=data[i].p*data[i].x;y+=data[i].p*data[i].y;sum+=data[i].p;count++;}
 float sx=x/sum,sy=y/sum;
 std::cout<<std::setprecision(17)<<"{\"free_cells\":"<<data.size()<<",\"selected_count\":"<<count<<",\"selected_mass\":"<<sum<<",\"xy\":["<<sx<<","<<sy<<"],\"error_GT_double_m\":"<<std::sqrt(std::pow(-3.2-sx,2)+std::pow(-3.3-sy,2))<<",\"error_GT_float_m\":"<<std::sqrt(std::pow((double)(float)-3.2-sx,2)+std::pow((double)(float)-3.3-sy,2))<<",\"selected_cell_indices\":[";
 for(int i=0;i<count;i++){if(i)std::cout<<",";std::cout<<data[i].index;}
 std::cout<<"]}"<<std::endl;
}
