filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/PMFS/PMFS.cpp"
with open(filepath) as f:
    content = f.read()

old = '''        // Update the wind estimations
        //  ------------------------------
        PMFSLib::EstimateWind(settings.simulation.useWindGroundTruth,
                              Grid2D<Vector2>(estimatedWindVectors, occupancy, gridMetadata),
                              node,
                              pubs.gmrfWind
                                  IF_GADEN(, pubs.groundTruthWind));'''

new = '''        // Update the wind estimations
        //  ------------------------------
        PMFSLib::EstimateWind(settings.simulation.useWindGroundTruth,
                              Grid2D<Vector2>(estimatedWindVectors, occupancy, gridMetadata),
                              node,
                              pubs.gmrfWind
                                  IF_GADEN(, pubs.groundTruthWind));
        
        // Fallback: if wind service failed, fill grid with current wind sensor reading
        // This allows PMFS to run without GMRF/GADEN wind estimation service
        {
            float wx = windSpeed * std::cos(windDirection);
            float wy = windSpeed * std::sin(windDirection);
            bool need_fallback = true;
            // Check if wind grid is already filled (non-zero)
            for (size_t i = 0; i < estimatedWindVectors.size(); i++) {
                if (estimatedWindVectors[i].x != 0.0f || estimatedWindVectors[i].y != 0.0f) {
                    need_fallback = false;
                    break;
                }
            }
            if (need_fallback && windSpeed > 0.01f) {
                GSL_WARN("PMFS: Wind service unavailable, using uniform wind field ({:.2f},{:.2f})", wx, wy);
                for (size_t i = 0; i < estimatedWindVectors.size(); i++) {
                    estimatedWindVectors[i] = Vector2(wx, wy);
                }
            }
        }'''

content = content.replace(old, new, 1)

with open(filepath, "w") as f:
    f.write(content)
print("Added uniform wind fallback")
