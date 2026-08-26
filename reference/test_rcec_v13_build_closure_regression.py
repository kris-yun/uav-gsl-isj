#!/usr/bin/env python3
"""Regression for the dormant CTT target missed by the original V12 closure."""
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools/close_rcec_v13_build_dependency.py'


def load_tool():
    spec = importlib.util.spec_from_file_location('rcec_v13_build_closure', TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError('could not load build-closure materializer')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    tool = load_tool()
    fixture = '''prefix
# Truth-free physical trace-bank builder for the CTT premise gates. It is not
# installed or launched by ROS and cannot access planner or final-source truth.
add_executable(ctt_trace_bank_builder tools/ctt_trace_bank_builder.cpp)
ament_target_dependencies(ctt_trace_bank_builder
    dependency_one
    dependency_two
)
target_link_libraries(ctt_trace_bank_builder PMFS)
suffix
'''
    closed, count = tool.remove_legacy_ctt_target(fixture)
    assert count == 1
    assert 'ctt_trace_bank_builder' not in closed
    assert closed.startswith('prefix\n')
    assert closed.endswith('suffix\n')
    print('RCEC_V13_CTT_BUILD_CLOSURE_REGRESSION=PASS')


if __name__ == '__main__':
    main()
