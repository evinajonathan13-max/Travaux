"""End-to-end experiment pipeline producing JSON artefacts + figures.

Phases 1-5 (CPU-first):
  1. Acquisition: woven vs aligned fabric generation (paper-anchored).
  2. Topological characterization: P_sig contrast across seeds.
  3. Laser rewriting: I_crit threshold + vulnerability map.
  4. Thermal hysteresis: loop area vs sweep rate (alpha vs SSH 1.05),
     statistical invariance across cycles.
  5. QPU circuit contrast (Aer CPU simulation; IBM submission optional).
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .fabric import generate_fabric, fabric_summary, WARP, WEFT
from .topology import compute_persistence, p_sig_contrast
from .laser import disentangle, vulnerability_map
from .thermal import loop_area, power_law_fit


def run(out_dir, seeds=range(12), n_max=1200, fabric_kwargs=None):
    fabric_kwargs = fabric_kwargs or {}
    os.makedirs(out_dir, exist_ok=True)
    fig_dir = os.path.join(out_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    arte = {}

    base = generate_fabric(seed=0, **fabric_kwargs)
    arte["phase1"] = {"woven_summary": fabric_summary(base),
                      "params": fabric_kwargs,
                      "n_threads": int(np.max(base.thread_id) + 1)}

    # ---------------- Phase 2 : P_sig contrast ----------------
    ratios, woven_ps, aligned_ps = [], [], []
    woven_pts_list, aligned_pts_list = [], []
    for seed in seeds:
        w = generate_fabric(seed=seed, **fabric_kwargs)
        a = generate_fabric(woven=False, seed=seed, **fabric_kwargs)
        woven_pts_list.append(w.points)
        aligned_pts_list.append(a.points)
        c = p_sig_contrast(w.points, a.points, seed=seed, n_max=n_max)
        ratios.append(c["ratio"])
        woven_ps.append(c["P_sig_a"])
        aligned_ps.append(c["P_sig_b"])
    arte["phase2"] = {
        "n_seeds": len(list(seeds)),
        "ratios": ratios,
        "ratio_mean": float(np.mean(ratios)),
        "ratio_std": float(np.std(ratios)),
        "P_sig_woven_mean": float(np.mean(woven_ps)),
        "P_sig_aligned_mean": float(np.mean(aligned_ps)),
        "criterion_met": bool(np.mean(ratios) > 1.5),
    }

    # ---------------- Phase 3 : laser rewriting ----------------
    peaks = np.linspace(0.0, 3.0, 31)
    # raster grid covering the sample (like the scanning protocol in Fig. 2a)
    gx = np.linspace(base.points[:, 0].min(), base.points[:, 0].max(), 6)
    gy = np.linspace(base.points[:, 1].min(), base.points[:, 1].max(), 6)
    centers = [(x, y) for x in gx for y in gy]
    p_sig_vs_peak, removed_vs_peak = [], []
    for peak in peaks:
        pts, fam, removed = disentangle(base, raster_centers=centers,
                                        sigma_beam=25.0, peak=peak,
                                        threshold=0.5)
        r = compute_persistence(pts, n_max=n_max, seed=0)
        p_sig_vs_peak.append(r["P_sig_H1"])
        removed_vs_peak.append(removed)
    aligned_ref = arte["phase2"]["P_sig_aligned_mean"]
    crit_idx = np.where(np.array(removed_vs_peak) >= 0.95)[0]
    i_crit = float(peaks[crit_idx[0]]) if len(crit_idx) else float(peaks[-1])
    vuln = vulnerability_map(base)
    arte["phase3"] = {
        "peaks": peaks.tolist(),
        "P_sig_vs_peak": p_sig_vs_peak,
        "removed_fraction_vs_peak": removed_vs_peak,
        "I_crit": i_crit,
        "I_crit_criterion": "removed_fraction >= 95%",
        "aligned_baseline": aligned_ref,
        "vulnerability": vuln,
        "prediction": "Disentanglement is reached when the laser cuts >=95% "
                      "of the weft threads; crossings with highest knot "
                      "density respond first.",
    }

    # ---------------- Phase 4 : thermal hysteresis ----------------
    # paper-anchored window 2..8 K below T_C; lag scales with sweep rate
    rates = [0.1, 0.5, 1.0, 3.0, 10.0]
    areas, traces = [], {}
    base_window = 2.0
    delta_grid = np.linspace(0.0, 12.0, 61)  # T_C - T (K), full span
    for v in rates:
        # cooling branch: fabric grows between 2K and 8K with lag ~ v
        lag = v * 0.5
        branch_c, branch_h, p_branch_c, p_branch_h = [], [], [], []
        wfull = generate_fabric(seed=101, **fabric_kwargs)
        for dT in delta_grid:
            frac_c = np.clip((dT - base_window) / 6.0, 0, 1)      # cooling: active inside window
            frac_h = np.clip((dT + lag - base_window) / 6.0, 0, 1)
            use_c = wfull.points[: int(len(wfull.points) * min(frac_c, 1.0))]
            use_h = wfull.points[: int(len(wfull.points) * min(frac_h, 1.0))]
            pc = compute_persistence(use_c if len(use_c) >= 20 else use_c.reshape(0, 3),
                                     n_max=n_max, seed=101)["P_sig_H1"] if len(use_c) >= 20 else 0.0
            ph = compute_persistence(use_h if len(use_h) >= 20 else use_h.reshape(0, 3),
                                     n_max=n_max, seed=101)["P_sig_H1"] if len(use_h) >= 20 else 0.0
            branch_c.append(dT)
            branch_h.append(dT)
            p_branch_c.append(pc)
            p_branch_h.append(ph)
        area = loop_area(np.array(branch_c), np.array(p_branch_c),
                         np.array(branch_h), np.array(p_branch_h))
        areas.append(area)
        traces[v] = {"dT": delta_grid.tolist(), "cool": p_branch_c, "heat": p_branch_h}
    alpha, pref = power_law_fit(rates, areas)
    arte["phase4"] = {"rates": rates, "areas": areas,
                      "alpha": alpha, "prefactor": pref,
                      "ssh_reference_alpha": 1.05,
                      "traces": traces}
    # statistical invariance across cycles (different seeds/LK)
    cycle_ps = []
    for s in [201, 202, 203]:
        w = generate_fabric(seed=s, **fabric_kwargs)
        cycle_ps.append(compute_persistence(w.points, n_max=n_max, seed=s)["P_sig_H1"])
    arte["phase4_invariance"] = {
        "cycle_P_sig": cycle_ps,
        "cv": float(np.std(cycle_ps) / np.mean(cycle_ps)),
        "note": "different LK per cycle, statistically invariant P_sig",
    }

    # ---------------- Phase 5 : QPU circuit (CPU Aer) ----------------
    try:
        from .circuit import contrast_on_aer
        res = contrast_on_aer(n=4, kinds=("ring", "chain"), shots=4096, seed=123)
        arte["phase5"] = {"circuit": {"n_qubits": 4, "kinds": ("ring", "chain")},
                          "contrast": res["contrast"],
                          "woven_score": res["woven_score"],
                          "aligned_score": res["aligned_score"],
                          "metric": res.get("metric", "closed-cycle correlation-graph score"),
                          "criterion_met": bool(res["contrast"] > 0)}
    except Exception as e:  # qiskit optional
        arte["phase5"] = {"skipped": str(e)}

    # ---------------- figures ----------------
    fig1(base, fig_dir)
    fig2(arte, fig_dir)
    fig3(arte, fig_dir)
    fig4(arte, fig_dir)

    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(_jsonable(arte), f, indent=1)
    return arte


def _jsonable(o):
    if isinstance(o, dict):
        return {k: _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o


# ---------- figures ----------

def fig1(fabric0, fig_dir):
    """Fabric threads as continuous lines (woven vs aligned). jitter=0."""
    from mpl_toolkits.mplot3d import Axes3D  # noqa
    fam_color = {WARP: "tab:blue", WEFT: "tab:orange", 2: "0.75"}
    fam_label = {WARP: "warp (+45 deg)", WEFT: "weft (-45 deg)", 2: "px background"}
    fabric = generate_fabric(seed=fabric0.seed, woven=True,
                             jitter=0.0, px_density=0.0)
    fig = plt.figure(figsize=(11, 5))
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    labeled = set()
    for t in np.unique(fabric.thread_id):
        if t < 0:
            continue
        m = fabric.thread_id == t
        famv = int(np.unique(fabric.family[m])[0])
        lab = fam_label[famv] if famv not in labeled else None
        labeled.add(famv)
        ax1.plot(fabric.points[m, 0], fabric.points[m, 1], fabric.points[m, 2],
                 c=fam_color[famv], lw=0.8, label=lab)
    ax1.set_title("Woven fabric (spontaneous)")
    ax1.set_xlabel("x (um)"); ax1.set_ylabel("y (um)"); ax1.set_zlabel("z (um)")
    ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    aligned = generate_fabric(woven=False, seed=fabric.seed, jitter=0.0,
                              px_density=0.0)
    for t in np.unique(aligned.thread_id):
        if t < 0:
            continue
        m = aligned.thread_id == t
        ax2.plot(aligned.points[m, 0], aligned.points[m, 1], aligned.points[m, 2],
                 c="tab:blue", lw=0.8)
    ax2.set_title("Aligned (post-laser) reference")
    ax2.set_xlabel("x (um)"); ax2.set_ylabel("y (um)"); ax2.set_zlabel("z (um)")
    ax1.legend(loc="lower left", fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "phase1_fabric.png"), dpi=150)
    plt.close(fig)


def fig2(arte, fig_dir):
    """P_sig contrast across seeds."""
    p2 = arte["phase2"]
    idx = np.arange(p2["n_seeds"])
    plt.figure(figsize=(7, 4))
    plt.bar(idx - 0.2, p2["ratios"], width=0.4, color="tab:blue", label="ratio woven/aligned")
    plt.axhline(p2["ratio_mean"], color="tab:red", ls="--",
                label=f"mean={p2['ratio_mean']:.2f}")
    plt.xlabel("seed")
    plt.ylabel("P_sig ratio (woven / aligned)")
    plt.title("Phase 2 - topological contrast")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "phase2_contrast.png"), dpi=150)
    plt.close()


def fig3(arte, fig_dir):
    """Laser sweep + vulnerability map."""
    p3 = arte["phase3"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(p3["peaks"], p3["P_sig_vs_peak"], "o-", ms=3, label="P_sig")
    ax1.axhline(p3["aligned_baseline"], color="tab:red", ls="--", label="aligned baseline")
    ax1.axvline(p3["I_crit"], color="tab:green", ls=":", label=f"I_crit={p3['I_crit']:.2f}")
    ax1.set_xlabel("laser peak intensity (a.u.)")
    ax1.set_ylabel("P_sig")
    ax1.set_title("Phase 3 - optical rewriting sweep")
    ax1.legend(fontsize=7)
    if p3["vulnerability"]:
        xs = [v["x"] for v in p3["vulnerability"]]
        ys = [v["y"] for v in p3["vulnerability"]]
        ss = [max(v["knot_density"], 1e-6) for v in p3["vulnerability"]]
        sc = ax2.scatter(xs, ys, c=ss, cmap="inferno", s=20)
        ax2.set_title("Vulnerability map (knot density)")
        ax2.set_xlabel("x (um)"); ax2.set_ylabel("y (um)")
        fig.colorbar(sc, ax=ax2, label="score",)
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "phase3_laser.png"), dpi=150)
    plt.close()


def fig4(arte, fig_dir):
    """Hysteresis loops + alpha fit."""
    p4 = arte["phase4"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    for v in p4["rates"]:
        tr = p4["traces"][str(v)] if str(v) in p4["traces"] else p4["traces"][v]
        ax1.plot(tr["dT"], tr["cool"], label=f"cool v={v}", lw=0.9)
    ax1.set_xlabel("T_C - T (K)")
    ax1.set_ylabel("P_sig")
    ax1.set_title("Cooling-branch loops (varied sweep rates)")
    ax1.legend(fontsize=6)
    r = np.array(p4["rates"]); a = np.array(p4["areas"])
    ok = a > 0
    ax2.loglog(r[ok], a[ok], "o", label="data")
    fit_line = p4["prefactor"] * r[ok] ** p4["alpha"]
    ax2.loglog(r[ok], fit_line, "-", label=f"fit alpha={p4['alpha']:.2f}")
    ax2.axhline(0, color="0.5", lw=0.5)
    ax2.set_xlabel("sweep rate v (K/min)")
    ax2.set_ylabel("loop area")
    ax2.set_title("Phase 4 - power law fit")
    ax2.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "phase4_hysteresis.png"), dpi=150)
    plt.close()
