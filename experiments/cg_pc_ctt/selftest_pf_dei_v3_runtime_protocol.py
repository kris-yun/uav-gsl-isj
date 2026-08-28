#!/usr/bin/env python3

import numpy as np

from pf_dei_v3_runtime_server import parse_request, posterior_from_logits


def main() -> int:
    lines = [
        "PFDEI_V3_REQUEST H02 3 3 2",
        "quadtree_0_0_2_2,quadtree_0_2_2_2",
        "0.2,1,2,0.01,0.1,0.2,0,1,1",
        "0.4,1.1,2,0.02,0.1,0.2,0,0,0",
        "0.6,1.2,2,0.03,0.1,0.2,0,0,0",
        "END",
    ]
    request = parse_request(lines)
    assert request.house == "H02" and request.update_id == 3
    assert request.carrier_ids == ("quadtree_0_0_2_2", "quadtree_0_2_2_2")
    assert np.allclose(request.schedule()["dt"], 0.2)
    prior = np.asarray([0.25, 0.75])
    assert np.allclose(posterior_from_logits(prior, np.zeros(2)), prior)
    assert posterior_from_logits(prior, np.asarray([10.0, 0.0]))[0] > 0.99

    bad = list(lines)
    bad[3] = "0.4,1.1,2,-0.02,0.1,0.2,0,0,0"
    try:
        parse_request(bad)
    except ValueError as error:
        assert "NEGATIVE_MEASURED" in str(error)
    else:
        raise AssertionError("negative measured ppm was accepted")
    print("PF_DEI_V3_RUNTIME_PROTOCOL_SELFTEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
