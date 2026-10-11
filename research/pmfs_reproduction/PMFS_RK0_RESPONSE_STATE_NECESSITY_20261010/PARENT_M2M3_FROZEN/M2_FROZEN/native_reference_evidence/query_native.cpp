#include <gaden/PlaybackSimulation.hpp>
#include <gaden/core/Logging.hpp>
#include <fstream>
#include <sstream>
#include <iostream>
#include <iomanip>
#include <map>
#include <cmath>
std::vector<std::string> split(std::string x){std::vector<std::string> a;std::stringstream s(x);std::string b;while(std::getline(s,b,','))a.push_back(b);return a;}
int main(int argc,char**argv){try{
 if(argc!=5)throw std::runtime_error("ENV_DIRECTORY BANK QUERY_CSV NEW_OUTPUT");
 if(std::filesystem::exists(argv[4]))throw std::runtime_error("new output required");
 auto config=gaden::EnvironmentConfiguration::ReadDirectory(argv[1]);if(!config)throw std::runtime_error("environment missing");
 std::ifstream input(argv[3]);std::string line;std::getline(input,line);if(!line.empty()&&line.back()=='\r')line.pop_back();auto headers=split(line);
 std::ofstream out(argv[4]);out<<"query_id,frame,x,y,z,ppm_float32,physical_free,wind_x,wind_y,wind_z\n"<<std::setprecision(17);
 int last=-1;std::unique_ptr<gaden::PlaybackSimulation> simulation;
 while(std::getline(input,line)){
  if(!line.empty()&&line.back()=='\r')line.pop_back();if(line.empty())continue;auto data=split(line);if(data.size()!=headers.size())throw std::runtime_error("query shape");
  std::map<std::string,std::string> row;for(size_t i=0;i<data.size();++i)row[headers[i]]=data[i];
  int frame=std::stoi(row.at("frame"));if(frame!=last){
   gaden::PlaybackSimulation::Parameters params;params.startIteration=frame;params.resultsDirectory=argv[2];
   gaden::LoopConfig loop;loop.loop=false;simulation=std::make_unique<gaden::PlaybackSimulation>(params,config,loop);simulation->AdvanceTimestep();last=frame;
  }
  gaden::Vector3 position{std::stof(row.at("x")),std::stof(row.at("y")),std::stof(row.at("z"))};
  float value=simulation->SampleConcentration(position);if(!std::isfinite(value)||value<0)throw std::runtime_error("invalid concentration");
  auto wind=simulation->SampleWind(position);
  out<<row.at("query_id")<<","<<frame<<","<<position.x<<","<<position.y<<","<<position.z<<","<<value<<","<<(config->environment.at(position)==gaden::Environment::CellState::Free)<<","<<wind.x<<","<<wind.y<<","<<wind.z<<"\n";
 }
 return 0;
}catch(std::exception const& x){std::cerr<<x.what()<<"\n";return 1;}}
