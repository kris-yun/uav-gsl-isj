#pragma once

#if ENABLE_PLUME_TRACKING
    #define SURGE_CAST_NAME "SurgeCast"
    #define SURGE_SPIRAL_NAME "SurgeSpiral"
    #include <gsl_server/algorithms/PlumeTracking/SurgeCast/SurgeCast.hpp>
    #include <gsl_server/algorithms/PlumeTracking/SurgeSpiral/SurgeSpiral.hpp>
#else
    #define SURGE_CAST_NAME "(NOT COMPILED) SurgeCast"
    #define SURGE_SPIRAL_NAME "(NOT COMPILED) SurgeSpiral"
#endif


#if ENABLE_SPIRAL
    #define SPIRAL_NAME "Spiral"
    #include <gsl_server/algorithms/Spiral/Spiral.hpp>
#else
    #define SPIRAL_NAME "(NOT COMPILED) Spiral"
#endif


#if ENABLE_PARTICLE_FILTER
    #define PARTICLE_FILTER_NAME "ParticleFilter"
    #include <gsl_server/algorithms/ParticleFilter/ParticleFilter.hpp>
#else
    #define PARTICLE_FILTER_NAME "(NOT COMPILED) ParticleFilter"
#endif


#if ENABLE_GrGSL
    #define GRGSL_NAME "GrGSL"
    #include <gsl_server/algorithms/GrGSL/GrGSL.hpp>
#else
    #define GRGSL_NAME "(NOT COMPILED) GrGSL"
#endif


#if ENABLE_PMFS
    #define PMFS_NAME "PMFS"
    #include <gsl_server/algorithms/PMFS/PMFS.hpp>
#else
    #define PMFS_NAME "(NOT COMPILED) PMFS"
#endif


#if ENABLE_SEMANTIC_PMFS
    #define SEMANTIC_PMFS_NAME "SemanticPMFS"
    #include <gsl_server/algorithms/Semantics/SemanticPMFS/SemanticPMFS.hpp>
#else
    #define SEMANTIC_PMFS_NAME "(NOT COMPILED) SemanticPMFS"
#endif


#if ENABLE_SEMANTIC_GrGSL
    #define SEMANTIC_GrGSL_NAME "SemanticGrGSL"
    #include <gsl_server/algorithms/Semantics/SemanticGrGSL/SemanticGrGSL.hpp>
#else
    #define SEMANTIC_GrGSL_NAME "(NOT COMPILED) SemanticGrGSL"
#endif

#if ENABLE_OPGSL
    #define OPGSL_NAME "OPGSL"
    #include <gsl_server/algorithms/OPGSL/OPGSL.hpp>
#else
    #define OPGSL_NAME "(NOT COMPILED) OPGSL"
#endif

#if ENABLE_OPGSL_SCIENTIFIC_V31
    #define OPGSL_SCIENTIFIC_V31_NAME "OPGSL_SCIENTIFIC_V31"
    #include <gsl_server/algorithms/OPGSLScientificV31/OPGSLScientificV31.hpp>
#else
    #define OPGSL_SCIENTIFIC_V31_NAME "(NOT COMPILED) OPGSL_SCIENTIFIC_V31"
#endif

#if ENABLE_OPGSL_SCIM_V1
    #define OPGSL_SCIM_V1_NAME "OPGSL_SCIM_V1"
    #include <gsl_server/algorithms/OPGSLSCIMV1/OPGSLSCIMV1.hpp>
#else
    #define OPGSL_SCIM_V1_NAME "(NOT COMPILED) OPGSL_SCIM_V1"
#endif
