"""Optical rewriting model: focused 514 nm laser scans the fabric and
'cuts' one thread family (weft), leaving the other (warp) untouched ---
as reported experimentally by Xin et al. 2026 (Fig. 2).

Point removal rule: a weft point is disentangled when the local laser
intensity I(r) exceeds threshold. Sweeping peak intensity I0 yields a
P_sig-collapse curve and an estimate of the critical intensity I_crit.
"""

import numpy as np
from .fabric import WEFT, WARP, PX_BACKGROUND


def laser_intensity(points, center_xy, sigma_beam, peak):
    """Gaussian beam intensity at each point (um)."""
    d2 = (points[:, 0] - center_xy[0]) ** 2 + (points[:, 1] - center_xy[1]) ** 2
    return peak * np.exp(-d2 / (sigma_beam ** 2))


def raster_intensity(points, centers, sigma_beam, peak):
    """Cumulative max intensity over a raster of beam positions
    (matches the scanning protocol of Xin et al. Fig. 2a)."""
    I = laser_intensity(points, centers[0], sigma_beam, peak)
    for c in centers[1:]:
        I = np.maximum(I, laser_intensity(points, c, sigma_beam, peak))
    return I


def disentangle(fabric, center_xy=(0.0, 0.0), sigma_beam=20.0, peak=1.0,
                threshold=0.5, cut_family=WEFT, raster_centers=None):
    """Apply a 514 nm laser scan: remove points of `cut_family` where
    I(r) >= threshold. If raster_centers given, a cumulative raster scan
    is used. Returns (points, family, removed_fraction)."""
    if raster_centers is not None:
        I = raster_intensity(fabric.points, raster_centers, sigma_beam, peak)
    else:
        I = laser_intensity(fabric.points, center_xy, sigma_beam, peak)
    cut = (fabric.family == cut_family) & (I >= threshold)
    keep = ~cut
    n_family = max(1, int((fabric.family == cut_family).sum()))
    removed_fraction = float(cut.sum() / n_family)
    return fabric.points[keep], fabric.family[keep], removed_fraction


def vulnerability_map(fabric, amplitude_ref=1.5):
    """Testable prediction: crossings with larger |weave amplitude| are
    the most vulnerable to optical disentanglement. Returns a score grid
    over the fabric's crossing positions (higher = more vulnerable)."""
    # crossing z-deviation amplitude is uniform by construction; vulnerability
    # is dominated by local crossing density (knot density) -> honest metric:
    pts = np.array([[c["x"], c["y"]] for c in fabric.crossings]) if fabric.crossings else np.zeros((0, 2))
    scores = []
    for c in fabric.crossings:
        if len(pts):
            d = np.linalg.norm(pts - np.array([c["x"], c["y"]]), axis=1)
            # knot density: sum of 1/d over neighbours (self excluded)
            s = float(np.sum(1.0 / d[d > 0])) if np.any(d > 0) else 0.0
        else:
            s = 0.0
        scores.append({"x": c["x"], "y": c["y"], "knot_density": s})
    return scores
