/*--------------------------------------------------------------------------------
 * Pkg for playing the simulation results of the "filament_simulator" pkg.
 * It allows to run on real time, and provide services to simulated sensors (gas, wind)
 * It supports loading several simulations at a time, which allows multiple gas sources and gas types
 * It also generates a point cloud representing the gas concentration [ppm] on the 3D environment
 --------------------------------------------------------------------------------*/
#define GADEN_LOGGER_ID "GadenPlayer"
#include <gaden_common/Utils.hpp>

#include "gaden/core/Assertions.hpp"
#include "gaden/internal/MathUtils.hpp"
#include "gaden/internal/PathUtils.hpp"
#include "gaden/internal/Time.hpp"
#include "simulation_player.h"
#include <gaden_common/Visualization.hpp>
#include <cmath>
#include <cstdlib>

namespace
{
    constexpr float kMaxDecodedWindComponent = 1.0e4f;

    bool isValidDecodedWind(const gaden::Vector3& wind)
    {
        return std::isfinite(wind.x) && std::isfinite(wind.y) && std::isfinite(wind.z) &&
               std::abs(wind.x) <= kMaxDecodedWindComponent &&
               std::abs(wind.y) <= kMaxDecodedWindComponent &&
               std::abs(wind.z) <= kMaxDecodedWindComponent;
    }
}

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);

    std::shared_ptr<Player> player = std::make_shared<Player>();

    player->run();

    return 0;
}

Player::Player()
    : rclcpp::Node("gaden_player")
{}

//--------------- SERVICES CALLBACKS----------------------//

gaden_msgs::msg::GasInCell Player::GetAllGasesSingleCell(float x, float y, float z, const std::vector<gaden::GasType>& gas_types)
{
    const gaden::Vector3 point(x, y, z);
    const auto indices = environmentConfig->environment.coordsToIndices(point);
    GADEN_INFO("Service gas query point=({},{},{}) indices=({},{},{}) min=({},{},{}) cell_size={} in_bounds={}",
               point.x, point.y, point.z,
               indices.x, indices.y, indices.z,
               environmentConfig->environment.description.minCoord.x,
               environmentConfig->environment.description.minCoord.y,
               environmentConfig->environment.description.minCoord.z,
               environmentConfig->environment.description.cellSize,
               environmentConfig->environment.IsInBounds(point));
    std::map<gaden::GasType, float> concentrations = Scene->SampleConcentrations(point);

    // Configure Response
    gaden_msgs::msg::GasInCell response;
    for (int i = 0; i < gas_types.size(); i++)
    {
        float conc = concentrations.at(gas_types.at(i));
        response.concentration.push_back(conc);
    }

    return response;
}

bool Player::GetGasValue_srv(gaden_msgs::srv::GasPosition::Request::SharedPtr req, gaden_msgs::srv::GasPosition::Response::SharedPtr res)
{
    std::vector<gaden::GasType> gasTypes = Scene->GetGasTypes();
    std::vector<std::string> gasNames;

    for (int i = 0; i < gasTypes.size(); i++)
        gasNames.push_back(gaden::to_string(gasTypes.at(i)));

    res->gas_type = gasNames;

    for (int i = 0; i < req->x.size(); i++)
        res->positions.push_back(GetAllGasesSingleCell(req->x[i], req->y[i], req->z[i], gasTypes));

    return true;
}

bool Player::GetWindValue_srv(gaden_msgs::srv::WindPosition::Request::SharedPtr req, gaden_msgs::srv::WindPosition::Response::SharedPtr res)
{
    // Since the wind fields are identical among different instances, return just the information from instance[0]
    for (int i = 0; i < req->x.size(); i++)
    {
        gaden::Vector3 windVec = Scene->SampleWind(gaden::Vector3{req->x[i], req->y[i], req->z[i]});
        if (!isValidDecodedWind(windVec))
        {
            GADEN_ERROR("Rejected invalid decoded wind vector ({}, {}, {})", windVec.x, windVec.y, windVec.z);
            return false;
        }
        res->u.push_back(windVec.x);
        res->v.push_back(windVec.y);
        res->w.push_back(windVec.z);
    }
    return true;
}

bool Player::SetIteration_srv(gaden_msgs::srv::SetIteration::Request::SharedPtr req, gaden_msgs::srv::SetIteration::Response::SharedPtr res)
{
    bool loaded = true;
    for (const auto& simulation : Scene->GetSimulations())
    {
        auto playback = std::dynamic_pointer_cast<gaden::PlaybackSimulation>(simulation);
        if (!playback || !playback->LoadIteration(static_cast<size_t>(req->iteration)))
            loaded = false;
    }
    res->success = loaded;
    res->loaded_iteration = loaded ? req->iteration : -1;
    res->message = loaded ? "loaded recorded iteration" : "requested iteration unavailable";
    return true;
}

