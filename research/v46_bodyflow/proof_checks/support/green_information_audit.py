"""V46 analytic Green-kernel information certificates, not a performance test.

Checks two-epoch contrasts against the Schur projection of the *full* specified
3-D log-Gaussian model with unknown q, h and fixed per-sensor gains.  The source
coordinates are used to evaluate analytic Jacobians, never to select an action.
"""
from pathlib import Path
import importlib.util
import json
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
_candidates = [HERE.parent / "m1/m1_decoders.py",
               ROOT / "output/V46_Overleaf/reference_code/m1/m1_decoders.py",
               ROOT / "output/V45A_Overleaf/reference_code/m1/m1_decoders.py"]
M1_PATH = next((p for p in _candidates if p.is_file()), None)
if M1_PATH is None:
    raise FileNotFoundError("Place this certificate beside ../m1/m1_decoders.py")
spec = importlib.util.spec_from_file_location("m1_decoders", M1_PATH)
m1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m1)


def info(delta2, *, h=11., z1=5., z2=5., known_gains=False):
    delta1 = np.array([[-4., -2.], [5., -1.], [-1., 3.]])
    n = len(delta1)
    ages = [100., 102.]
    kap = .8
    U = np.array([.7, .2, .1])
    s = np.array([2., -3., h])
    centers = [np.array([40., 20.]), np.array([42., 19.])]
    Js, B, bs = [], [], []
    for d, z, a, center in zip([delta1, delta2], [z1, z2], ages, centers):
        p = np.column_stack([d + center, np.full(n, z)])
        deriv = (p - U*a - s)/(2*kap*a)
        Js.append(deriv[:, :2])
        bs.append(float(deriv[0, 2]))
        block = np.column_stack([np.ones(n), deriv[:, 2]])
        if not known_gains:
            block = np.column_stack([block, np.eye(n)])
        B.append(block)
    A, B = np.vstack(Js), np.vstack(B)
    resid = A - B @ np.linalg.pinv(B) @ A
    I_full = resid.T @ resid  # sigma_log = 1, with profiled continuous nuisance
    q1 = np.eye(2)/(2*kap*ages[0])
    q2 = np.eye(2)/(2*kap*ages[1])
    E = delta2@q2 - delta1@q1
    I_z = E.T@E/2
    return {"I_full": I_full, "I_z": I_z, "E": E,
            "b": np.array(bs), "B_rank": np.linalg.matrix_rank(B)}


def main():
    d1 = np.array([[-4., -2.], [5., -1.], [-1., 3.]])
    wind = np.array([[1.3, .2], [.8, -.1], [1.1, .4]])
    Econtrol = m1.encode(d1, wind, [.4, .35, .25])
    # Deliberately specified algebra witness. This is not a tuned performance run.
    R = m1.decode(Econtrol, speed_reconfigure=1.)["relative"]
    movement_s = 1.5
    d2 = d1 + movement_s*R
    q1, q2 = np.eye(2)/160, np.eye(2)/163.2
    F, G = (d2-d1)@q2, d1@(q2-q1)
    sF = float(np.linalg.svd(F, compute_uv=False)[-1])
    nG = float(np.linalg.norm(G, 2))
    assert sF > 2*nG
    moving, rigid = info(d2), info(d1)
    eig_contrast_gain = np.linalg.eigvalsh(moving["I_z"]-rigid["I_z"])
    eig_full_gain = np.linalg.eigvalsh(moving["I_full"]-rigid["I_full"])
    equality_error = float(np.linalg.norm(moving["I_full"]-moving["I_z"], 2))
    assert equality_error < 1e-14
    assert moving["B_rank"] == 4 and len(d1) == 3
    assert eig_contrast_gain.min() > 0 and eig_full_gain.min() > 0

    # At h = flight height, b1=b2=-Uz/(2*kappa). One common contrast direction
    # can retain source information; double centering may discard it.
    equal_b = info(d2, h=5.)
    lower_eigs = np.linalg.eigvalsh(equal_b["I_full"]-equal_b["I_z"])
    assert abs(equal_b["b"][1]-equal_b["b"][0]) < 1e-15
    assert equal_b["B_rank"] == 3
    assert lower_eigs.min() > -1e-14 and lower_eigs.max() > 1e-7

    # A rank-two ordinary geometric expansion can exactly cancel diffusion age.
    cancelling = (102./100.)*d1
    cancel_result = info(cancelling)
    assert np.linalg.matrix_rank(cancelling-d1) == 2
    assert np.linalg.norm(cancel_result["E"], 2) < 1e-15
    assert np.linalg.norm(cancel_result["I_full"], 2) < 1e-26

    # Ordinary rigid translation is NOT zero-information in a diffusing puff.
    assert np.linalg.eigvalsh(rigid["I_z"]).min() > 0

    # Unknown transport changes the nuisance tangent; no derivative-free claim.
    # Analytic full-log Green derivative wrt unknown horizontal wind is age*Js.
    # A single epoch has Js columns in that wind nuisance space, so source
    # information can vanish even for a noncollinear sensor array.
    a = 100.; p = np.column_stack([d1+[40.,20.], np.full(3,5.)])
    source = np.array([2.,-3.,11.]); U = np.array([.7,.2,.1]); kap=.8
    J_s = (p-U*a-source)[:,:2]/(2*kap*a)
    J_U = a*J_s
    residual = J_s-J_U@np.linalg.pinv(J_U)@J_s
    assert np.linalg.norm(residual) < 1e-14

    report = {
        "scope": "ANALYTIC_IDENTITIES_ONLY; known-age/known-kappa/known-wind, log-Gaussian submodel; no native performance result",
        "R": R.tolist(),
        "movement_duration_s": movement_s,
        "age_difference_s": 2.,
        "maximum_nominal_reconfiguration_speed": float(np.linalg.norm(R,axis=1).max()),
        "sigma_min_F": sF,
        "norm_G": nG,
        "dominance_margin_sigmaF_minus_2normG": sF-2*nG,
        "unequal_height_sensitivities": moving["b"].tolist(),
        "unknown_gain_nuisance_rank": int(moving["B_rank"]),
        "full_minus_contrast_norm_when_spanning": equality_error,
        "contrast_information_gain_eigenvalues": eig_contrast_gain.tolist(),
        "physical_full_information_gain_eigenvalues": eig_full_gain.tolist(),
        "equal_height_sensitivities": equal_b["b"].tolist(),
        "equal_b_nuisance_rank": int(equal_b["B_rank"]),
        "full_minus_contrast_eigenvalues_when_not_spanning": lower_eigs.tolist(),
        "rank_two_expansion_cancel_E_norm": float(np.linalg.norm(cancel_result["E"],2)),
        "rank_two_expansion_cancel_full_info_norm": float(np.linalg.norm(cancel_result["I_full"],2)),
        "rigid_translation_contrast_info_eigenvalues": np.linalg.eigvalsh(rigid["I_z"]).tolist(),
        "single_epoch_unknown_wind_source_residual_norm": float(np.linalg.norm(residual)),
        "test_count": 7,
        "status": "PASS",
    }
    outfile = Path(__file__).with_name("GREEN_INFORMATION_AUDIT_RESULTS.json")
    outfile.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
