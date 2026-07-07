hpp_path = '/home/zyc/ros2_ws/src/GSL/gsl_server/include/gsl_server/wranf/RwgfSupervisor.hpp'
with open(hpp_path, 'r') as f:
    hpp = f.read()
if 'const RwgfConfig& config()' not in hpp:
    hpp = hpp.replace(
        '    RwgfOutput process(const Input& input);',
        '    RwgfOutput process(const Input& input);\n    const RwgfConfig& config() const { return cfg_; }\n    bool enabled() const { return cfg_.enabled; }'
    )
with open(hpp_path, 'w') as f:
    f.write(hpp)
print('done')
