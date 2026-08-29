
file(GLOB_RECURSE SOURCES "${CMAKE_CURRENT_LIST_DIR}/*.cpp") 

find_package(gmrf_msgs REQUIRED)
# PF-SNRE's trajectory-independent online provider uses the exact GADEN Humble
# core already exported by gaden_common (PlaybackSimulation/SampleConcentration).
# This is not a second simulator implementation.
find_package(gaden_common REQUIRED)

# Create the library
add_library(PMFS ${SOURCES})

# Link ament dependencies
ament_target_dependencies(PMFS
    ${COMMON_AMENT_DEPENDENCIES}
    gmrf_msgs
    gaden_common
    ${CONDITIONAL_GADEN_MSGS}
)

# Link other dependencies
target_link_libraries(PMFS  
    ${OpenCV_LIBS}
    OpenMP::OpenMP_CXX
    fmt
    ${CONDITIONAL_TRACY}
    GSL_common
)
add_compile_definitions(ENABLE_PMFS=1)


target_link_libraries(gsl_actionserver_node
    PMFS
)
