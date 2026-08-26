cmake_minimum_required(VERSION 3.11)
project(gsl_server) 

# enabling debug mode disables optimizations and activates a bunch of assertions in the code.
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release")
endif()

option(PFDI_LOW_MEMORY_BUILD "Compile Release without debug/sanitizer overhead on constrained validation VMs" OFF)
if(PFDI_LOW_MEMORY_BUILD)
    # This changes diagnostics and compile-time memory only.  Runtime method
    # equations, floating-point optimization level and ROS interfaces remain
    # identical to the frozen Release build.
    set(CMAKE_CXX_FLAGS "-Wpedantic ${CMAKE_CXX_FLAGS}")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 ${CMAKE_CXX_FLAGS}")
else()
    set(CMAKE_CXX_FLAGS "-g -ggdb -Wpedantic -fno-omit-frame-pointer ${CMAKE_CXX_FLAGS}")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 ${CMAKE_CXX_FLAGS}")
endif()
set(CMAKE_CXX_FLAGS_DEBUG "-O0 ${CMAKE_CXX_FLAGS}")
set(CMAKE_CXX_STANDARD 20)

set(CMAKE_VERBOSE_MAKEFILE ON)

# OPGSL V3.1 build compatibility: preserve strict Werror for new code while
# allowing pre-existing vendor/common warning classes in the legacy graph.
# No runtime equations or thresholds are changed.
add_compile_options(-Wno-error=unused-parameter -Wno-error=reorder -Wno-error=deprecated-copy -Wno-error=sign-compare -Wno-error=pedantic -Wno-error=unused-variable -Wno-error=unused-but-set-variable -Wno-error=range-loop-construct -Wno-error=missing-field-initializers)
 #Outputs the compiler command to the build log file

#########################
#OPTIONS
#########################

# extra logging to tell you what is being executed
set(GSL_TRACING ON) 
 
# if ON, the code is compiled with support for directly querying gaden simulations to obtain the wind ground truth. 
# If you dont have gaden in this workspace, you need to set this to OFF or it wont compile
set(USE_GADEN ON)

# if ON uses the nav_assistant package rather than directly communicating with nav_2. 
# It adds some extra features, but currently it has a relatively high performance cost due to async inter-process communication  
set(USE_NAV_ASSISTANT OFF) 

# Compile graphical interface with DearImGUI. Currently only affects the PMFS and SemanticPMFS algorithms. Not required to function, it is mostly for debugging purposes
set(USE_GUI OFF)


# Tracy is a profiler. ON enables some instrumentation macros (and adds a dependency to tracy). To do sampling-based profiling you also need to run the node as sudo
set(USE_TRACY OFF) 
# disable to do sampling-only profiling
set(USE_TRACY_INSTRUMENTATION OFF) 

set(DISABLE_NAVIGATION OFF) # Disables navigation decisions and lets you control the robot directly. For testing, mostly
##############################################################################


if(NOT PFDI_LOW_MEMORY_BUILD)
    include(CMake/SanitizationOptions.cmake)
endif()
include(CMake/HandleConditionals.cmake)
include(CMake/CommonDependencies.cmake)


#########################
## INCLUDES
#########################

include_directories(
  src
  third_party/DDA/include
  third_party/DDA/third_party/glm
  third_party/StateMachine/include
)

##########################
# EXECUTABLES
##########################

#### Server node
##############
add_executable(gsl_actionserver_node src/gsl_server/gsl_server.cpp)
ament_target_dependencies( gsl_actionserver_node
    rclcpp
    rclcpp_action
    gsl_actions
)

##### Call node
add_executable(gsl_actionserver_call src/aux_nodes/gsl_server_call.cpp)
ament_target_dependencies( gsl_actionserver_call
    rclcpp
    rclcpp_action
    gsl_actions
)

#### Send pose node
add_executable(send_pose src/aux_nodes/send_pose.cpp)
ament_target_dependencies( send_pose
    rclcpp
    geometry_msgs
)

##########################
# ALGORITHMS
##########################

include(src/gsl_server/algorithms/Common/CMakeLists.txt) # Required

# You can disable the compilation of any of these algorithms by commenting them out here (useful if you don't want to install their dependencies)
###############################################################################################################################################
include(src/gsl_server/algorithms/PMFS/CMakeLists.txt)

# Isolated ME-ACI development replay. It is never installed or launched by ROS.
add_executable(meaci_replay_true tools/meaci_replay_true.cpp)
ament_target_dependencies(meaci_replay_true
    ${COMMON_AMENT_DEPENDENCIES}
    gmrf_msgs
    ${CONDITIONAL_GADEN_MSGS}
)
target_link_libraries(meaci_replay_true PMFS)

# Truth-free physical trace-bank builder for the CTT premise gates. It is not
# installed or launched by ROS and cannot access planner or final-source truth.
add_executable(ctt_trace_bank_builder tools/ctt_trace_bank_builder.cpp)
ament_target_dependencies(ctt_trace_bank_builder
    ${COMMON_AMENT_DEPENDENCIES}
    gmrf_msgs
    ${CONDITIONAL_GADEN_MSGS}
)
target_link_libraries(ctt_trace_bank_builder PMFS)
#include(src/gsl_server/algorithms/Semantics/CMakeLists.txt) # There is further modularity inside of this file!



##########################
# INSTALLATION
##########################

if(BUILD_TESTING)
  enable_testing()
  add_executable(
    test_opgsl_scientific_v31_core
    test/test_opgsl_scientific_v31_core.cpp
  )
  target_compile_definitions(
    test_opgsl_scientific_v31_core PRIVATE OPGSL_CORE_STANDALONE
  )
  target_compile_features(test_opgsl_scientific_v31_core PRIVATE cxx_std_20)
  target_compile_options(
    test_opgsl_scientific_v31_core PRIVATE
    -Wall -Wextra -Wpedantic -Werror -UNDEBUG
  )
  add_test(
    NAME opgsl_scientific_v31_core
    COMMAND test_opgsl_scientific_v31_core
  )

  add_executable(
    test_opgsl_scientific_v31_vertical_gate
    test/test_opgsl_scientific_v31_vertical_gate.cpp
  )
  target_compile_definitions(
    test_opgsl_scientific_v31_vertical_gate PRIVATE OPGSL_CORE_STANDALONE
  )
  target_compile_features(test_opgsl_scientific_v31_vertical_gate PRIVATE cxx_std_20)
  target_compile_options(
    test_opgsl_scientific_v31_vertical_gate PRIVATE
    -Wall -Wextra -Wpedantic -Werror -UNDEBUG
  )
  add_test(
    NAME opgsl_scientific_v31_vertical_gate
    COMMAND test_opgsl_scientific_v31_vertical_gate
  )

  add_executable(
    test_ctt_transport_trace
    test/test_ctt_transport_trace.cpp
  )
  target_compile_features(test_ctt_transport_trace PRIVATE cxx_std_20)
  target_compile_options(
    test_ctt_transport_trace PRIVATE
    -Wall -Wextra -Wpedantic -Werror -UNDEBUG
  )
  add_test(
    NAME ctt_transport_trace
    COMMAND test_ctt_transport_trace
  )
endif()

install(
  TARGETS gsl_actionserver_node  gsl_actionserver_call send_pose
  DESTINATION lib/${PROJECT_NAME}
)

install(
	DIRECTORY resources
	DESTINATION share/${PROJECT_NAME}
)
ament_package()
