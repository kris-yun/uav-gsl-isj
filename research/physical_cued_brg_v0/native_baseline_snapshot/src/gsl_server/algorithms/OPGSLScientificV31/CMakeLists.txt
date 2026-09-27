file(GLOB_RECURSE SOURCES "${CMAKE_CURRENT_LIST_DIR}/*.cpp")

find_package(Eigen3 REQUIRED)

add_library(OPGSL_SCIENTIFIC_V31 ${SOURCES})
ament_target_dependencies(OPGSL_SCIENTIFIC_V31 ${COMMON_AMENT_DEPENDENCIES})
target_link_libraries(OPGSL_SCIENTIFIC_V31 Eigen3::Eigen fmt GSL_common)
target_compile_definitions(OPGSL_SCIENTIFIC_V31 PRIVATE ENABLE_OPGSL_SCIENTIFIC_V31=1)
target_compile_definitions(gsl_actionserver_node PRIVATE ENABLE_OPGSL_SCIENTIFIC_V31=1)
target_link_libraries(gsl_actionserver_node OPGSL_SCIENTIFIC_V31)
