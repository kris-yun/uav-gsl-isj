file(GLOB_RECURSE SOURCES "${CMAKE_CURRENT_LIST_DIR}/*.cpp")

find_package(Eigen3 REQUIRED)

# Create the library
add_library(OPGSL ${SOURCES})

# Link ament dependencies
ament_target_dependencies(OPGSL
    ${COMMON_AMENT_DEPENDENCIES}
)

# Link other dependencies
target_link_libraries(OPGSL
    Eigen3::Eigen
    fmt
    GSL_common
)
add_compile_definitions(ENABLE_OPGSL=1)


target_link_libraries(gsl_actionserver_node
    OPGSL
)
