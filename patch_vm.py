import paramiko
import time

# Connect to VM
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.111.128', username='zyc', password='123456')

# Read the file
stdin, stdout, stderr = client.exec_command('cat /home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp')
content = stdout.read().decode('utf-8')

# 1. Add eta_fixed_ parameter in constructor
old_line = "    posterior3d_.arrival_rate_alphaw_ = getParam<float>(\"opgsl.event_driven.alpha_w\", 0.5f);"
new_line = old_line + "\n    posterior3d_.eta_fixed_ = getParam<float>(\"opgsl.event_driven.eta_fixed\", -1.0f);"

if old_line in content and "eta_fixed_" not in content:
    content = content.replace(old_line, new_line)
    print("Added eta_fixed_ parameter to constructor")
else:
    print("Parameter already exists or constructor line not found")

# 2. Modify binaryEventUpdate to use fixed eta when specified
old_eta_code = """    float eta;
    if (detected) {
        eta = std::clamp(-std::log(phi_map), 0.05f, 1.0f);
    } else {
        eta = std::clamp(-std::log(1.0f - phi_map), 0.05f, 1.0f);
    }"""

new_eta_code = """    float eta;
    if (eta_fixed_ > 0.0f) {
        eta = eta_fixed_;
    } else {
        if (detected) {
            eta = std::clamp(-std::log(phi_map), 0.05f, 1.0f);
        } else {
            eta = std::clamp(-std::log(1.0f - phi_map), 0.05f, 1.0f);
        }
    }"""

if old_eta_code in content:
    content = content.replace(old_eta_code, new_eta_code)
    print("Modified binaryEventUpdate to support fixed eta")
else:
    print("WARNING: eta code pattern not found, checking alternatives...")
    # Try to find the eta code with different formatting
    if "eta_fixed_" in content:
        print("eta_fixed_ already in code")
    else:
        print("Could not find eta code to modify")

# 3. Add eta_fixed_ member variable in hpp
stdin2, stdout2, stderr2 = client.exec_command('cat /home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp')
hpp = stdout2.read().decode('utf-8')

if "float eta_fixed_" not in hpp:
    # Find the class definition and add the member
    old_member = "    bool use_event_driven_;"
    new_member = old_member + "\n    float eta_fixed_ = -1.0f;"
    if old_member in hpp:
        hpp = hpp.replace(old_member, new_member)
        print("Added eta_fixed_ member to hpp")
    
    # Write hpp
    sftp = client.open_sftp()
    with sftp.open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp', 'w') as f:
        f.write(hpp)
    sftp.close()
else:
    print("eta_fixed_ already in hpp")

# Write cpp
sftp = client.open_sftp()
with sftp.open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(content)
sftp.close()
print("Files written")

# Build
stdin3, stdout3, stderr3 = client.exec_command('cd /home/zyc/gsl_ws && source /opt/ros/humble/setup.bash && colcon build --packages-select gsl_server 2>&1')
build_out = stdout3.read().decode('utf-8')
print("Build output:")
print(build_out[-500:] if len(build_out) > 500 else build_out)

client.close()
