# Mechanism finding

The official PMFS evidence path has two stages:

1. Every raw hit/miss observation is propagated from the robot cell through an anisotropic kernel and then through the navigation map (`EstimateHitProbabilities` -> `PropagateProbabilities`). This creates a spatially correlated hit-probability/confidence field.
2. `sourceProbFromMaps()` then loops over every free cell and multiplies a per-cell agreement factor:
   `1 - confidence_i * sourceDiscriminationPower * |measured_i - simulated_i|`.

Thus correlated descendants of the same physical measurement are re-used as if they were independent factors.

For the frozen R1 House01/seed0 first source update:
- raw events = 20;
- unique robot sites = 4;
- hits = 1, misses = 19;
- free cells = 626;
- cells with confidence > 0 = 276;
- cells with confidence > 0.01 = 130;
- cells with confidence > 0.1 = 84.

This is only a mechanism hypothesis. It must be tested on the exact same frozen Native forward maps so the forward model cannot explain any ranking change.

The prior persistent-source experiment is frozen `MECHANISM_NULL_OR_ADVERSE` and must not be combined with this test.
