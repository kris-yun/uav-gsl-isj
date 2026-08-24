add_library(OPGSL_SCIM_V1
  ${CMAKE_CURRENT_LIST_DIR}/OPGSLSCIMV1.cpp
  ${CMAKE_CURRENT_LIST_DIR}/../../../SCIMCore.cpp
)
ament_target_dependencies(OPGSL_SCIM_V1 ${COMMON_AMENT_DEPENDENCIES})
target_link_libraries(OPGSL_SCIM_V1 Eigen3::Eigen fmt GSL_common)
target_compile_definitions(OPGSL_SCIM_V1 PRIVATE ENABLE_OPGSL_SCIM_V1=1)
target_compile_definitions(gsl_actionserver_node PRIVATE ENABLE_OPGSL_SCIM_V1=1)
target_link_libraries(gsl_actionserver_node OPGSL_SCIM_V1)
