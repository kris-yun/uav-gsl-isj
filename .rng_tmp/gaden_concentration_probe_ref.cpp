#include "gaden/RunningSimulation.hpp"
#include "gaden/datatypes/sources/PointSource.hpp"
#include <rclcpp/rclcpp.hpp>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <vector>
int main(int argc, char** argv) {
    if (argc < 7) return 2;
    rclcpp::init(argc, argv);
    std::filesystem::path envPath=argv[1], windDir=argv[2], out=argv[6];
    gaden::EnvironmentConfiguration cfg;
    if (cfg.environment.ReadFromFile(envPath) != gaden::ReadResult::OK) return 3;
    std::vector<std::filesystem::path> winds;
    for (int i=0;i<11;++i) winds.push_back(windDir / (std::string("wind_iteration_")+std::to_string(i)));
    cfg.windSequence.Initialize(winds, cfg.environment.numCells(), gaden::LoopConfig{.loop=true,.from=1,.to=10});
    auto source=std::make_shared<gaden::PointSource>();
    source->sourcePosition={std::stof(argv[3]),std::stof(argv[4]),std::stof(argv[5])}; source->gasType=gaden::GasType::methane;
    gaden::RunningSimulation::Parameters p; p.source=source; p.deltaTime=.1f; p.windIterationDeltaTime=1.f; p.temperature=298.f; p.pressure=1.f;
    p.filamentPPMcenter_initial=10.f; p.filamentInitialSigma=10.f; p.filamentGrowthGamma=15.f; p.filamentNoise_std=.01f; p.numFilaments_sec=7.f; p.expectedNumIterations=30; p.windLoop=gaden::LoopConfig{.loop=true,.from=1,.to=10}; p.saveResults=false; p.preCalculateConcentrations=false;
    gaden::RunningSimulation sim(p,std::make_shared<gaden::EnvironmentConfiguration>(cfg)); std::ofstream f(out); f<<std::setprecision(9); const auto& d=cfg.environment.description;
    for (int t=0;t<30;++t) { sim.AdvanceTimestep(); for (int q=0;q<100;++q) { int x=(q*17+3)%d.dimensions.x, y=(q*29+7)%d.dimensions.y, z=(q*13+2)%d.dimensions.z; gaden::Vector3 pt=d.minCoord+gaden::Vector3{(x+.5f)*d.cellSize,(y+.5f)*d.cellSize,(z+.5f)*d.cellSize}; if(q<10) pt=source->sourcePosition+gaden::Vector3{.03f*q,0,0}; f<<t<<","<<q<<","<<sim.SampleConcentration(pt)<<"\n"; }}
    rclcpp::shutdown();
}
