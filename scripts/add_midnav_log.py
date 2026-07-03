path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp"
with open(path) as f:
    content = f.read()

old_impl = """    void MovingStatePMFS::updateWranfMidNavigation()
    {
        if (!wranfSupervisor_ || !wranfSupervisor_->config().enabled) return;
        if (!pmfs) return;

        uav_gsl_wranf::Input win;"""

new_impl = """    void MovingStatePMFS::updateWranfMidNavigation()
    {
        if (!wranfSupervisor_ || !wranfSupervisor_->config().enabled) return;
        if (!pmfs) return;

        static int midnav_count = 0;
        midnav_count++;
        if (midnav_count <= 20 || midnav_count % 50 == 0) {
            GSL_INFO("[WRANF-MIDNAV] step={} conc={:.4f} wind={:.4f} dir={:.2f}",
                     midnav_count, pmfs->last_concentration, pmfs->last_windSpeed, pmfs->last_windDirection);
        }

        uav_gsl_wranf::Input win;"""

if old_impl in content:
    content = content.replace(old_impl, new_impl)
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added midnav logging")
else:
    print("ERROR: Pattern not found")