bool Player::FrameQuery_srv(gaden_msgs::srv::FrameQuery::Request::SharedPtr req, gaden_msgs::srv::FrameQuery::Response::SharedPtr res)
{
    bool loaded = true;
    for (const auto& simulation : Scene->GetSimulations()) {
        auto playback = std::dynamic_pointer_cast<gaden::PlaybackSimulation>(simulation);
        if (!playback || !playback->LoadIteration(static_cast<size_t>(req->iteration))) loaded = false;
    }
    const gaden::Vector3 point(req->x, req->y, req->z);
    const auto& environment = environmentConfig->environment;
    const auto indices = environment.coordsToIndices(point);
    if (!loaded || !environment.IsInBounds(indices)) {
        res->valid = false;
        if (!loaded) {
            res->error_message = "requested iteration unavailable";
        } else {
            const auto& description = environment.description;
            res->error_message =
                "query point out of bounds point=(" +
                std::to_string(point.x) + "," +
                std::to_string(point.y) + "," +
                std::to_string(point.z) + ") indices=(" +
                std::to_string(indices.x) + "," +
                std::to_string(indices.y) + "," +
                std::to_string(indices.z) + ") dimensions=(" +
                std::to_string(description.dimensions.x) + "," +
                std::to_string(description.dimensions.y) + "," +
                std::to_string(description.dimensions.z) + ") min=(" +
                std::to_string(description.minCoord.x) + "," +
                std::to_string(description.minCoord.y) + "," +
                std::to_string(description.minCoord.z) + ") cell_size=" +
                std::to_string(description.cellSize);
        }
        return true;
    }
    try {
        const auto gases = Scene->SampleConcentrations(point);
        float concentration = 0.0f;
        for (const auto& value : gases) concentration += value.second;
        const auto wind = Scene->SampleWind(point);
        if (!isValidDecodedWind(wind)) {
            res->valid = false;
            res->error_message = "invalid decoded wind vector";
            GADEN_ERROR("Rejected invalid decoded wind vector ({}, {}, {}) at iteration {}", wind.x, wind.y, wind.z, req->iteration);
            return true;
        }
        res->valid = true; res->concentration = concentration;
        res->wind_u = wind.x; res->wind_v = wind.y; res->wind_w = wind.z;
        res->error_message.clear();
    } catch (const std::exception& error) { res->valid = false; res->error_message = error.what(); }
    return true;
}

//------------------------ MAIN --------------------------//
void Player::run()
{
    // if there is a gaden project directory, we will just parse those files instead of reading everything from ROS params
    std::filesystem::path projectPath = declare_parameter<std::string>("projectPath", "");
    GadenUtils::LoadProject(projectPath, gadenProject);

    environmentConfig = std::make_shared<gaden::EnvironmentConfiguration>();

    // Read Node Parameters
    if (gadenProject)
        loadGadenProject();
    else
        loadNodeParameters();

    // Init variables
    initSimulations();
    const auto& environment = environmentConfig->environment.description;
    GADEN_INFO("Loaded environment: min={} max={} dimensions={} cell_size={}",
               environment.minCoord,
               environment.maxCoord,
               environment.dimensions,
               environment.cellSize);
    rclcpp::Time time_last_loaded_file = now();
    srand(time(NULL)); // initialize random seed

    // Services offered
    auto serviceGas = create_service<gaden_msgs::srv::GasPosition>(
        "odor_value", std::bind(&Player::GetGasValue_srv, this, std::placeholders::_1, std::placeholders::_2));
    auto serviceWind = create_service<gaden_msgs::srv::WindPosition>(
        "wind_value", std::bind(&Player::GetWindValue_srv, this, std::placeholders::_1, std::placeholders::_2));
    auto serviceIteration = create_service<gaden_msgs::srv::SetIteration>(
        "set_iteration", std::bind(&Player::SetIteration_srv, this, std::placeholders::_1, std::placeholders::_2));
    auto serviceFrameQuery = create_service<gaden_msgs::srv::FrameQuery>(
        "frame_query", std::bind(&Player::FrameQuery_srv, this, std::placeholders::_1, std::placeholders::_2));

    // Loop
    rclcpp::Rate r(100); // Set max rate at 100Hz (for handling services - Top Speed!!)
    auto shared_this = shared_from_this();

    // playback frequency
    float player_freq = declare_parameter<float>("player_freq", 1); // Hz
    bool manual_iteration_mode = declare_parameter<bool>("manual_iteration_mode", false);
    GADEN_INFO("player_freq {:.2f} Hz", player_freq);
    gaden::Utils::Time::Countdown countdown(1.f / player_freq);

    // load the first timestep immediately
    Scene->AdvanceTimestep();

    while (rclcpp::ok())
    {
        if (!manual_iteration_mode && countdown.isDone())
        {
            // Read Gas and Wind data from log_files
            Scene->AdvanceTimestep();

            displayCurrentGasDistribution(); // Rviz visualization

            // Looping?
            time_last_loaded_file = now();
            countdown.Restart();
        }

        // Attend service request at max rate!
        // This allows sensors to have higher sampling rates than the simulation update
        rclcpp::spin_some(shared_this);
        r.sleep();
    }
}

