#pragma once

#include "gsl_server/algorithms/PMFS/internal/PFDEIPredictiveProvider.hpp"

#include <olfaction_msgs/msg/gas_sensor.hpp>
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/u_int64.hpp>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>

#include <atomic>
#include <cmath>
#include <cstdint>
#include <map>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace GSL::PMFS_internal::pfsnre
{
    // Truth-free asynchronous acquisition path.  It exists because native PMFS
    // source simulations can block the main Algorithm::OnUpdate/spin_some loop.
    // The recorder keeps the complete sensor-exposure trajectory, including
    // samples that the depth-1 Classic PMFS subscription may legitimately drop.
    class AsyncRecorder
    {
    public:
        struct Sample
        {
            std::int64_t stampNs = 0;
            pfdei::SampleContext context;
            float measuredPpm = 0.0f;
            bool acceptedByStopAndMeasure = false;
            std::size_t acceptedCountAfter = 0;
            std::size_t stopIndex = 0;
        };

        AsyncRecorder(const std::string& gasTopic,
                      const std::string& iterationTopic,
                      bool useSimTime)
            : node_(std::make_shared<rclcpp::Node>(
                  "pf_snre_async_recorder",
                  rclcpp::NodeOptions().parameter_overrides({rclcpp::Parameter("use_sim_time", useSimTime)}))),
              tfBuffer_(node_->get_clock()),
              tfListener_(tfBuffer_)
        {
            rclcpp::QoS iterationQos(1);
            iterationQos.reliable().transient_local();
            iterationSub_ = node_->create_subscription<std_msgs::msg::UInt64>(
                iterationTopic, iterationQos,
                [this](std_msgs::msg::UInt64::SharedPtr msg)
                {
                    currentIteration_.store(static_cast<std::int64_t>(msg->data), std::memory_order_release);
                });

            rclcpp::QoS gasQos(4096);
            gasQos.reliable();
            gasSub_ = node_->create_subscription<olfaction_msgs::msg::GasSensor>(
                gasTopic, gasQos,
                [this](olfaction_msgs::msg::GasSensor::SharedPtr msg) { onGas(std::move(msg)); });

            executor_.add_node(node_);
            thread_ = std::thread([this]() { executor_.spin(); });
        }

        AsyncRecorder(const AsyncRecorder&) = delete;
        AsyncRecorder& operator=(const AsyncRecorder&) = delete;

        ~AsyncRecorder()
        {
            executor_.cancel();
            if (thread_.joinable()) thread_.join();
            executor_.remove_node(node_);
        }

        void markAccepted(std::int64_t stampNs, std::size_t acceptedCountAfter, std::size_t stopIndex)
        {
            if (acceptedCountAfter < 1 || acceptedCountAfter > 10)
                throw std::invalid_argument("PF-SNRE accepted sample count must be 1..10");
            std::lock_guard<std::mutex> lock(mutex_);
            for (auto it = samples_.rbegin(); it != samples_.rend(); ++it)
            {
                if (it->stampNs == stampNs)
                {
                    applyMark(*it, acceptedCountAfter, stopIndex);
                    return;
                }
                if (it->stampNs < stampNs) break;
            }
            const auto [it, inserted] = pendingMarks_.emplace(stampNs, Mark{acceptedCountAfter, stopIndex});
            if (!inserted)
                throw std::runtime_error("PF-SNRE duplicate pending accepted-sample mark");
        }

        std::vector<Sample> snapshot() const
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if (!fatalError_.empty()) throw std::runtime_error(fatalError_);
            if (!pendingMarks_.empty())
                throw std::runtime_error("PF-SNRE recorder still has accepted samples not observed by async path");
            if (currentIteration_.load(std::memory_order_acquire) < 0)
                throw std::runtime_error("PF-SNRE recorder has not received GADEN current_iteration");
            return samples_;
        }

        std::size_t size() const
        {
            std::lock_guard<std::mutex> lock(mutex_);
            return samples_.size();
        }

        std::int64_t currentIteration() const
        {
            return currentIteration_.load(std::memory_order_acquire);
        }

    private:
        struct Mark { std::size_t count; std::size_t stop; };

        std::shared_ptr<rclcpp::Node> node_;
        tf2_ros::Buffer tfBuffer_;
        tf2_ros::TransformListener tfListener_;
        rclcpp::Subscription<std_msgs::msg::UInt64>::SharedPtr iterationSub_;
        rclcpp::Subscription<olfaction_msgs::msg::GasSensor>::SharedPtr gasSub_;
        rclcpp::executors::SingleThreadedExecutor executor_;
        std::thread thread_;
        std::atomic<std::int64_t> currentIteration_{-1};
        mutable std::mutex mutex_;
        std::vector<Sample> samples_;
        std::map<std::int64_t, Mark> pendingMarks_;
        std::string fatalError_;

        static float ppmFromGasMsg(const olfaction_msgs::msg::GasSensor::SharedPtr& msg)
        {
            if (msg->raw_units == msg->UNITS_OHM)
            {
                const double rs_r0 = msg->raw / 50000.0;
                const double ppm = std::pow(rs_r0 / msg->calib_a, 1.0 / msg->calib_b);
                if (!(ppm >= 0.0) || !std::isfinite(ppm))
                    throw std::runtime_error("PF-SNRE async recorder invalid OHM->ppm conversion");
                return static_cast<float>(ppm);
            }
            if (msg->raw_units == msg->UNITS_PPM)
            {
                if (!(msg->raw >= 0.0) || !std::isfinite(msg->raw))
                    throw std::runtime_error("PF-SNRE async recorder invalid ppm message");
                return static_cast<float>(msg->raw);
            }
            throw std::runtime_error("PF-SNRE async recorder unknown gas concentration unit");
        }

        void onGas(olfaction_msgs::msg::GasSensor::SharedPtr msg)
        {
            try
            {
                const auto iteration = currentIteration_.load(std::memory_order_acquire);
                if (iteration < 0)
                    throw std::runtime_error("PF-SNRE gas arrived before current_iteration instrumentation");
                const rclcpp::Time stamp(msg->header.stamp);
                if (msg->header.frame_id.empty())
                    throw std::runtime_error("PF-SNRE gas message has empty sensor frame");
                const auto transform = tfBuffer_.lookupTransform("map", msg->header.frame_id, stamp);

                Sample sample;
                sample.stampNs = stamp.nanoseconds();
                sample.context.timeS = static_cast<double>(sample.stampNs) * 1e-9;
                sample.context.x = transform.transform.translation.x;
                sample.context.y = transform.transform.translation.y;
                sample.context.z = transform.transform.translation.z;
                sample.context.playbackIteration = iteration;
                sample.measuredPpm = ppmFromGasMsg(msg);

                std::lock_guard<std::mutex> lock(mutex_);
                if (!samples_.empty() && sample.stampNs <= samples_.back().stampNs)
                    throw std::runtime_error("PF-SNRE async gas timestamps are not strictly increasing");
                const auto pending = pendingMarks_.find(sample.stampNs);
                if (pending != pendingMarks_.end())
                {
                    applyMark(sample, pending->second.count, pending->second.stop);
                    pendingMarks_.erase(pending);
                }
                samples_.push_back(std::move(sample));
            }
            catch (const std::exception& e)
            {
                std::lock_guard<std::mutex> lock(mutex_);
                if (fatalError_.empty()) fatalError_ = std::string("PF-SNRE async recorder failure: ") + e.what();
            }
        }

        static void applyMark(Sample& sample, std::size_t acceptedCountAfter, std::size_t stopIndex)
        {
            if (sample.acceptedByStopAndMeasure)
                throw std::runtime_error("PF-SNRE sample marked accepted twice");
            sample.acceptedByStopAndMeasure = true;
            sample.acceptedCountAfter = acceptedCountAfter;
            sample.stopIndex = stopIndex;
        }
    };
}
