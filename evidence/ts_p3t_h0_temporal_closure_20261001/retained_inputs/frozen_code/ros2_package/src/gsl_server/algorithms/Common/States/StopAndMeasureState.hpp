#pragma once

#include <gsl_server/algorithms/Common/States/GSLState.hpp>
#include <rclcpp/time.hpp>
#include <vector>
#include <fstream>
#include <string>
#include "gsl_server/core/ConditionalMacros.hpp"

namespace GSL
{
    class StopAndMeasureState : public State
    {
    public:
        StopAndMeasureState(Algorithm* _algorithm);

        double average_concentration();                              // average of all the readings since we entered the state
        double average_windDirection();                              // average of all the readings since we entered the state
        double average_windSpeed();                                  // average of all the readings since we entered the state
        virtual void addGasReading(double concentration);            // called from the sensor callback
        virtual void addWindReading(double speed, double direction); // called from the sensor callback
        virtual void OnUpdate() override;
        // Read-only view used by TESS to form the exact completed measurement
        // block.  It deliberately exposes neither source truth nor planner state.
        const std::vector<float>& gasSamples() const { return gas_v; }

    protected:
        virtual void OnEnterState(State* previousState) override;
        virtual void OnExitState(State* nextState) override;
        IF_GUI(void RenderUI() override;)

    protected:
        double measure_time; // how long to measure for, in seconds
        rclcpp::Time time_stopped;

        // Disabled by default so legacy algorithms retain their existing
        // duration-based protocol.  The active paired harness explicitly
        // enables this exact-sample protocol to remove callback-scheduling
        // variability from TESS block formation.
        int fixed_settle_samples_ = -1;
        int fixed_measure_samples_ = -1;
        int fixed_settle_gas_seen_ = 0;
        int fixed_settle_wind_seen_ = 0;
        bool fixed_block_completed_ = false;

    private:
        std::vector<float> gas_v;
        std::vector<rclcpp::Time> gas_time_v;
        std::vector<float> windSpeed_v;
        std::vector<float> windDirection_v;

        // Measurement trace logger (read-only)
        std::ofstream measurement_trace_file_;
        std::ofstream continuous_gas_trace_file_;
        bool measurement_trace_enabled_ = false;
        bool continuous_gas_trace_enabled_ = false;
        int measurement_cycle_counter_ = 0;
        rclcpp::Time measure_window_start_;
        void initMeasurementTrace();
        void writeMeasurementTrace(double concentration, double windSpeed, double windDirection);
        void writeContinuousGasTrace();
    };
} // namespace GSL
