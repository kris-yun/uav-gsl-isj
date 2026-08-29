#!/usr/bin/env python3
"""Apply/check the read-only PF-SNRE GADEN playback-iteration instrumentation.

This patch changes no gas/wind physics and reads no source truth.  It adds one
transient-local std_msgs/UInt64 publisher to gaden_player so a late-subscribing
PF-SNRE runtime can know the exact iteration_N currently sampled by /odor_value.

The patch is intentionally narrow and fail-fast.  It never fuzzy-patches an
unknown gaden_player source tree.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

MARKER = "PF_SNRE_READONLY_CURRENT_ITERATION_V1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_text(text: str) -> str:
    if MARKER in text:
        return text

    include_anchor = '#include <gaden_common/Visualization.hpp>\n'
    include_repl = include_anchor + '#include <std_msgs/msg/u_int64.hpp> // ' + MARKER + '\n'
    if text.count(include_anchor) != 1:
        raise RuntimeError("unexpected gaden_player include anchor; refuse fuzzy patch")
    text = text.replace(include_anchor, include_repl, 1)

    service_anchor = '''    auto serviceWind = create_service<gaden_msgs::srv::WindPosition>(\n        "wind_value", std::bind(&Player::GetWindValue_srv, this, std::placeholders::_1, std::placeholders::_2));\n\n    // Loop\n'''
    service_repl = '''    auto serviceWind = create_service<gaden_msgs::srv::WindPosition>(\n        "wind_value", std::bind(&Player::GetWindValue_srv, this, std::placeholders::_1, std::placeholders::_2));\n\n    // Read-only instrumentation for PF-SNRE.  Transient-local QoS is required\n    // so a GSL node that subscribes after player startup immediately receives\n    // the currently active iteration instead of guessing a clock offset.\n    auto iterationPub = create_publisher<std_msgs::msg::UInt64>(\n        "current_iteration", rclcpp::QoS(1).reliable().transient_local());\n    std::size_t pfSnreCurrentIteration = playbackMetadata.params.at(0).startIteration;\n    const auto publishCurrentIteration = [&]()\n    {\n        std_msgs::msg::UInt64 msg;\n        msg.data = static_cast<uint64_t>(pfSnreCurrentIteration);\n        iterationPub->publish(msg);\n    };\n\n    // Loop\n'''
    if text.count(service_anchor) != 1:
        raise RuntimeError("unexpected gaden_player service anchor; refuse fuzzy patch")
    text = text.replace(service_anchor, service_repl, 1)

    first_anchor = '''    // load the first timestep immediately\n    Scene->AdvanceTimestep();\n\n    while (rclcpp::ok())\n'''
    first_repl = '''    // load the first timestep immediately\n    Scene->AdvanceTimestep();\n    publishCurrentIteration();\n\n    while (rclcpp::ok())\n'''
    if text.count(first_anchor) != 1:
        raise RuntimeError("unexpected first-timestep anchor; refuse fuzzy patch")
    text = text.replace(first_anchor, first_repl, 1)

    advance_anchor = '''            // Read Gas and Wind data from log_files\n            Scene->AdvanceTimestep();\n\n            displayCurrentGasDistribution(); // Rviz visualization\n'''
    advance_repl = '''            // Read Gas and Wind data from log_files.  Mirror the exact\n            // PlaybackSimulation loop rule before publishing the newly active\n            // iteration.  No concentration/wind state is modified here.\n            if (playbackMetadata.loop.loop && pfSnreCurrentIteration >= playbackMetadata.loop.to)\n                pfSnreCurrentIteration = playbackMetadata.loop.from;\n            else\n                ++pfSnreCurrentIteration;\n            Scene->AdvanceTimestep();\n            publishCurrentIteration();\n\n            displayCurrentGasDistribution(); // Rviz visualization\n'''
    if text.count(advance_anchor) != 1:
        raise RuntimeError("unexpected advance anchor; refuse fuzzy patch")
    text = text.replace(advance_anchor, advance_repl, 1)
    return text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gaden-root", type=Path, required=True,
                    help="GADEN source root containing gaden_player/src/simulation_player.cpp")
    ap.add_argument("--check", action="store_true", help="verify instrumentation without modifying files")
    args = ap.parse_args()

    cpp = args.gaden_root / "gaden_player" / "src" / "simulation_player.cpp"
    pkg = args.gaden_root / "gaden_player" / "package.xml"
    if not cpp.is_file() or not pkg.is_file():
        raise SystemExit("STOP_PF_SNRE_GADEN_PLAYER_SOURCE_NOT_FOUND")
    pkg_text = pkg.read_text(encoding="utf-8")
    if "<depend>std_msgs</depend>" not in pkg_text:
        raise SystemExit("STOP_PF_SNRE_GADEN_PLAYER_STD_MSGS_DEPENDENCY_MISSING")

    old = cpp.read_text(encoding="utf-8")
    if args.check:
        if MARKER not in old or '"current_iteration", rclcpp::QoS(1).reliable().transient_local()' not in old:
            raise SystemExit("STOP_PF_SNRE_GADEN_ITERATION_TOPIC_NOT_PATCHED")
        print(f"PF_SNRE_GADEN_ITERATION_TOPIC_PATCHED sha256={sha256(cpp)}")
        return

    new = patch_text(old)
    if new != old:
        cpp.write_text(new, encoding="utf-8")
    print(f"PF_SNRE_GADEN_ITERATION_TOPIC_READY sha256={sha256(cpp)} changed={int(new != old)}")


if __name__ == "__main__":
    main()
