"""Woven ferroelectric domain fabric generator, anchored on Xin et al. 2026
(Light: Science & Applications 15:315, DOI 10.1038/s41377-026-02374-7).

Paper-anchored parameters:
- two thread families: "warp" (+45 deg) and "weft" (-45 deg) diagonal threads
- over/under crossings assigned randomly per crossing -> random LK distribution
- lattice constant ~ 10 um (twice the striation period)
- threads carry CDWs at their terminating ends (tail-to-tail)
- after 514 nm laser scanning only one family survives (disentangled)
"""

from dataclasses import dataclass
import numpy as np

WARP = 0
WEFT = 1
PX_BACKGROUND = 2


@dataclass
class FabricResult:
    points: np.ndarray          # (N, 3) in um
    family: np.ndarray          # (N,) int labels: 0 warp, 1 weft, 2 px background
    crossings: list             # list of dicts {position, over_family} per warp-weft crossing
    cdw_mask: np.ndarray        # (N,) bool: points at charged-domain-wall thread ends
    thread_id: np.ndarray       # (N,) int: thread index (-1 = px background)
    seed: int                   # RNG seed used


def _thread_constant_offsets(box_xy, spacing, theta_deg):
    """Constant intercepts for the diagonal family: y = tan(theta)*x + c.

    Intercept range is computed over the four box corners (robust for
    positive or negative slopes).
    """
    th = np.tan(np.deg2rad(theta_deg))
    x0, x1, y0, y1 = box_xy
    corner_c = [y - th * x for x in (x0, x1) for y in (y0, y1)]
    c_min, c_max = min(corner_c), max(corner_c)
    n = int((c_max - c_min) / spacing) + 1
    return th, np.linspace(c_min, c_max, n)


def generate_fabric(box_xy=(-50.0, 50.0, -50.0, 50.0),
                    spacing=10.0,
                    amplitude=1.5,
                    sigma=2.0,
                    step=1.0,
                    jitter=0.15,
                    px_density=0.0,
                    theta_deg=45.0,
                    woven=True,
                    seed=0):
    """Generate a woven (or parallel-only) ferroelectric fabric point cloud.

    Returns FabricResult with thread_id per point (background = -1).
    For woven=False only warp threads (no weaving), i.e. the post-laser
    disentangled structure.
    """
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = box_xy

    th_w, c_w = _thread_constant_offsets(box_xy, spacing, theta_deg)
    th_f, c_f = _thread_constant_offsets(box_xy, spacing, -theta_deg)

    pts, fam, cdw, tids = [], [], [], []
    crossings = []
    tid = 0

    families = [(WARP, th_w, c_w)]
    if woven:
        families.append((WEFT, th_f, c_f))

    if woven:
        for iw, c1 in enumerate(c_w):
            for ifw, c2 in enumerate(c_f):
                if abs(th_w - th_f) < 1e-9:
                    continue
                xc = (c2 - c1) / (th_w - th_f)
                yc = th_w * xc + c1
                if x0 <= xc <= x1 and y0 <= yc <= y1:
                    over = int(rng.integers(0, 2))
                    crossings.append({"iw": iw, "if": ifw, "x": xc, "y": yc, "over": over})

    for family_idx, th, c_vals in families:
        for line_idx, c in enumerate(c_vals):
            n_t = max(8, int((x1 - x0) / step))
            t = np.linspace(x0, x1, n_t)
            xs = t
            ys = th * t + c
            inside = (ys >= y0) & (ys <= y1)
            zs = np.zeros(n_t)
            for cr in crossings:
                on_thread = (cr["iw"] if family_idx == WARP else cr["if"]) == line_idx
                if not on_thread:
                    continue
                if family_idx == WARP:
                    s_over = (cr["over"] == WARP)
                else:
                    s_over = (cr["over"] == WEFT)
                a = amplitude if s_over else -amplitude
                zs += a * np.exp(-0.5 * ((xs - cr["x"]) / sigma) ** 2)
            mask = inside
            n_in = int(mask.sum())
            if n_in == 0:
                continue
            xs, ys, zs = xs[mask], ys[mask], zs[mask]
            jitter_xyz = rng.normal(0.0, jitter, (n_in, 3))
            p = np.stack([xs, ys, zs], axis=1) + jitter_xyz
            cd = np.zeros(n_in, dtype=bool)
            cd[0] = True
            cd[-1] = True
            pts.append(p)
            fam.append(np.full(n_in, family_idx))
            cdw.append(cd)
            tids.append(np.full(n_in, tid))
            tid += 1

    # Px background: paper describes prism-shaped, essentially flat domains
    if px_density > 0:
        n_bg = int(px_density * (x1 - x0) * (y1 - y0))
        bgx = rng.uniform(x0, x1, n_bg)
        bgy = rng.uniform(y0, y1, n_bg)
        bgz = rng.uniform(-jitter, jitter, n_bg)
        pts.append(np.stack([bgx, bgy, bgz], axis=1))
        fam.append(np.full(n_bg, PX_BACKGROUND))
        cdw.append(np.zeros(n_bg, dtype=bool))
        tids.append(np.full(n_bg, -1))

    points = np.concatenate(pts)
    family = np.concatenate(fam)
    cdw_mask = np.concatenate(cdw)
    thread_id = np.concatenate(tids)
    return FabricResult(points=points, family=family, crossings=crossings,
                        cdw_mask=cdw_mask, thread_id=thread_id, seed=seed)


def fabric_summary(result):
    n_w = int(np.sum(result.family == WARP))
    n_f = int(np.sum(result.family == WEFT))
    n_b = int(np.sum(result.family == PX_BACKGROUND))
    lk_over = sum(1 for c in result.crossings if c["over"] == WARP)
    lk_under = len(result.crossings) - lk_over
    return {"n_points": len(result.points), "warp": n_w, "weft": n_f,
            "background": n_b, "crossings": len(result.crossings),
            "LK_over": lk_over, "LK_under": lk_under}
