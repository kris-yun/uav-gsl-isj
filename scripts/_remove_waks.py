with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFSLib.cpp', 'r') as f:
    content = f.read()

old = '''        // WAKS: Wind-Adaptive Kernel Scaling
        // In low-wind conditions, use minimum elongation to maintain directionality
        // Cross-domain: adaptive kernel methods from image processing
        static const double waks_min_wind = 0.05;  // minimum effective wind speed
        static const double waks_min_stretch = 0.3; // minimum stretch factor
        double effective_wind = std::max(windSpeed, waks_min_wind);
        double effective_stretch = std::max(settings.kernelStretchConstant, waks_min_stretch);
        
        double kernel_rotation_wind = -angles::normalize_angle(downwindDirection + M_PI / 2);
        HitProbKernel kernel =
            {
                .angle = kernel_rotation_wind,
                .sigma = Vector2(
                    settings.kernelSigma / (1 + effective_stretch * effective_wind / settings.kernelSigma), // semi-minor ellipse axis
                    settings.kernelSigma + effective_stretch * effective_wind                               // semi-major axis
                    ),
                .valueAt1 = (hit ? 0.6f : 0.1f)};'''

new = '''        double kernel_rotation_wind = -angles::normalize_angle(downwindDirection + M_PI / 2);
        HitProbKernel kernel =
            {
                .angle = kernel_rotation_wind,
                .sigma = Vector2(
                    settings.kernelSigma / (1 + settings.kernelStretchConstant * windSpeed / settings.kernelSigma), // semi-minor ellipse axis
                    settings.kernelSigma + settings.kernelStretchConstant * windSpeed                               // semi-major axis
                    ),
                .valueAt1 = (hit ? 0.6f : 0.1f)};'''

content = content.replace(old, new)
with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFSLib.cpp', 'w') as f:
    f.write(content)
print('WAKS removed')
