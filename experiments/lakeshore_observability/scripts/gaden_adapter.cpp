#include "gaden/RunningSimulation.hpp"
#include "gaden/Preprocessing.hpp"
#include "gaden/datatypes/GasTypes.hpp"
#include <iostream>
#include <fstream>
#include <iomanip>
#include <random>
using namespace gaden;
int main(int argc,char** argv){
 if(argc<3) return 2;
 auto conf=std::make_shared<EnvironmentConfiguration>();auto& e=conf->environment;
 e.description={{80,40,31},{-100,-100,-5},{300,100,150},5};
 e.cells.assign(e.numCells(),Environment::CellState::Free);
 for(int z=0;z<31;z++)for(int y=0;y<40;y++)for(int x=0;x<80;x++){
  auto i=e.indexFrom3D({x,y,z});
  if(z==0)e.cells[i]=Environment::CellState::Obstacle;
  else if(x==0||x==79||y==0||y==39||z==30)e.cells[i]=Environment::CellState::Outlet;
 }
 conf->windSequence=Preprocessing::ParseOpenFoamVectorCloud({argv[1]},e,{});
 std::ofstream out(argv[2]);out<<std::setprecision(9);
 if(argc==3){
  out<<"x,y,z,u,v,w\n";auto& wind=conf->windSequence.GetCurrent();
  std::mt19937 rng(20261003);std::uniform_int_distribution<int> rx(1,78),ry(1,38),rz(1,29);
  for(int i=0;i<100;i++) {int x=rx(rng),y=ry(rng),z=rz(rng);auto q=e.coordsOfCellCenter({x,y,z});auto w=wind[e.indexFrom3D({x,y,z})];out<<q.x<<','<<q.y<<','<<q.z<<','<<w.x<<','<<w.y<<','<<w.z<<'\n';}
  return 0;
 }
 RunningSimulation::Parameters p;
 p.deltaTime=.1;p.windIterationDeltaTime=1;p.filamentInitialSigma=100;p.filamentGrowthGamma=10000;p.filamentNoise_std=.02;
 p.temperature=298;p.pressure=1;p.filamentPPMcenter_initial=20;p.numFilaments_sec=std::stof(argv[5]);p.expectedNumIterations=4000;
 p.source->sourcePosition={std::stof(argv[3]),std::stof(argv[4]),1};p.source->gasType=GasType::methane;
 p.saveResults=false;p.preCalculateConcentrations=false;
 RunningSimulation sim(p,conf);Simulation& base=sim;
 out<<"time,x,y,z,u,v,w,concentration\n";
 // Constant-speed closed ladder: 80+30+80+30+80+60+80=440m, period220s.
 Vector2 nodes[]={{100,-40},{100,40},{130,40},{130,-40},{160,-40},{160,40},{100,40},{100,-40}};
 double lengths[]={80,30,80,30,80,60,80}; // return path completes at original start (total440m)
 for(int t=0;t<300;t++){
  while(sim.GetCurrentTime()<120+t)sim.AdvanceTimestep();
  double d=std::fmod(2.*t,440.);int seg=0;while(d>=lengths[seg]&&seg<6){d-=lengths[seg];seg++;}
  Vector2 xy=nodes[seg]+float(d/lengths[seg])*(nodes[seg+1]-nodes[seg]);
  for(float z:{10.f,30.f,60.f,100.f}){Vector3 q{xy.x,xy.y,z};auto w=base.SampleWind(q);auto c=sim.SampleConcentration(q);out<<t<<','<<q.x<<','<<q.y<<','<<z<<','<<w.x<<','<<w.y<<','<<w.z<<','<<c<<'\n';}
 }
}