// Load Node parameters
void Player::loadNodeParameters()
{
    GadenUtils::OldProjectWarning();

    // Number of simulators to load (For simulating multiple gases and multiple sources)
    int num_simulators = declare_parameter<int>("num_simulators", 1);

    GADEN_INFO("num_simulators: {}", num_simulators);

    // FilePath for simulated data
    playbackMetadata.params.resize(num_simulators);
    GADEN_VERIFY(num_simulators >= 1, "Must have at least one simulation to play back!");
    int initial_iteration = declare_parameter<int>("initial_iteration", 1);

    for (int i = 0; i < num_simulators; i++)
    {
        // Get location of simulation data for instance (i)
        std::string paramName = fmt::format("simulation_data_{}", i);
        playbackMetadata.params[i].resultsDirectory = declare_parameter<std::string>(paramName.c_str(), "");
        playbackMetadata.params[i].startIteration = initial_iteration;
        GADEN_INFO("simulation_data_{}: {}", i, playbackMetadata.params[i].resultsDirectory);
    }

    playbackMetadata.gasDisplayColors.resize(num_simulators);
    for (int i = 0; i < num_simulators; i++)
    {
        // Get location of simulation data for instance (i)
        std::string paramName = fmt::format("gas_display_color_{}", i);
        auto colorAsVec = declare_parameter<std::vector<float>>(paramName.c_str(), {0, 1, 0});
        playbackMetadata.gasDisplayColors.at(i).r = colorAsVec.at(0);
        playbackMetadata.gasDisplayColors.at(i).g = colorAsVec.at(1);
        playbackMetadata.gasDisplayColors.at(i).b = colorAsVec.at(2);
        playbackMetadata.gasDisplayColors.at(i).a = 1;
    }

    // Initial iteration
    std::filesystem::path occupancyFile = declare_parameter<std::string>("occupancyFile", "");
    GADEN_CHECK_RESULT(environmentConfig->environment.ReadFromFile(occupancyFile));

    // Loop
    playbackMetadata.loop.loop = declare_parameter<bool>("allow_looping", false);
    playbackMetadata.loop.from = declare_parameter<int>("loop_from_iteration", 1);
    playbackMetadata.loop.to = declare_parameter<int>("loop_to_iteration", 1);
}

void Player::loadGadenProject()
{
    std::string playbackID = declare_parameter<std::string>("playbackID", "");
    try
    {
        playbackMetadata = gadenProject->GetPlaybackScene(playbackID);
        playbackMetadata.gasDisplayColors.resize(playbackMetadata.gasDisplayColors.size());

        std::filesystem::path occupancyFile = gadenProject->rootDirectory / "OccupancyGrid3D.csv";
        GADEN_CHECK_RESULT(environmentConfig->environment.ReadFromFile(occupancyFile));
    }
    catch (std::exception const& e)
    {
        GADEN_ERROR("Could not find a playback configuration with the name '{}'", playbackID);
        GADEN_TERMINATE;
    }
}

void Player::initSimulations()
{
    // Find the wind files
    // We only need to find them once, since the wind is assumed to be identical for all simulation instances
    std::filesystem::path pathOldProjects = playbackMetadata.params.at(0).resultsDirectory / "wind";                                           // in projects generated pre-3.0 the wind is in a subdirectory of gas_simulations
    std::filesystem::path pathNewProjects = playbackMetadata.params.at(0).resultsDirectory.parent_path().parent_path().parent_path() / "wind"; // in projects generated post-3.0 the wind is in a subdirectory of the environment configuration, above gas_simulations
    std::vector<std::filesystem::path> windFiles;
    GADEN_INFO("Looking for wind files in:\n"
               "\t-'{}'\n"
               "\t-'{}'",
               pathNewProjects, pathOldProjects);

    if (std::filesystem::exists(pathNewProjects))
    {
        GADEN_INFO("Found wind files at '{}'", pathNewProjects);
        windFiles = gaden::paths::GetAllFilesInDirectory(pathNewProjects);
    }
    else if (std::filesystem::exists(pathOldProjects))
    {
        GADEN_INFO("Found wind files at '{}'", pathOldProjects);
        windFiles = gaden::paths::GetAllFilesInDirectory(pathOldProjects);
    }
    else
    {
        GADEN_ERROR("Could not find wind files!");
        GADEN_TERMINATE;
    }

    if (std::getenv("GADEN_WIND_CONTRACT_LOG_ORDER") != nullptr)
    {
        for (size_t i = 0; i < windFiles.size(); ++i)
            GADEN_INFO("Wind sequence input order[{}] = '{}'", i, windFiles.at(i).filename());
    }

    environmentConfig->windSequence.Initialize(windFiles, environmentConfig->environment.numCells(), {});
    Scene.emplace(playbackMetadata, environmentConfig);
}

