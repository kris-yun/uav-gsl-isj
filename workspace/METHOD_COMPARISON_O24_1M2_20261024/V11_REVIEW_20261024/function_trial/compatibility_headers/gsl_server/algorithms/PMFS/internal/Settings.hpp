#pragma once
namespace GSL::PMFS_internal { struct SimulationSettings { bool useWindGroundTruth;int maxRegionSize,stepsBetweenSourceUpdates;double sourceDiscriminationPower,refineFraction;int maxWarmupIterations,iterationsToRecord;double deltaTime,noiseSTDev; }; }
