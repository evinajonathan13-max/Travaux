"""Topological characterization: Vietoris-Rips persistence and P_sig metric.

P_sig follows the frozen RATISS law R = P_sig = max H1 persistence length
(birth->death) over Vietoris-Rips GF(2). Optionally H2; counts significant
cycles above a noise gate.
"""

import numpy as np
from ripser import ripser


def compute_persistence(points, maxdim=1, thresh=np.inf, n_max=2000, seed=0):
    """Compute Vietoris-Rips persistence diagrams on a point cloud.

    Subsamples deterministically if len(points) > n_max for speed.
    Returns dict with diagrams per dimension and gate-free P_sig values.
    """
    points = np.asarray(points, dtype=float)
    if len(points) > n_max:
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(points), n_max, replace=False)
        points = points[idx]
    res = ripser(points, maxdim=maxdim, thresh=thresh)
    out = {"diagrams": res["dgms"], "n_points_used": len(points)}
    for dim in range(maxdim + 1):
        dgm = res["dgms"][dim]
        finite = dgm[np.isfinite(dgm[:, 1])]
        lengths = finite[:, 1] - finite[:, 0]
        out[f"P_sig_H{dim}"] = float(lengths.max()) if len(lengths) else 0.0
        out[f"n_cycles_H{dim}"] = int(len(finite))
        out[f"lengths_H{dim}"] = lengths
    return out


def p_sig_contrast(pts_a, pts_b, maxdim=1, seed=0, n_max=2000):
    """Contrast of P_sig between two point clouds (woven vs aligned)."""
    ra = compute_persistence(pts_a, maxdim=maxdim, seed=seed, n_max=n_max)
    rb = compute_persistence(pts_b, maxdim=maxdim, seed=seed, n_max=n_max)
    pa, pb = ra[f"P_sig_H1"], rb[f"P_sig_H1"]
    ratio = pa / pb if pb > 0 else np.inf
    return {"P_sig_a": pa, "P_sig_b": pb, "ratio": ratio, "raw_a": ra, "raw_b": rb}