// Display in RVIZ the gas distribution
void Player::displayCurrentGasDistribution()
{
    if (!sourceMarkerPub)
    {
        sourceMarkerPub = create_publisher<visualization_msgs::msg::MarkerArray>("source_visualization", 1);
        gasMarkerPub = create_publisher<visualization_msgs::msg::Marker>("Gas_Distribution", 1);
    }

    visualization_msgs::msg::Marker gasMarker;
    {
        gasMarker.header.frame_id = "map";
        gasMarker.header.stamp = now();
        gasMarker.ns = "Gas_Dispersion";
        gasMarker.action = visualization_msgs::msg::Marker::ADD;
        gasMarker.type = visualization_msgs::msg::Marker::POINTS; // Marker type
        gasMarker.id = 0;                                         // One marker with multiple points.
        gasMarker.scale.x = 0.035;
        gasMarker.scale.y = 0.035;
        gasMarker.scale.z = 0.035;
    }

    visualization_msgs::msg::MarkerArray sourceMarkerArray;

    const auto& simulations = Scene->GetSimulations();
    for (int i = 0; i < simulations.size(); i++)
    {
        gaden::PlaybackSimulation::Mode mode = As<gaden::PlaybackSimulation>(simulations[i])->GetMode();
        size_t count = 0;

        // fill the gas marker, depending on whether it's a filament list simulation or a concentration map simulation
        if (mode == gaden::PlaybackSimulation::Mode::Filaments)
        {
            auto const& filaments = simulations[i]->GetFilaments();
            count = FillMarkerArray(gasMarker.points, filaments);
        }
        else if (mode == gaden::PlaybackSimulation::Mode::Concentration)
        {
            count = FillMarkerArrayConcentrations(gasMarker.points, simulations[i]);
        }

        // add the gas colors
        for (size_t pointIdx = 0; pointIdx < count; pointIdx++)
            gasMarker.colors.push_back(GadenUtils::toRosColor(Scene->GetColors().at(i)));

        // source marker
        visualization_msgs::msg::Marker sourceMarker = GadenUtils::MarkerSourcePosition(this, *simulations[i]);
        sourceMarker.id = i;
        sourceMarkerArray.markers.push_back(sourceMarker);
    }

    // Display particles
    gasMarkerPub->publish(gasMarker);
    sourceMarkerPub->publish(sourceMarkerArray);
}

//==================================== SIM_OBJ ==============================//

size_t Player::FillMarkerArray(std::vector<geometry_msgs::msg::Point>& points, std::vector<gaden::Filament> const& filaments)
{
    size_t count = 0;
    for (auto it = filaments.begin(); it != filaments.end(); it++)
    {
        const gaden::Filament& filament = *it;
        for (int i = 0; i < 3; i++)
        {
            geometry_msgs::msg::Point p; // Location of point
            float distance = filament.sigma / 100;
            p.x = (filament.position.x) + gaden::uniformRandom(-distance, distance);
            p.y = (filament.position.y) + gaden::uniformRandom(-distance, distance);
            p.z = (filament.position.z) + gaden::uniformRandom(-distance, distance);

            // Add particle marker
            points.push_back(p);
            count++;
        }
    }
    return count;
}

size_t Player::FillMarkerArrayConcentrations(std::vector<geometry_msgs::msg::Point>& points, const std::shared_ptr<gaden::Simulation> sim)
{
    size_t count = 0;
    auto const& env = sim->config->environment;

#pragma omp parallel for
    for (size_t i = 0; i < env.numCells(); i++)
    {
        gaden::Vector3 point = env.coordsOfCellCenter(env.indicesFrom1D(i));
        float conc = sim->SampleConcentration(point);
        for (size_t n = 0; n < std::round(conc * 0.1); n++)
        {
            geometry_msgs::msg::Point p; // Location of point
            p.x = point.x + gaden::uniformRandom(-env.description.cellSize, env.description.cellSize);
            p.y = point.y + gaden::uniformRandom(-env.description.cellSize, env.description.cellSize);
            p.z = point.z + gaden::uniformRandom(-env.description.cellSize, env.description.cellSize);

#pragma omp critical
            {
                points.push_back(p);
                count++;
            }
        }
    }
    return count;
}
