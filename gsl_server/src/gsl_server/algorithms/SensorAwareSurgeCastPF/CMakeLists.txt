file(GLOB_RECURSE SOURCES "${CMAKE_CURRENT_LIST_DIR}/*.cpp")
add_library(SensorAwareSurgeCastPF ${SOURCES})
ament_target_dependencies(SensorAwareSurgeCastPF ${COMMON_AMENT_DEPENDENCIES})
target_include_directories(SensorAwareSurgeCastPF PUBLIC ${CMAKE_CURRENT_LIST_DIR})
target_link_libraries(SensorAwareSurgeCastPF
    OpenMP::OpenMP_CXX fmt ${CONDITIONAL_TRACY} GSL_common PlumeTracking)
add_compile_definitions(ENABLE_SENSOR_AWARE_SC_PF=1)
target_link_libraries(gsl_actionserver_node SensorAwareSurgeCastPF)
