"""Thermal cycling / hysteresis model.

Paper-anchored window: woven fabric forms when 2 K < (T_C - T) < 8 K, and
dissolves below. Hysteresis: cooling vs heating branches are separated by a
temperature lag proportional to sweep rate (relaxation-time model), so loop
area scales with sweep rate v (Kuyper-esque power law Area ~ v^alpha, to be
compared with the SSH result alpha ~ 1.05 from the RATISS engine).

Independence of cycles (non-ergodicity): each cycle uses a different fabric
seed -> different LK distribution, but we verify statistical invariance of
P_sig across cycles.
"""

import numpy as np


def hysteresis_branches(points_cooling_seq, points_heating_seq, p_sig_fn):
    """Compute P_sig(T) on both branches. Sequences are (T, points) lists.
    Returns (T_c, P_c, T_h, P_h)."""
    T_c = np.array([t for t, _ in points_cooling_seq])
    T_h = np.array([t for t, _ in points_heating_seq])
    P_c = np.array([p_sig_fn(p) for _, p in points_cooling_seq])
    P_h = np.array([p_sig_fn(p) for _, p in points_heating_seq])
    return T_c, P_c, T_h, P_h


def loop_area(T_c, P_c, T_h, P_h):
    """Absolute area between cooling and heating P_sig(T) branches by
    interpolation on the common T grid."""
    t = np.linspace(max(T_c.min(), T_h.min()), min(T_c.max(), T_h.max()), 200)
    pc = np.interp(t, T_c, P_c)
    ph = np.interp(t, T_h, P_h)
    return float(np.trapezoid(np.abs(pc - ph), t))


def power_law_fit(rates, areas):
    """Fit Area ~ A * v^alpha by log-log regression. Returns (alpha, A)."""
    r = np.asarray(rates, float)
    a = np.asarray(areas, float)
    ok = (r > 0) & (a > 0)
    slope, intercept = np.polyfit(np.log(r[ok]), np.log(a[ok]), 1)
    return float(slope), float(np.exp(intercept))
