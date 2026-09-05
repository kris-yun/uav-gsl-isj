"""Small offline regression checks for diagnostic arithmetic and signatures."""
from ctpi_r4_failure_attribution import auc_between, compressed_xy


def main():
    constant = [{"t": 10., "error_m": 3.}, {"t": 230., "error_m": 3.}]
    assert auc_between(constant, 0, 240) == 720.
    assert auc_between(constant, 60, 120) == 180.
    linear = [{"t": 0., "error_m": 0.}, {"t": 240., "error_m": 240.}]
    assert auc_between(linear, 60, 120) == 5400.
    assert sum(auc_between(linear, t, t+60) for t in (0,60,120,180)) == 28800.
    duplicate = [{"t": 0., "error_m": 8.}, {"t": 0., "error_m": 2.}, {"t": 240., "error_m": 2.}]
    assert auc_between(duplicate, 0, 240) == 480.
    a = [{"t": 1., "x": 2., "y": 3.}, {"t": 2., "x": 2., "y": 3.}, {"t": 3., "x": 4., "y": 5.}]
    b = [{"t": 9., "x": 2., "y": 3.}, {"t": 10., "x": 4., "y": 5.}]
    assert compressed_xy(a) == compressed_xy(b)
    print("CTPI_R4_ATTRIBUTION_SELFTEST=PASS")


if __name__ == "__main__":
    main()
