import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.128', username='zyc')

package_xml = '''<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>gaden_msgs</name>
  <version>0.0.1</version>
  <description>Minimal gaden_msgs for GSL oracle wind</description>
  <maintainer email="test@test.com">user</maintainer>
  <license>MIT</license>
  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>rosidl_default_generators</buildtool_depend>
  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>
</package>
'''

stdin, stdout, stderr = ssh.exec_command(f"cat > /home/zyc/ros2_ws/src/gaden_msgs/package.xml << 'XMLEOF'\n{package_xml}XMLEOF")
print(stdout.read().decode())
print(stderr.read().decode())

stdin, stdout, stderr = ssh.exec_command("source /opt/ros/humble/setup.bash && cd ~/ros2_ws && colcon build --packages-select gaden_msgs 2>&1 | tail -5")
print(stdout.read().decode())
ssh.close()
