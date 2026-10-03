# R1B runtime audit

ROS2 Humble / native GADEN core3.0, unchanged existing PF_DEI_V3_GADEN_BUILD libgaden.so; native CLI adapter uses official ParseOpenFoamVectorCloud, RunningSimulation, SampleWind and SampleConcentration. Exact adapter/lib SHA in before/after files, equality asserted. Isolated build Git links are historically broken, so no unsupported exact source commit is asserted. No package/kernel/House change.

18 regular3D wind CSVs, 99,200 cells each,80x40x31 at5m. Six physically divergence-consistent full fronts; six uniform and six x-invariant profile controls. Front90/120/150m; amplitudes are unchanged original F1/F2 values, not re-normalized after front translation. Original XF120 full field bytes preserved. Native random100-point parity and all1200 actual trajectory wind queries per field checked. Ground and outlet geometry identical to prior experiments.

Methane,298K/1atm,120s warmup,300s trajectory query,1Hz,filament release5/10/20,noise/sigma/growth unchanged. Seeds32001..32008,OMP1 per native process,4 independent processes. New-seed byte repeatability checked. Native observation output still has10/30/60/100m for unchanged adapter; only10m primary and30m secondary analyzed. This is native filament physics including methane buoyancy, not thermally driven CFD/LES.
