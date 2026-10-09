#include "Fixture.hpp"
#include <gsl_server/algorithms/Common/Algorithm.hpp>
#include <gsl_server/algorithms/Common/Utils/RosUtils.hpp>
#include <std_msgs/msg/string.hpp>
#include <rclcpp/serialization.hpp>
#include <omp.h>
#include <thread>

using namespace GSL;
using namespace R4;
class Capture : public Algorithm {
 fs::path output;
 Fixture fixture;
 std::unique_ptr<Simulations> simulations;
 std::ofstream raw,wire,events;
 size_t block=1,gases=0,winds=0,gasid=0,windid=0;
 rclcpp::Subscription<std_msgs::msg::String>::SharedPtr trigger;
 bool updated=false;
 template<class T> void serialize(const T& msg,int64_t receipt,const std::string& type) {
  rclcpp::SerializedMessage a;rclcpp::Serialization<T> serializer;serializer.serialize_message(&msg,&a);auto b=a.get_rcl_serialized_message();std::ostringstream hex;hex<<std::hex<<std::setfill('0');for(size_t i=0;i<b.buffer_length;++i)hex<<std::setw(2)<<int(b.buffer[i]);
  wire<<"{\"type\":\""<<type<<"\",\"block_id\":"<<block<<",\"receipt_ns\":"<<receipt<<",\"cdr_hex\":\""<<hex.str()<<"\"}\n";wire.flush();
 }
 template<class T> void trace(const T& msg,int64_t receipt,const std::string& kind,size_t id,double ppm,double units,double raw_value,double speed,double local_dir,const PoseStamped& transformed) {
  auto sample=tfBuffer.buffer.lookupTransform("map",msg.header.frame_id,rclcpp::Time(msg.header.stamp));
  auto latest=tfBuffer.buffer.lookupTransform("map",msg.header.frame_id,tf2::TimePointZero);
  auto stamp=int64_t(msg.header.stamp.sec)*1000000000LL+msg.header.stamp.nanosec;
  auto tfns=int64_t(transformed.header.stamp.sec)*1000000000LL+transformed.header.stamp.nanosec;
  auto sensns=int64_t(sample.header.stamp.sec)*1000000000LL+sample.header.stamp.nanosec;
  auto latestns=int64_t(latest.header.stamp.sec)*1000000000LL+latest.header.stamp.nanosec;
  double yaw=Utils::getYaw(sample.transform.rotation),nowyaw=Utils::getYaw(latest.transform.rotation);
  auto delta=std::atan2(std::sin(nowyaw-yaw),std::cos(nowyaw-yaw));
  double drift=std::hypot(latest.transform.translation.x-sample.transform.translation.x,latest.transform.translation.y-sample.transform.translation.y);
  if(receipt<stamp||double(receipt-stamp)/1e9>=2||drift>=.01||std::abs(delta)>=1e-4||node->get_parameter("use_sim_time").as_bool())throw std::runtime_error("NEW_FIXTURE_CLOCK_TF_CONTRACT_FAILED");
  raw<<kind<<","<<id<<","<<block<<","<<stamp<<","<<msg.header.frame_id<<","<<receipt<<","<<raw_value<<","<<units<<","<<ppm<<","<<speed<<","<<local_dir<<","<<(kind=="wind"?Utils::getYaw(transformed.pose.orientation):0)<<","<<tfns<<","<<sensns<<","<<sample.transform.translation.x<<","<<sample.transform.translation.y<<","<<yaw<<","<<latestns<<","<<latest.transform.translation.x<<","<<latest.transform.translation.y<<","<<nowyaw<<","<<drift<<","<<std::abs(delta)<<"\n";raw.flush();
 }
 void ready() {
  size_t active=0;for(const auto& n:simulations->QTleaves)active+=n.value==1;
  if(fixture.hit.size()!=1102||fixture.meta.numFreeCells!=626||active!=simulations->QTleaves.size()||omp_get_max_threads()!=1)throw std::runtime_error("PRE_RUN_ARRAY_OR_THREAD_SCHEMA_FAILED");
  fixture.verifyTree(*simulations);R4Audit::tree(simulations->QTleaves,"coarse_tree.csv");
  if(!raw||!wire||!events||!R4Audit::candidate_log)throw std::runtime_error("PRE_RUN_LOG_SINK_FAILED");
  std::ofstream f(output/"READY_SCHEMA.json");f<<"{\"run_id\":\"P1B_NATIVE_CAPTURE_R4\",\"input_class\":\"SYNTHETIC_OR_REPLAY_FIXTURE\",\"pid\":"<<getpid()<<",\"grid_cells\":1102,\"free_cells\":626,\"coarse_leaves\":"<<active<<",\"total_coarse_nodes\":"<<simulations->QTleaves.size()<<",\"threads\":1,\"use_sim_time\":false,\"raw_message_fields\":[\"stamp\",\"frame\",\"receipt\",\"cdr\",\"block\",\"sample_TF\",\"consumer_TF\"],\"native_update_hooks\":[\"leaf_samples\",\"rng_engine\",\"gaussian_cache\",\"unblurred_hit_map\",\"blurred_hit_map\",\"raw_score\",\"local_refinement_tree\",\"normalization\",\"final_posterior\"]}\n";
 }
 void updateOnce() {
  if(updated||block!=4)throw std::runtime_error("ONE_SHOT_OR_MEASUREMENT_SCHEMA_FAILED");
  fixture.dumpHit(output/"hit_before_update.csv");R4Audit::tree(simulations->QTleaves,"coarse_tree.csv");
  std::vector<float> wind;wind.reserve(fixture.wind.size()*2);for(auto w:fixture.wind){wind.push_back(w.x);wind.push_back(w.y);}R4Audit::binary(output/"forward_wind_snapshot.f32",wind);
  for(auto& h:fixture.hit)if(!std::isfinite(h.logOdds)||!std::isfinite(h.confidence))throw std::runtime_error("PRE_UPDATE_NONFINITE_MAP");
  std::ofstream rng(output/"rng_before_update.txt");rng<<Utils::r4_rng_state()<<"\n";rng.close();
  std::ofstream pre(output/"PRE_UPDATE_VALIDATION.json");pre<<"{\"all_raw_members_bound\":true,\"gas_count\":9,\"wind_count\":9,\"blocks\":3,\"native_pid\":"<<getpid()<<",\"hooks_installed_before_execution\":true,\"time_ns\":"<<node->now().nanoseconds()<<"}\n";pre.close();
  updated=true;std::ofstream(output/"SOURCE_UPDATE_STARTED.txt")<<node->now().nanoseconds()<<"\n";
  simulations->updateSourceProbability(float(fixture.sim.refineFraction));
  R4Audit::binary(output/"variance.f64",simulations->varianceOfHitProb);
  R4Audit::finish(fixture.posterior);fixture.dumpPosterior(output);
  std::ofstream f(output/"NATIVE_COMPLETE.json");f<<"{\"run_id\":\"P1B_NATIVE_CAPTURE_R4\",\"native_source_updates\":1,\"pid\":"<<getpid()<<",\"candidate_simulations\":"<<R4Audit::serial<<",\"time_ns\":"<<node->now().nanoseconds()<<"}\n";done=true;
 }
protected:
 void processGasAndWindMeasurements(double concentration,double speed,double direction) override {
  if(gases!=3||winds!=3||block>3)throw std::runtime_error("NEW_RAW_MEASUREMENT_BLOCK_MEMBERSHIP_FAILED");
  auto ij=fixture.meta.coordinatesToIndices(currentRobotPosition.x,currentRobotPosition.y);
  if(!fixture.hitGrid().freeAt(ij.x,ij.y))throw std::runtime_error("fixture robot outside free map");
  bool hit=concentration>thresholdGas;
  fixture.measurement(hit,direction,speed,ij);fixture.dumpHit(output/("hit_after_block_"+std::to_string(block)+".csv"));
  events<<block<<","<<node->now().nanoseconds()<<","<<concentration<<","<<thresholdGas<<","<<hit<<","<<speed<<","<<direction<<","<<ij.x<<","<<ij.y<<","<<currentRobotPosition.x<<","<<currentRobotPosition.y<<","<<gases<<","<<winds<<"\n";events.flush();
  block++;gases=winds=0;stateMachine.forceResetState(stopAndMeasureState.get());
 }
public:
 bool done=false;
 Capture(std::shared_ptr<rclcpp::Node> n,const fs::path& input,const fs::path& out):Algorithm(n),output(out),fixture(input) {
  if(fs::exists(output/"NATIVE_COMPLETE.json"))throw std::runtime_error("native capture already completed");fs::create_directories(output);
  thresholdGas=.1;thresholdWind=.1;getParam<double>("stop_and_measure_time",.1);
  stopAndMeasureState=std::make_unique<StopAndMeasureState>(this);waitForGasState=std::make_unique<WaitForGasState>(this);stateMachine.forceSetState(stopAndMeasureState.get());
  simulations=fixture.simulation();R4Audit::initialize(output);
  raw.open(output/"raw_consumed_messages.csv");raw<<std::setprecision(17)<<"kind,message_id,block_id,stamp_ns,frame_id,receipt_ns,raw,raw_units,ppm,speed,local_direction,map_TO_direction,returned_TF_stamp_ns,sample_TF_stamp_ns,sample_x,sample_y,sample_yaw,consumer_latest_TF_stamp_ns,consumer_x,consumer_y,consumer_yaw,pose_drift_xy_m,pose_drift_yaw_rad\n";
  wire.open(output/"raw_ros_cdr.jsonl");events.open(output/"measurement_events.csv");events<<std::setprecision(17)<<"block_id,consumer_ns,concentration,threshold,hit,wind_speed,wind_direction,robot_i,robot_j,robot_x,robot_y,gas_members,wind_members\n";
  raw.flush();events.flush();
  localizationSub=node->create_subscription<PoseWithCovarianceStamped>("/r4/pose",10,[this](PoseWithCovarianceStamped::SharedPtr m){localizationCallback(m);});
  gasSub=node->create_subscription<olfaction_msgs::msg::GasSensor>("/r4/gas",20,[this](olfaction_msgs::msg::GasSensor::SharedPtr m){auto now=node->now().nanoseconds();serialize(*m,now,"GasSensor");auto ppm=Algorithm::gasCallback(m);trace(*m,now,"gas",++gasid,ppm,m->raw_units,m->raw,0,0,PoseStamped());gases++;});
  windSub=node->create_subscription<olfaction_msgs::msg::Anemometer>("/r4/pmfs_to",20,[this](olfaction_msgs::msg::Anemometer::SharedPtr m){auto now=node->now().nanoseconds();serialize(*m,now,"Anemometer");auto p=Algorithm::windCallback(m);trace(*m,now,"wind",++windid,0,0,0,m->wind_speed,m->wind_direction,p);winds++;});
  trigger=node->create_subscription<std_msgs::msg::String>("/r4/trigger",10,[this](std_msgs::msg::String::SharedPtr m){if(m->data!="RUN_P1B_NATIVE_CAPTURE_R4")throw std::runtime_error("invalid capture trigger");updateOnce();});
  ready();
 }
 void poll() {rclcpp::spin_some(node);if(block<=3&&gases==3&&winds==3)stopAndMeasureState->OnUpdate();}
};
int main(int argc,char** argv) {
 try {if(argc<3)throw std::runtime_error("native_capture INPUT OUTPUT [--ros-args...]");fs::path input=argv[1],output=argv[2];rclcpp::init(argc,argv);auto node=std::make_shared<rclcpp::Node>("r4_native_capture");Capture capture(node,input,output);
  auto start=std::chrono::steady_clock::now();while(rclcpp::ok()&&!capture.done){capture.poll();std::this_thread::sleep_for(std::chrono::milliseconds(2));if(std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()>900)throw std::runtime_error("R4_NATIVE_900S_LIMIT");}
  rclcpp::shutdown();return capture.done?0:2;
 }catch(const std::exception& e){std::cerr<<"R4_NATIVE_ERROR: "<<e.what()<<"\n";return 1;}
}
