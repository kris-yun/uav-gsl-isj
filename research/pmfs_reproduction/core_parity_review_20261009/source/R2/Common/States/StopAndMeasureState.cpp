#include <gsl_server/algorithms/Common/Algorithm.hpp>
#include <gsl_server/algorithms/Common/States/StopAndMeasureState.hpp>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <algorithm>

namespace GSL
{
    StopAndMeasureState::StopAndMeasureState(Algorithm* _algorithm)
        : State(_algorithm)
    {
        measure_time = algorithm->getParam<double>("stop_and_measure_time", 2.0);
        fixed_settle_samples_ = algorithm->getParam<int>("measurement_settle_samples", -1);
        fixed_measure_samples_ = algorithm->getParam<int>("measurement_block_samples", -1);
        if (fixed_settle_samples_ < 0 || fixed_measure_samples_ <= 0) {
            fixed_settle_samples_ = -1;
            fixed_measure_samples_ = -1;
        }
        initMeasurementTrace();
    }

    void StopAndMeasureState::OnEnterState(State* previous)
    {
        GSL_TRACE("Entering StopAndMeasure");
        time_stopped = algorithm->node->now();
        measure_window_start_ = time_stopped;
        gas_v.clear();
        gas_time_v.clear();
        windSpeed_v.clear();
        windDirection_v.clear();
        fixed_settle_gas_seen_ = 0;
        fixed_settle_wind_seen_ = 0;
        fixed_block_completed_ = false;
    }

    void StopAndMeasureState::OnUpdate()
    {
        double timeSoFar = (algorithm->node->now() - time_stopped).seconds();
        const bool fixed_ready = fixed_measure_samples_ > 0 &&
            static_cast<int>(gas_v.size()) == fixed_measure_samples_ &&
            static_cast<int>(windSpeed_v.size()) == fixed_measure_samples_;
        if (!fixed_block_completed_ && ((fixed_measure_samples_ > 0 && fixed_ready) ||
            (fixed_measure_samples_ <= 0 && timeSoFar >= measure_time)))
        {
            fixed_block_completed_ = true;
            GSL_INFO("{} gas measurements, {} wind measurements over {:.2f} seconds", gas_v.size(), windSpeed_v.size(), timeSoFar);
            if (gas_v.size() == 0 || windDirection_v.size() == 0)
            {
                GSL_WARN("Resetting stop and measure, no readings exist!");
                algorithm->stateMachine.forceResetState(this);
                return;
            }

            double concentration = average_concentration();
            double windSpeed = average_windSpeed();
            double windDirection = average_windDirection();

            GSL_INFO("avg_gas={:.2};  avg_windSpeed={:.2};  avg_wind_dir={:.2}", concentration, windSpeed, windDirection);
            writeMeasurementTrace(concentration, windSpeed, windDirection);
            algorithm->processGasAndWindMeasurements(concentration, windSpeed, windDirection);
        }
    }

    void StopAndMeasureState::addGasReading(double concentration)
    {
        if (algorithm->stateMachine.getCurrentState() != this)
            return;
        if (fixed_measure_samples_ > 0) {
            if (fixed_settle_gas_seen_ < fixed_settle_samples_) {
                ++fixed_settle_gas_seen_;
                return;
            }
            if (static_cast<int>(gas_v.size()) >= fixed_measure_samples_)
                return;
        }
        gas_v.push_back(concentration);
        gas_time_v.push_back(algorithm->node->now());
    }

    void StopAndMeasureState::addWindReading(double speed, double direction)
    {
        if (algorithm->stateMachine.getCurrentState() != this)
            return;
        if (fixed_measure_samples_ > 0) {
            if (fixed_settle_wind_seen_ < fixed_settle_samples_) {
                ++fixed_settle_wind_seen_;
                return;
            }
            if (static_cast<int>(windSpeed_v.size()) >= fixed_measure_samples_)
                return;
        }
        windSpeed_v.push_back(speed);
        windDirection_v.push_back(direction);
    }

    void StopAndMeasureState::OnExitState(State* next)
    {
        if (next != this)
            algorithm->currentResult = algorithm->checkSourceFound();
    }

    double StopAndMeasureState::average_concentration()
    {
        float average = Utils::getAverageFloatCollection(gas_v.begin(), gas_v.end());
        if (average == Utils::INVALID_AVERAGE)
        {
            GSL_WARN("No gas measurements were received during StopAndMeasure!");
            return 0;
        }
        return average;
    }
    double StopAndMeasureState::average_windDirection()
    {
        float average = Utils::getAverageDirection(windDirection_v.begin(), windDirection_v.end());
        if (average == Utils::INVALID_AVERAGE)
            return 0;
        return average;
    }
    double StopAndMeasureState::average_windSpeed()
    {
        float average = Utils::getAverageFloatCollection(windSpeed_v.begin(), windSpeed_v.end());
        if (average == Utils::INVALID_AVERAGE)
        {
            GSL_WARN("No wind measurements were received during StopAndMeasure!");
            return 0;
        }
        return average;
    }

