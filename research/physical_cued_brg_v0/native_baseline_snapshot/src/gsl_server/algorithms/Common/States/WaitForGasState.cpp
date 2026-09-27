#include <gsl_server/algorithms/Common/Algorithm.hpp>
#include <gsl_server/algorithms/Common/States/WaitForGasState.hpp>
#include <gsl_server/core/Logging.hpp>

namespace GSL
{
    WaitForGasState::WaitForGasState(Algorithm* _algorithm)
        : State(_algorithm)
    {
        maxWaitTime = algorithm->getParam<float>("maxWaitForGasTime", 10.0);
        initWaitDiag();
    }

    void WaitForGasState::OnEnterState(State* previous)
    {
        GSL_TRACE("Entering WaitForGas");
        startTime = algorithm->node->now();
        wait_enter_time_ = startTime;
        gas_sample_count_ = 0;
        gas_max_ = 0;
        gas_sum_ = 0;
    }

    void WaitForGasState::OnUpdate()
    {
        if ((algorithm->node->now() - startTime).seconds() > maxWaitTime)
        {
            GSL_WARN("Timed out while waiting for gas, going exploring");
            NavigateToPose::Goal goal;
            goal.pose = algorithm->getRandomPoseInMap();
            algorithm->movingState->sendGoal(goal);
            // Log timeout event
            logWaitCycle(true, goal.pose.pose.position.x, goal.pose.pose.position.y, false);
        }
    }

    void WaitForGasState::addMeasurement(double concentration)
    {
        if (algorithm->stateMachine.getCurrentState() != this)
            return;
        gas_sample_count_++;
        gas_sum_ += concentration;
        if (concentration > gas_max_) gas_max_ = concentration;
        if (concentration > algorithm->thresholdGas)
        {
            GSL_INFO("Found gas! (concentration={:.6f} > threshold={:.6f})", concentration, algorithm->thresholdGas);
            logWaitCycle(false, 0, 0, true);
            algorithm->stateMachine.forceSetState(algorithm->stopAndMeasureState.get());
        }
    }

    void WaitForGasState::initWaitDiag()
    {
        std::string filepath = algorithm->getParam<std::string>("wait_diag_file", "");
        if (!filepath.empty()) {
            wait_diag_file_.open(filepath, std::ios::out | std::ios::trunc);
            if (wait_diag_file_.is_open()) {
                wait_diag_file_ << "wait_cycle_id,wait_enter_time,wait_elapsed,"
                    << "gas_sample_count,gas_max,gas_mean,gas_threshold,"
                    << "gas_above_threshold,timeout_triggered,"
                    << "exploration_goal_x,exploration_goal_y,"
                    << "found_gas,entered_stop_and_measure\n";
                wait_diag_enabled_ = true;
            }
        }
    }

    void WaitForGasState::logWaitCycle(bool timeout, double goal_x, double goal_y, bool found_gas)
    {
        if (!wait_diag_enabled_ || !wait_diag_file_.is_open()) return;
        wait_cycle_counter_++;
        double elapsed = (algorithm->node->now() - wait_enter_time_).seconds();
        double gas_mean = gas_sample_count_ > 0 ? gas_sum_ / gas_sample_count_ : 0;
        bool above = gas_max_ > algorithm->thresholdGas;
        wait_diag_file_ << wait_cycle_counter_ << ","
            << wait_enter_time_.seconds() << "," << elapsed << ","
            << gas_sample_count_ << "," << gas_max_ << "," << gas_mean << ","
            << algorithm->thresholdGas << "," << (above ? "true" : "false") << ","
            << (timeout ? "true" : "false") << ","
            << goal_x << "," << goal_y << ","
            << (found_gas ? "true" : "false") << ","
            << (found_gas ? "true" : "false") << "\n";
        wait_diag_file_.flush();
    }

} // namespace GSL

#if USE_GUI
#include "imgui.h"
void GSL::WaitForGasState::RenderUI()
{
    ImGui::Text("WaitForGasState");
}
#endif