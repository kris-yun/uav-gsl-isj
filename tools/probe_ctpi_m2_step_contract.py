"""Synthetic counterexample for the frozen M2 step; no House/bank data read."""
import json
import numpy as np
from ctpi_g2_m2_crosshouse_field_gate import advance, CELL_SIZE_M, TIME_STEP_S, DIFFUSIVITY_M2_S


def main():
    concentration = np.zeros((9, 9), dtype=np.float64)
    concentration[4, 4] = 1.0
    free = np.ones((9, 9), dtype=bool)
    u = np.full((9, 9), 0.15)
    v = np.full((9, 9), 0.15)
    # Interior pulse and distinct interior source: zero boundary flux this step.
    result = advance(concentration, u, v, (2, 2), free)
    expected = concentration.sum() + TIME_STEP_S
    actual = result.sum()
    coefficient = TIME_STEP_S * ((0.15+0.15)/CELL_SIZE_M + 4*DIFFUSIVITY_M2_S/CELL_SIZE_M**2)
    assert np.isclose(actual, 2.4444444444444446)
    assert np.isclose(actual-expected, coefficient-1.)
    print(json.dumps(dict(
        status="COUNTEREXAMPLE_REPRODUCED_NOT_HOUSE_VERDICT",
        grid_shape=[9,9], wind_u_m_s=0.15, wind_v_m_s=0.15,
        dt_s=TIME_STEP_S, dx_m=CELL_SIZE_M, diffusivity_m2_s=DIFFUSIVITY_M2_S,
        input_sum=float(concentration.sum()), added_source=TIME_STEP_S,
        expected_sum=float(expected), actual_sum=float(actual),
        excess_sum=float(actual-expected),
        interpretation="Negative central coefficient plus zero clipping increases mass on this synthetic input. Does not establish prevalence in prior House runs."
    ), indent=2))


if __name__ == "__main__":
    main()
