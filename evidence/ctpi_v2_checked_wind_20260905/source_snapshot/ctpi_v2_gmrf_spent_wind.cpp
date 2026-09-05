// Spent R4 WIND ONLY replay through installed GMRF core; no gas/source access.
#include <array>
#include <cstdint>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <opencv2/imgcodecs.hpp>
#include <yaml-cpp/yaml.h>
#include "../ros2_package/src/gsl_server/algorithms/PMFS/CTPIGmrfWindV2.hpp"
#ifdef CTPI_CHECKED_WIND
#include "../ros2_package/src/gsl_server/algorithms/PMFS/CTPIGmrfCheckedWindV2.hpp"
#endif

std::vector<std::string> split(const std::string& line)
{
    std::istringstream s(line); std::string item; std::vector<std::string> out;
    while(std::getline(s,item,',')) out.push_back(item);
    return out;
}

int main(int argc,char**argv)
{
    try
    {
        if(argc!=5) throw std::invalid_argument("map_yaml wind_csv parameters_json NEW_output_directory");
        const std::filesystem::path yamlPath=argv[1], out=argv[4];
        if(std::filesystem::exists(out)) throw std::invalid_argument("output already exists");
        const auto yaml=YAML::LoadFile(yamlPath.string());
        if(yaml["negate"].as<int>()!=0 || yaml["origin"][2].as<double>()!=0)
            throw std::invalid_argument("unsupported map convention");
        auto imagePath=std::filesystem::path(yaml["image"].as<std::string>());
        if(imagePath.is_relative()) imagePath=yamlPath.parent_path()/imagePath;
        const auto image=cv::imread(imagePath.string(),cv::IMREAD_GRAYSCALE);
        if(image.empty()) throw std::invalid_argument("map image missing");
        gmrfw::TOccupancyMap occupancy;
        occupancy.width=image.cols; occupancy.height=image.rows;
        occupancy.resolution=yaml["resolution"].as<double>();
        occupancy.origin_x=yaml["origin"][0].as<double>();
        occupancy.origin_y=yaml["origin"][1].as<double>();
        occupancy.data.resize(occupancy.width*occupancy.height);
        const double freeThreshold=1-yaml["free_thresh"].as<double>();
        const double occupiedThreshold=1-yaml["occupied_thresh"].as<double>();
        for(int y=0;y<image.rows;++y) for(int x=0;x<image.cols;++x)
        {
            const double value=image.at<uint8_t>(y,x)/255.;
            occupancy.data[x+(image.rows-y-1)*image.cols]=value>freeThreshold?0:(value<occupiedThreshold?100:-1);
        }
        // Explicit configuration, never selected from forecast errors.
        const auto config=YAML::LoadFile(argv[3])["parameters"];
        gmrfw::CGMRF_map::Parameters parameters;
        parameters.cell_size=config["cell_size"].as<double>();
        parameters.lambdaPrior_advection=config["advection"].as<double>();
        parameters.lambdaPrior_mass_conservation=config["mass_conservation"].as<double>();
        parameters.lambdaPrior_diffusion=config["diffusion"].as<double>();
        parameters.lambdaPrior_obstacles=config["obstacles"].as<double>();
        if(config["var_speed"].as<double>()!=.001 || config["var_direction"].as<double>()!=.0001)
            throw std::invalid_argument("adapter variance mismatch");
#ifdef CTPI_CHECKED_WIND
        GSL::ctpi_v2::GmrfCheckedWind wind(occupancy,parameters,YAML::LoadFile(argv[3])["latest_cell"].as<bool>());
#else
        GSL::ctpi_v2::GmrfWind wind(occupancy,parameters);
#endif
        const auto dims=wind.geometry().map_size();
        const int cells=dims.x()*dims.y();
        std::ifstream input(argv[2]); std::string line;
        if(!input || !std::getline(input,line)) throw std::invalid_argument("wind CSV missing");
        auto names=split(line); std::map<std::string,size_t> columns;
        for(size_t i=0;i<names.size();++i) columns[names[i]]=i;
        for(auto name:{"t_sim_s","step","iteration","x","y","wind_u","wind_v"})
            if(!columns.count(name)) throw std::invalid_argument("wind column missing");
        std::filesystem::create_directory(out);
        std::ofstream predictions(out/"predictions.csv"), geometry(out/"geometry.csv");
        std::ofstream fields(out/"wind_fields_f64_native.bin",std::ios::binary);
#ifdef CTPI_CHECKED_WIND
        std::ofstream solves(out/"solver_audit.csv");
        solves<<std::setprecision(17)<<"step,t_sim_s,iterations,active_observations,relative_change,backward_residual,update_mismatch\n";
#endif
        predictions<<std::setprecision(17)<<"step,t_sim_s,input_through_s,x,y,u,v,pred_u,pred_v,persist_u,persist_v,same_printed_pose,replay_seam\n";
        geometry<<std::setprecision(17)<<"index,x,y,free\n";
        for(int i=0;i<cells;++i)
        {
            double x,y; wind.geometry().id2xy_public(i,x,y);
            geometry<<i<<','<<x<<','<<y<<','<<wind.geometry().is_cell_free(i)<<'\n';
        }
        size_t steps=0; double pu=0,pv=0,px=0,py=0; long previousIteration=-1;
        while(std::getline(input,line))
        {
            if(line.empty()) continue;
            auto row=split(line);
            auto get=[&](const char* key){return std::stod(row.at(columns.at(key)));};
            const double stamp=get("t_sim_s");
            if(stamp>240.+1e-9) break;
            if(get("step")!=double(steps+1)) throw std::invalid_argument("wind step gap");
            const double x=get("x"),y=get("y"),u=get("wind_u"),v=get("wind_v");
            const long iteration=static_cast<long>(get("iteration"));
            if(steps)
            {
                // Prediction before this row's wind is passed into the producer.
                const auto pred=wind.predictAt(stamp,x,y);
                predictions<<steps+1<<','<<stamp<<','<<wind.stamp()<<','<<x<<','<<y<<','<<u<<','<<v<<','
                    <<pred.x<<','<<pred.y<<','<<pu<<','<<pv<<','<<(x==px&&y==py)<<','<<(iteration<previousIteration)<<'\n';
            }
            wind.assimilate(stamp,x,y,u,v);
#ifdef CTPI_CHECKED_WIND
            const auto& audit=wind.solveAudit();
            solves<<steps+1<<','<<stamp<<','<<audit.iterations<<','<<audit.observations<<','
                  <<audit.relativeChange<<','<<audit.backwardResidual<<','<<audit.updateMismatch<<'\n';
#endif
            // For downstream chronological transport: post-step snapshot i may
            // first predict step i+1. Layout [step][cell][u,v], native IEEE f64.
            for(int i=0;i<cells;++i)
            {
                const auto w=wind.fieldAt(i); const std::array<double,2> uv{w.x,w.y};
                fields.write(reinterpret_cast<const char*>(uv.data()),sizeof(uv));
            }
            pu=u;pv=v;px=x;py=y;previousIteration=iteration;++steps;
            if(steps%100==0) std::cout<<"WIND_STEP "<<steps<<std::endl;
        }
        if(steps!=1200) throw std::runtime_error("240 s wind record incomplete");
        predictions.close(); geometry.close(); fields.close();
        if(!predictions||!geometry||!fields) throw std::runtime_error("output write failed");
#ifdef CTPI_CHECKED_WIND
        solves.close();
        if(!solves) throw std::runtime_error("solver audit write failed");
#endif
        std::ofstream done(out/"COMPLETED.json");
        done<<"{\"status\":\"SPENT_WIND_CONDITIONAL_MEAN_ONLY\",\"steps\":"<<steps
            <<",\"map_width\":"<<dims.x()<<",\"map_height\":"<<dims.y()
            <<",\"cell_size\":"<<parameters.cell_size<<",\"native_field_bytes\":"<<steps*cells*2*sizeof(double)
            <<",\"first_forecast_s\":0.4,\"last_forecast_s\":240.0}\n";
        std::cout<<"SPENT_WIND_COMPLETE "<<steps<<std::endl;
    }
    catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 2;}
}
