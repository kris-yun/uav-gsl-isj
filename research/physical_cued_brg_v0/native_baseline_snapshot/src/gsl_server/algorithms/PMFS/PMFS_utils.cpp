#include <stdexcept>
#include <iomanip>
#include <cstdlib>
#include "gsl_server/algorithms/Common/Grid2D.hpp"
#include "gsl_server/algorithms/Common/Utils/Math.hpp"
#include <fstream>
#include <gsl_server/algorithms/PMFS/PMFS.hpp>

namespace GSL
{
    void PMFS::OnCompleteNavigation(GSLResult result, State* previousState)
    {
        if (result == GSLResult::Success)
            stateMachine.forceSetState(stopAndMeasureState.get());
        else
        {
            functionQueue.submit([&]()
                                 {
                                     movingState->chooseGoalAndMove();
                                 });
        }
    }

    GSLResult PMFS::checkSourceFound()
    {
        if (stateMachine.getCurrentState() == waitForMapState.get())
            return GSLResult::Running;

        rclcpp::Duration time_spent = node->now() - startTime;
        if (time_spent.seconds() > resultLogging.maxSearchTime)
        {
            saveResultsToFile(GSLResult::Failure);
            return GSLResult::Failure;
        }

        if (resultLogging.navigationTime == -1)
        {
            if (sqrt(pow(currentRobotPose.pose.pose.position.x - resultLogging.sourcePositionGT.x, 2) +
                     pow(currentRobotPose.pose.pose.position.y - resultLogging.sourcePositionGT.y, 2)) < 0.5)
            {
                resultLogging.navigationTime = time_spent.seconds();
            }
        }

        double variance = Utils::Variance(Grid2D<double>(sourceProbability, occupancy, gridMetadata));
        GSL_INFO("Variance: {:.2f}", variance);

        if (variance < settings.declaration.threshold)
        {
            saveResultsToFile(GSLResult::Success);
            return GSLResult::Success;
        }

        return GSLResult::Running;
    }

    void PMFS::saveResultsToFile(GSLResult result)
    {
        auditBelief(result == GSLResult::Success ? "declared_success" : "terminal_failure");
        // 1. Search time.
        rclcpp::Duration time_spent = node->now() - startTime;
        double search_t = time_spent.seconds();

        Vector2 sourceLocationAll = Utils::ExpectedValue(Grid2D<double>(sourceProbability, occupancy, gridMetadata), 1);
        Vector2 sourceLocation = Utils::ExpectedValue(Grid2D<double>(sourceProbability, occupancy, gridMetadata), 0.05);

        double error = sqrt(pow(resultLogging.sourcePositionGT.x - sourceLocation.x, 2) + pow(resultLogging.sourcePositionGT.y - sourceLocation.y, 2));
        double errorAll = sqrt(pow(resultLogging.sourcePositionGT.x - sourceLocationAll.x, 2) + pow(resultLogging.sourcePositionGT.y - sourceLocationAll.y, 2));

        std::string resultString = fmt::format("RESULT IS: Success={}, Search_t={:.2f}, Error={:.2f}", (int)result, search_t, error);
        GSL_INFO_COLOR(fmt::terminal_color::blue, "{}", resultString);

        // Save to file
        if (resultLogging.resultsFile != "")
        {
            std::ofstream file;
            file.open(resultLogging.resultsFile, std::ios_base::app);
            if (result != GSLResult::Success)
                file << "FAILED ";

            file << resultLogging.navigationTime << " " << search_t << " " << errorAll << " " << error << " " << iterationsCounter << " "
                 << Utils::Variance(Grid2D<double>(sourceProbability, occupancy, gridMetadata)) << "\n";
            file.close();
        }
        else
            GSL_WARN("No file provided for logging result. Skipping it.");

        if (resultLogging.navigationPathFile != "")
        {
            std::ofstream file;
            file.open(resultLogging.navigationPathFile, std::ios_base::app);
            file << "------------------------\n";
            for (PoseWithCovarianceStamped p : resultLogging.robotPosesVector)
                file << p.pose.pose.position.x << ", " << p.pose.pose.position.y << "\n";
            file.close();
        }
        else
            GSL_WARN("No file provided for logging path. Skipping it.");
    }

} // namespace GSL
// Optional output only: never changes source, variance, RNG, planner, or stopping.
namespace GSL {
void PMFS::auditBelief(const char* stage) {
    const char* path = std::getenv("BRG_BELIEF_AUDIT_JSONL");
    if (!path || !*path) return;
    std::ofstream f(path, std::ios::app);
    if (!f) throw std::runtime_error("BRG belief audit cannot open");
    Vector2 estimate = Utils::ExpectedValue(Grid2D<double>(sourceProbability, occupancy, gridMetadata), 0.05);
    f << std::setprecision(17) << "{\"stage\":\"" << stage << "\",\"time_s\":" << node->now().seconds()
      << ",\"search_time_s\":" << (node->now()-startTime).seconds()
      << ",\"iterations_counter\":" << iterationsCounter
      << ",\"brg_event_count\":" << brgEvent << ",\"width\":" << gridMetadata.dimensions.x
      << ",\"height\":" << gridMetadata.dimensions.y << ",\"resolution\":" << gridMetadata.cellSize
      << ",\"origin_x\":" << gridMetadata.origin.x << ",\"origin_y\":" << gridMetadata.origin.y
      << ",\"estimate_xy\":[" << estimate.x << ',' << estimate.y << "],\"free_cells\":[";
    bool first=true;
    for(size_t i=0;i<occupancy.size();++i) if(occupancy[i]==Occupancy::Free){if(!first)f<<',';f<<i;first=false;}
    f << "],\"source_map\":[";
    for(size_t i=0;i<sourceProbability.size();++i){if(i)f<<',';f<<sourceProbability[i];}
    f << "],\"variance_map\":[";
    for(size_t i=0;i<simulations.varianceOfHitProb.size();++i){if(i)f<<',';f<<simulations.varianceOfHitProb[i];}
    f << "]}\n";
    f.flush(); if(!f)throw std::runtime_error("BRG belief audit write failed");
}
}
