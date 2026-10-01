"""Isolated rebuild of archived Native ExpectedValue, never a ROS rebuild."""
import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

from prepare_features import sha, write_json


def recover(root, out):
    archive=root/"freeze/exact_b24_source.tar.gz"
    assert sha(archive)=="771b21e6001e4c175a61f419de472579d77e728a5c8a9d794ac288fa159b0b75"
    target=out/"endpoint_source"
    target.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive) as t:
        for m in t.getmembers():
            if m.isfile() and any(m.name.startswith(p) for p in ("ros2_package/src/","ros2_package/tools/","ros2_package/third_party/")):
                dst=target/m.name
                assert dst.resolve().is_relative_to(target.resolve())
                dst.parent.mkdir(parents=True,exist_ok=True)
                dst.write_bytes(t.extractfile(m).read())
    base=target/"ros2_package"
    original=base/"tools/tnqc_expected_value_native.cpp"
    math_source=base/"src/gsl_server/algorithms/Common/Utils/Math.cpp"
    text=original.read_text()
    # Readout addition only: both functions are called from original Math.cpp.
    anchor='<< ",\\\"pmfs_top5_error_m\\\":" << error'
    assert text.count(anchor)==1
    extended=out/"native_endpoint_with_variance.cpp"
    extended.write_text(text.replace(anchor,anchor+'\n              << ",\\\"variance_m2\\\":" << GSL::Utils::Variance(grid)'))
    includes=[base/"src",base/"third_party/DDA/include",base/"third_party/DDA/third_party/glm"]+list(Path("/opt/ros/humble/include").iterdir())
    commands=[]
    for tool,exe in ((original,"tnqc_expected_value_native"),(extended,"native_endpoint_with_variance")):
        cmd=["g++","-std=c++20","-O3","-fopenmp","-ffunction-sections","-fdata-sections"]+[f"-I{p}" for p in includes]+[str(tool),str(math_source),"-Wl,--gc-sections","-o",str(out/exe)]
        run=subprocess.run(cmd,capture_output=True,text=True)
        (out/f"{exe}_build.log").write_text(run.stdout+run.stderr)
        assert run.returncode==0,run.stderr
        commands.append({"command":cmd,"binary_sha256":sha(out/exe)})
    write_json(out/"ENDPOINT_RECOVERY_PROVENANCE.json",{"status":"REBUILT_NOT_ORIGINAL_BINARY; parity must pass before evaluation","source_archive_sha256":sha(archive),"original_tool_sha256":sha(original),"math_cpp_sha256":sha(math_source),"readout_extension_sha256":sha(extended),"compiler":subprocess.check_output(["g++","--version"],text=True),"commands":commands,"protected_ros_build_install_modified":False})


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();recover(a.root,a.out)