    void StopAndMeasureState::initMeasurementTrace()
    {
        std::string filepath = algorithm->getParam<std::string>("measurement_trace_file", "");
        if (!filepath.empty()) {
            measurement_trace_file_.open(filepath, std::ios::out | std::ios::trunc);
            if (measurement_trace_file_.is_open()) {
                measurement_trace_file_ << "run_uuid,measurement_cycle_id,method,"
                    << "sim_time_start,sim_time_end,"
                    << "num_gas_samples,gas_raw_min,gas_raw_max,gas_raw_mean,gas_hit_count,gas_hit_fraction,"
                    << "gas_value_used_by_algorithm,gas_threshold_actual,gas_above_threshold,"
                    << "num_wind_samples,wind_speed_min,wind_speed_max,wind_speed_mean,"
                    << "wind_value_used_by_algorithm,wind_threshold_actual,wind_above_threshold,"
                    << "wind_direction_used_x,wind_direction_used_y,wind_direction_used_z,pose_x,pose_y,pose_z,"
                    << "algorithm_branch_code,algorithm_branch_label\n";
                measurement_trace_enabled_ = true;
            }
        }
        std::string raw_filepath = algorithm->getParam<std::string>("continuous_measurement_samples_file", "");
        if (!raw_filepath.empty()) {
            continuous_gas_trace_file_.open(raw_filepath, std::ios::out | std::ios::trunc);
            if (continuous_gas_trace_file_.is_open()) {
                continuous_gas_trace_file_ << "run_uuid,measurement_cycle_id,sample_index,sim_time,measured_gas_ppm,pose_x,pose_y,pose_z\n";
                continuous_gas_trace_enabled_ = true;
            }
        }
    }

    void StopAndMeasureState::writeMeasurementTrace(double concentration, double windSpeed, double windDirection)
    {
        if (!measurement_trace_enabled_ || !measurement_trace_file_.is_open())
            return;

        measurement_cycle_counter_++;
        writeContinuousGasTrace();
        double t_start = (measure_window_start_ - algorithm->startTime).seconds();
        double t_end = (algorithm->node->now() - algorithm->startTime).seconds();

        double gas_min = 1e9, gas_max = -1e9, gas_sum = 0;
        for (auto v : gas_v) { gas_min = std::min(gas_min, (double)v); gas_max = std::max(gas_max, (double)v); gas_sum += v; }
        double gas_mean = gas_v.empty() ? 0 : gas_sum / gas_v.size();
        const size_t gas_hit_count = std::count_if(gas_v.begin(), gas_v.end(), [this](float value) {
            return value > algorithm->thresholdGas;
        });
        const double gas_hit_fraction = gas_v.empty() ? 0.0 : static_cast<double>(gas_hit_count) / gas_v.size();

        double ws_min = 1e9, ws_max = -1e9, ws_sum = 0;
        for (auto v : windSpeed_v) { ws_min = std::min(ws_min, (double)v); ws_max = std::max(ws_max, (double)v); ws_sum += v; }
        double ws_mean = windSpeed_v.empty() ? 0 : ws_sum / windSpeed_v.size();

        double wind_dir_x = cos(windDirection);
        double wind_dir_y = sin(windDirection);

        bool gas_above = concentration > algorithm->thresholdGas;
        bool wind_above = windSpeed > algorithm->thresholdWind;

        int branch_code;
        std::string branch_label;
        if (gas_above && wind_above) { branch_code = 0; branch_label = "GAS_WIND"; }
        else if (gas_above && !wind_above) { branch_code = 1; branch_label = "GAS_NO_WIND"; }
        else if (!gas_above && wind_above) { branch_code = 2; branch_label = "NO_GAS_WIND"; }
        else { branch_code = 3; branch_label = "NOTHING"; }

        std::string run_uuid = algorithm->getParam<std::string>("run_uuid", "unknown");
        std::string method_name = algorithm->getParam<std::string>("method", "unknown");

        measurement_trace_file_ << run_uuid << "," << measurement_cycle_counter_ << "," << method_name << ","
            << t_start << "," << t_end << ","
            << gas_v.size() << "," << gas_min << "," << gas_max << "," << gas_mean << "," << gas_hit_count << "," << gas_hit_fraction << ","
            << concentration << "," << algorithm->thresholdGas << "," << (gas_above ? "true" : "false") << ","
            << windSpeed_v.size() << "," << ws_min << "," << ws_max << "," << ws_mean << ","
            << windSpeed << "," << algorithm->thresholdWind << "," << (wind_above ? "true" : "false") << ","
            << wind_dir_x << "," << wind_dir_y << "," << 0.0 << ","
            << algorithm->currentRobotPose.pose.pose.position.x << ","
            << algorithm->currentRobotPose.pose.pose.position.y << ","
            << algorithm->currentRobotPose.pose.pose.position.z << ","
            << branch_code << "," << branch_label << "\n";
        measurement_trace_file_.flush();
    }

    void StopAndMeasureState::writeContinuousGasTrace()
    {
        if (!continuous_gas_trace_enabled_ || !continuous_gas_trace_file_.is_open())
            return;
        const std::string run_uuid = algorithm->getParam<std::string>("run_uuid", "unknown");
        for (size_t i = 0; i < gas_v.size(); ++i) {
            const double t = (gas_time_v[i] - algorithm->startTime).seconds();
            continuous_gas_trace_file_ << run_uuid << "," << measurement_cycle_counter_ << "," << i << "," << t << ","
                << gas_v[i] << "," << algorithm->currentRobotPose.pose.pose.position.x << ","
                << algorithm->currentRobotPose.pose.pose.position.y << "," << algorithm->currentRobotPose.pose.pose.position.z << "\n";
        }
        continuous_gas_trace_file_.flush();
    }

} // namespace GSL


#if USE_GUI
#include "imgui.h"
void GSL::StopAndMeasureState::RenderUI()
{
    ImGui::Text("StopAndMeasureState");
}
#endif
