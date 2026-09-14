# TROQL external-dataset search, 2010–2026

Date: 2026-09-14

## Search protocol

Three queries were run across Semantic Scholar, OpenAlex, arXiv, OpenReview,
Crossref, and DBLP using the repository paper-search workflow:

1. `gas source localization public dataset known source multiple wind conditions`
2. `robot olfaction dataset gas dispersion source location repeated experiments`
3. `turbulent gas source localization benchmark dataset wind tunnel`

The raw merged response is preserved in
`paper_search_troql_external_dataset_2010_2026.json`. OpenAlex returned 24 records,
Crossref 24, and arXiv 8; Semantic Scholar was rate-limited, DBLP encountered TLS
errors, and OpenReview returned no records. The arXiv records were semantic false
positives caused mainly by the token “gas”.

## Ranked relevant records and datasets

1. Burgués et al., *Gas distribution mapping and source localization using a 3D
   grid of metal oxide semiconductor sensors* (2019/2020), DOI
   <https://doi.org/10.1016/j.snb.2019.127309>, OpenAlex citations: 42. Public
   Orebro3DSEN data; multiple real source locations and airflow profiles. Selected
   and scored under frozen V1/V2 gates.
2. Ojeda et al., *Robotic Gas Source Localization With Probabilistic Mapping and
   Online Dispersion Simulation* (2024), DOI
   <https://doi.org/10.1109/TRO.2024.3426368>, OpenAlex citations: 26. Closest
   online-PMFS context, but not a fresh external run-level confirmation asset.
3. Ojeda et al., *VGR Dataset: A CFD-based Gas Dispersion Dataset for Mobile
   Robotic Olfaction* (2023), DOI
   <https://doi.org/10.1007/s10846-023-02012-z>, Crossref citations: 7. Large and
   public, but simulated and already adjacent to the project evidence lineage.
4. Burgués et al., *Exploration and localization of a gas source with MOX gas
   sensors on a mobile robot* (2017), DOI
   <https://doi.org/10.1109/ISOEN.2017.7968898>, OpenAlex citations: 16. Relevant
   real-sensor source-localization study; no newly identified factorial raw asset.
5. Wada et al., *Collecting a Database for Studying Gas Distribution Mapping and
   Gas Source Localization with Mobile Robots* (2010), DOI
   <https://doi.org/10.1299/jsmeicam.2010.5.183>, OpenAlex citations: 20. The paper
   describes controlled and uncontrolled data, but no current auditable download
   with the required source-by-transport replication was located.
6. Vergara et al., *Dataset from chemical gas sensor array in turbulent wind
   tunnel* (2015), DOI <https://doi.org/10.1016/j.dib.2015.02.014>, Crossref
   citations: 10. Public real sensor data, but the two physical source positions
   emit different gases, confounding source position with analyte identity.
7. GSL-Bench (2024), DOI <https://doi.org/10.1109/ICRA57147.2024.10610755>,
   OpenAlex citations: 1. High-fidelity benchmarking tool, but not an untouched
   real-sensor factorial confirmation dataset.
8. Gongora et al., *A Robotic Experiment Toward Understanding Human Gas-Source
   Localization Strategies* (2017), DOI
   <https://doi.org/10.1109/ISOEN.2017.7968899>. More than 150 simulated searches
   were reported, but the original dataset URL is no longer available and the
   data are simulator-derived.
9. Hinsen et al., *Red:Vapor* (2026 dataset article), dataset
   <https://zenodo.org/records/18299926>. Public real wind-tunnel data with
   low/high-wind repeats; rejected because the source is fixed and setup D rotates
   the entire model landscape, so there is no fixed-environment source contrast.
10. France et al., *Chasing Ghosts* (2026),
    <https://arxiv.org/abs/2602.19577>. Reports two rooms and five real flights per
    room; the current public repository does not yet contain raw flight sensor
    logs, so exact replay is unavailable.
11. Jin et al., *Towards Efficient Gas Leak Detection in Built Environments*
    (2023), DOI <https://doi.org/10.1109/ICRA48891.2023.10160816>. Reports 24 real
    experiments across source positions and obstacle setups; no public run-level
    raw sensor series was located.

## Search conclusion

Orebro3DSEN was the only located, currently downloadable real-sensor dataset that
supported both a strong same-source nuisance control and a different-source edge
without analyte confounding. Its untouched V2 confirmation failed one frozen
per-direction effect-size requirement. No second certifiably untouched public
asset satisfying the full factor contract was found.

This absence is a data/identification boundary, not evidence that the mechanism
works or fails universally.
