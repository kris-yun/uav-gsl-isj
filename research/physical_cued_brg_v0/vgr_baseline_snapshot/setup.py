from setuptools import setup
import os
from glob import glob

package_name = "vgr_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/params", glob("params/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="zyc",
    maintainer_email="test@test.com",
    description="VGR UAV simulation bridge for GSL baselines",
    license="MIT",
    entry_points={
        "console_scripts": [
            "vgr_sim_node = vgr_bridge.vgr_sim_node:main",
            "gsl_benchmark_runner = vgr_bridge.gsl_benchmark_runner:main",
            "pioe_gsl_node = vgr_bridge.pioe_gsl_node:main",
            "wind_value_server = vgr_bridge.wind_value_server:main",
            "gsl_pilot_runner = vgr_bridge.gsl_pilot_runner:main",
        ],
    },
)
