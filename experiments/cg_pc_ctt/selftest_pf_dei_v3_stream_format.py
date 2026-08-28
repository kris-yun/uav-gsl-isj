#!/usr/bin/env python3

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from pf_dei_v3_stream_format import read_multistream, read_wind_multistream, write_multistream_for_test


def expect_failure(path: Path, marker: str) -> None:
    try:
        read_multistream(path)
    except ValueError as exc:
        assert str(exc) == marker, (exc, marker)
    else:
        raise AssertionError(f"expected {marker}")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        valid = root / "valid.bin"
        expected = [
            np.array([0.0, 1.25, 3.5], dtype=np.float32),
            np.array([9.0, 2.0], dtype=np.float32),
        ]
        write_multistream_for_test(valid, expected)
        actual = read_multistream(valid)
        assert len(actual) == len(expected)
        for lhs, rhs in zip(actual, expected, strict=True):
            assert lhs.dtype == np.dtype("float32")
            assert np.array_equal(lhs, rhs)

        bad_magic = root / "bad_magic.bin"
        bad_magic.write_bytes(b"BADMAGIC" + valid.read_bytes()[8:])
        expect_failure(bad_magic, "PF_DEI_V3_STREAM_BAD_MAGIC")

        truncated = root / "truncated.bin"
        truncated.write_bytes(valid.read_bytes()[:-1])
        expect_failure(truncated, "PF_DEI_V3_STREAM_SIZE_MISMATCH")

        trailing = root / "trailing.bin"
        trailing.write_bytes(valid.read_bytes() + b"x")
        expect_failure(trailing, "PF_DEI_V3_STREAM_SIZE_MISMATCH")

        invalid = root / "invalid.bin"
        write_multistream_for_test(invalid, [np.array([0.0, np.nan], dtype=np.float32)])
        expect_failure(invalid, "PF_DEI_V3_STREAM_INVALID_PPM")

        wind_bad = root / "wind_bad.bin"
        wind_bad.write_bytes(b"PFV3WND1" + b"\x01\x00\x00\x00" + b"\x01\x00\x00\x00" + b"\x00" * 8)
        try:
            read_wind_multistream(wind_bad)
        except ValueError as exc:
            assert str(exc) == "PF_DEI_V3_WIND_SIZE_MISMATCH"
        else:
            raise AssertionError("expected PF_DEI_V3_WIND_SIZE_MISMATCH")

    print("PF_DEI_V3_STREAM_FORMAT_SELFTEST PASS")


if __name__ == "__main__":
    main()
