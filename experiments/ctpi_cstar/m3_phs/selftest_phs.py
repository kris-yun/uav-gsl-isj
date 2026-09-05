from __future__ import annotations

from phs import marginalize_region_laws, decide_from_region_placements


def close(a, b, tol=1e-12):
    assert abs(a - b) <= tol, (a, b)


def main():
    # Two region hypotheses, each with two physical placements, two routes,
    # two future-outcome categories. The geometry quadrature is uniform.
    placement_laws = [
        [
            [[0.5, 0.5], [1.0, 0.0]],
            [[0.5, 0.5], [0.8, 0.2]],
        ],
        [
            [[0.5, 0.5], [0.0, 1.0]],
            [[0.5, 0.5], [0.2, 0.8]],
        ],
    ]
    weights = [[0.5, 0.5], [0.5, 0.5]]
    region = marginalize_region_laws(placement_laws, weights)

    # Route 0 remains identical after correct placement marginalization.
    for source in range(2):
        close(region[source][0][0], 0.5)
        close(region[source][0][1], 0.5)

    # Route 1 remains substantially source-separating; exact mixtures are .9/.1.
    close(region[0][1][0], 0.9)
    close(region[1][1][0], 0.1)

    decision = decide_from_region_placements(
        [0.5, 0.5], placement_laws, weights, [1.0, 20.0]
    )
    assert decision.selected_route == 1
    assert decision.resolution > 0.0

    # Changing only placement quadrature changes the region law but remains normalized.
    skew = marginalize_region_laws(placement_laws, [[0.9, 0.1], [0.9, 0.1]])
    for source in skew:
        for law in source:
            close(sum(law), 1.0)

    print("CSTAR_PHS_SELFTEST PASS")


if __name__ == "__main__":
    main()
