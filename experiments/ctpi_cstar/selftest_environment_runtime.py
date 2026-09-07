"""Synthetic destructive regressions; no House data, training or simulator."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

import numpy as np

from experiments.ctpi_cstar.environment_runtime import (
    Grid3D, NumericWindReader, decode_wind, legacy_header, numeric_sequence,
    sha256, validate_clock_sensor, verify_bindings, verify_qualified_helper,
)

ROOT = Path(__file__).resolve().parents[2]


class EnvironmentRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cstar-env-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.grid = Grid3D((-1., -2., -.5), (1., 0., 1.5), (2, 2, 2), 1.)

    def header(self, index=0, float_prefix=False):
        raw = bytearray(136)
        struct.pack_into("<i", raw, 0, 1)
        for i, value in enumerate(self.grid.minimum + self.grid.maximum):
            struct.pack_into("<f" if float_prefix else "<d", raw, 4 + 8*i, value)
        struct.pack_into("<3i", raw, 52, *self.grid.dimensions)
        struct.pack_into("<d", raw, 64, self.grid.cell_size)
        struct.pack_into("<i", raw, 132, index)
        return raw

    def save_header(self, raw):
        path = self.root / "iteration_0"
        path.write_bytes(zlib.compress(bytes(raw) + b"FILAMENT_BODY_MUST_NOT_BE_DECODED" * 1000))
        return path

    def test_numeric_order_0_1_10(self):
        for i in range(11):
            (self.root / f"wind_iteration_{i}").touch()
        self.assertEqual([p.name for p in numeric_sequence(self.root, "wind_iteration_")],
                         [f"wind_iteration_{i}" for i in range(11)])

    def test_gap_rejected(self):
        for i in (0, 2):
            (self.root / f"wind_iteration_{i}").touch()
        with self.assertRaisesRegex(ValueError, "CONTIGUOUS"):
            numeric_sequence(self.root, "wind_iteration_")

    def test_alias_junk_negative_rejected(self):
        for suffix in ("01", "1junk", "-1", "", "1.0"):
            with self.subTest(suffix=suffix):
                p = self.root / ("wind_iteration_" + suffix)
                p.touch()
                with self.assertRaisesRegex(ValueError, "CANONICAL"):
                    numeric_sequence(self.root, "wind_iteration_")
                p.unlink()

    def test_empty_sequence_rejected(self):
        with self.assertRaisesRegex(ValueError, "EMPTY"):
            numeric_sequence(self.root, "wind_iteration_")

    def test_directory_not_file(self):
        (self.root / "wind_iteration_0").mkdir()
        with self.assertRaisesRegex(ValueError, "NOT_FILE"):
            numeric_sequence(self.root, "wind_iteration_")

    def test_wind_layouts_agree(self):
        values = np.arange(24, dtype=np.float32).reshape(8, 3)
        a, b = self.root / "legacy", self.root / "modern"
        a.write_bytes(values.T.astype("<f8").tobytes())
        b.write_bytes(struct.pack("<2i", 2, 0) + values.astype("<f4").tobytes())
        np.testing.assert_array_equal(decode_wind(a, 8)[0], decode_wind(b, 8)[0])
        self.assertEqual(decode_wind(a, 8)[1]["vector_sha256"], decode_wind(b, 8)[1]["vector_sha256"])

    def test_bad_layout_nonfinite(self):
        path = self.root / "bad"
        path.write_bytes(b"invalid")
        with self.assertRaisesRegex(ValueError, "LAYOUT"):
            decode_wind(path, 8)
        path.write_bytes(np.full((3, 8), np.nan, dtype="<f8").tobytes())
        with self.assertRaisesRegex(ValueError, "NONFINITE"):
            decode_wind(path, 8)

    def test_coordinate_encodings(self):
        for prefix in (False, True):
            with self.subTest(prefix=prefix):
                result = legacy_header(self.save_header(self.header(6, prefix)), self.grid)
                self.assertEqual(result["wind_index"], 6)
                self.assertEqual(result["sample_grid"], self.grid)

    def test_unmatched_coordinate_rejected(self):
        raw = self.header()
        struct.pack_into("<d", raw, 4, 93.)
        with self.assertRaisesRegex(ValueError, "COORDINATES"):
            legacy_header(self.save_header(raw), self.grid)

    def test_bad_header_grid_size_version_index(self):
        for offset, fmt, value, code in ((0, "i", 9, "UNSUPPORTED"), (52, "i", 3, "DIMENSIONS"),
                                        (64, "d", .2, "CELL_SIZE"), (132, "i", -1, "NEGATIVE")):
            with self.subTest(code=code):
                raw = self.header()
                struct.pack_into("<" + fmt, raw, offset, value)
                with self.assertRaisesRegex(ValueError, code):
                    legacy_header(self.save_header(raw), self.grid)

    def test_truncated_header(self):
        with self.assertRaisesRegex(ValueError, "TRUNCATED"):
            legacy_header(self._truncated(), self.grid)

    def _truncated(self):
        path = self.root / "short"
        path.write_bytes(zlib.compress(b"short"))
        return path

    def test_axis_order_and_boundaries(self):
        self.assertEqual(self.grid.flat_index((-.5, -1.5, 0)), 0)
        self.assertEqual(self.grid.flat_index((.5, -.5, 1)), 7)
        self.assertEqual(self.grid.flat_index((-.5, -.5, 0)), 2)
        for point in ((1, -1.5, 0), (-1.1, -1.5, 0), (float("nan"), 0, 0)):
            with self.assertRaises(ValueError):
                self.grid.flat_index(point)

    def test_reader_checks_actual_vector_not_self_reported_index(self):
        occ = self.root / "OccupancyGrid3D.csv"
        occ.write_text("#env_min(m) -1 -2 -0.5\n#env_max(m) 1 0 1.5\n#num_cells 2 2 2\n#cell_size 1\n")
        (self.root / "wind").mkdir()
        for index in range(11):
            (self.root / "wind" / f"wind_iteration_{index}").write_bytes(
                np.full((3, 8), index, dtype="<f8").tobytes())
        self.save_header(self.header(6))
        reader = NumericWindReader(self.root, occ)
        self.assertEqual(reader.verify_reply(0, (-.5, -1.5, 0), "OK 0 6 6 6 6"), 0)
        for reply, code in (("OK 0 5 5 5 6", "WRONG_PHYSICAL"), ("OK 0 6 6 6 5", "HEADER_WIND"),
                            ("OK nan 6 6 6 6", "NONFINITE"), ("ERR", "RESPONSE")):
            with self.assertRaisesRegex(ValueError, code):
                reader.verify_reply(0, (-.5, -1.5, 0), reply)
        with self.assertRaisesRegex(ValueError, "RANGE"):
            reader.vectors(11)

    def frozen_clock_sensor(self):
        clock = json.loads((ROOT / "experiments/ctpi_cstar/CSTAR_ENVIRONMENT_CLOCK_V1.json").read_text())
        sensor = json.loads((ROOT / "evidence/cstar_environment_20260906/probes_v1/H01/sensor_manifest.json").read_text())
        return clock, sensor

    def test_actual_clock_is_explicitly_not_physical_time(self):
        clock, sensor = self.frozen_clock_sensor()
        self.assertFalse(validate_clock_sensor(clock, sensor)["is_physical_time_replay"])

    def test_clock_and_oracle_fail_closed(self):
        clock, sensor = self.frozen_clock_sensor()
        for key, value in (("frame_id", "odom"), ("stamp_zero_is_bootstrap", False),
                           ("sensor_dt_s", .5), ("field_replay_speed_ratio", 1), ("seed", 11),
                           ("sensor_internal_state_available_to_model", True)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_clock_sensor(clock | {key: value}, sensor)

    def test_unresolved_sensor_alias_and_invalid_values(self):
        clock, original = self.frozen_clock_sensor()
        for key, value in (("mode", "dynamic"), ("tau_rise_s", -1), ("noise_std_ppm", float("nan"))):
            sensor = copy.deepcopy(original)
            sensor["sensor"]["config"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_clock_sensor(clock, sensor)

    def test_changed_file_invalidates_binding(self):
        path = self.root / "file"
        path.write_bytes(b"correct")
        bindings = [{"path": str(path), "sha256": sha256(path)}]
        verify_bindings(bindings)
        path.write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "STALE"):
            verify_bindings(bindings)

    def test_legacy_binary_rejected_before_launch(self):
        binary, source = self.root / "binary", self.root / "source"
        binary.write_bytes(b"numeric")
        source.write_bytes(b"source")
        attestation = {"contract": "CSTAR_NUMERIC_WIND_RUNTIME_CORRECTION_V1", "pass": True,
                       "live_frames": 8, "corrected_helper_sha256": sha256(binary),
                       "corrected_helper_source_sha256": sha256(source)}
        verify_qualified_helper(binary, source, attestation)
        binary.write_bytes(b"lexical")
        with self.assertRaisesRegex(ValueError, "UNQUALIFIED_HELPER_BINARY"):
            verify_qualified_helper(binary, source, attestation)


if __name__ == "__main__":
    unittest.main(verbosity=2)
