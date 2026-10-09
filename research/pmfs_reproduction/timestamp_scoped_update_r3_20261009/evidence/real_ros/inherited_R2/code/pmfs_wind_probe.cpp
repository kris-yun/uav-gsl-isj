#include <gsl_server/algorithms/Common/Algorithm.hpp>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <gsl_server/algorithms/Common/Utils/RosUtils.hpp>
#include <fstream>
#include <iomanip>
#include <cstdlib>

// Controlled ROS fixture: runs the upstream windCallback and upstream
// StopAndMeasure storage/averaging, without navigation or gas generation.
class Probe : public GSL::Algorithm {
public:
    explicit Probe(std::shared_ptr<rclcpp::Node> n):Algorithm(n) {
        stopAndMeasureState=std::make_unique<GSL::StopAndMeasureState>(this);
        stateMachine.forceSetState(stopAndMeasureState.get());
        windSub=node->create_subscription<olfaction_msgs::msg::Anemometer>(
            getParam<std::string>("anemometer_topic","/r2/pmfs_to"),10,
            [this](const olfaction_msgs::msg::Anemometer::SharedPtr msg){
                stateMachine.forceResetState(stopAndMeasureState.get());
                auto pose=Algorithm::windCallback(msg);
                std::ofstream out(std::getenv("PMFS_R2_TRACE"),std::ios::app);
                out<<std::setprecision(17)<<msg->header.stamp.sec<<","<<msg->header.stamp.nanosec<<","<<msg->header.frame_id<<","
                   <<msg->wind_speed<<","<<msg->wind_direction<<","<<pose.header.frame_id<<","<<pose.header.stamp.sec<<","<<pose.header.stamp.nanosec<<","
                   <<pose.pose.position.x<<","<<pose.pose.position.y<<","<<GSL::Utils::getYaw(pose.pose.orientation)<<","
                   <<stopAndMeasureState->average_windSpeed()<<","<<stopAndMeasureState->average_windDirection()<<","
                   <<node->now().nanoseconds()<<","<<node->get_parameter("use_sim_time").as_bool()<<"\n";
            });
    }
protected:
    void processGasAndWindMeasurements(double,double,double) override {}
};
int main(int argc,char**argv) {
    rclcpp::init(argc,argv);
    auto node=std::make_shared<rclcpp::Node>("pmfs_wind_probe");
    Probe probe(node);
    rclcpp::spin(node);
    rclcpp::shutdown();
}
