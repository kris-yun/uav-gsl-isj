#pragma once
#include <fstream>
#include <string>
#include <gsl_server/algorithms/Common/States/GSLState.hpp>
#include <rclcpp/time.hpp>
#include "gsl_server/core/ConditionalMacros.hpp"

namespace GSL
{
    // Does nothing. As soon as a gas reading above the threshold arrives, moves to StopAndMeasure
    class WaitForGasState : public State
    {
    public:
        WaitForGasState(Algorithm* _algorithm);

        void addMeasurement(double concentration);
        void OnUpdate() override;

    protected:
        void OnEnterState(State* previous) override;

    protected:
        float maxWaitTime;
        rclcpp::Time startTime;
        IF_GUI(void RenderUI() override;)
        // Diagnostic logger (read-only)
        std::ofstream wait_diag_file_;
        bool wait_diag_enabled_ = false;
        int wait_cycle_counter_ = 0;
        int gas_sample_count_ = 0;
        double gas_max_ = 0;
        double gas_sum_ = 0;
        rclcpp::Time wait_enter_time_;
        void initWaitDiag();
        void logWaitCycle(bool timeout, double goal_x, double goal_y, bool found_gas);
    };
} // namespace GSL