
file(GLOB_RECURSE SOURCES "${CMAKE_CURRENT_LIST_DIR}/*.cpp")
# Some older VM checkouts contain an untracked duplicate at PMFS/Simulations.cpp.
# The maintained implementation is internal/Simulations.cpp; compiling both
# creates an ABI/signature conflict and makes a build depend on local debris.
list(FILTER SOURCES EXCLUDE REGEX ".*/PMFS/Simulations\\.cpp$")

find_package(gmrf_msgs REQUIRED)

# Create the library
add_library(PMFS ${SOURCES})

# Link ament dependencies
ament_target_dependencies(PMFS
    ${COMMON_AMENT_DEPENDENCIES}
    gmrf_msgs
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
