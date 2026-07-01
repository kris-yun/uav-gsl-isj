file(GLOB_RECURSE SOURCES "${CMAKE_CURRENT_LIST_DIR}/*.cpp")
add_library(OPGSL ${SOURCES})
ament_target_dependencies(OPGSL ${COMMON_AMENT_DEPENDENCIES})
target_include_directories(OPGSL PUBLIC ${CMAKE_CURRENT_LIST_DIR})
target_link_libraries(OPGSL
    OpenMP::OpenMP_CXX fmt ${CONDITIONAL_TRACY} GSL_common)
add_compile_definitions(ENABLE_OPGSL=1)
target_link_libraries(gsl_actionserver_node OPGSL)
