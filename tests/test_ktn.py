"""KTH:Li woven experiment tests (CPU only, deterministic)."""

import numpy as np
import pytest

from ktn.fabric import generate_fabric, fabric_summary, WARP, WEFT
from ktn.topology import compute_persistence, p_sig_contrast
from ktn.laser import disentangle, vulnerability_map
from ktn.thermal import loop_area, power_law_fit


# ---------------- Phase 1 : generation ----------------

def test_fabric_deterministic():
    a = generate_fabric(seed=11)
    b = generate_fabric(seed=11)
    assert np.allclose(a.points, b.points)
    assert len(a.crossings) == len(b.crossings)


def test_fabric_has_two_families_and_crossings():
    f = generate_fabric(seed=3)
    fams = set(np.unique(f.family))
    assert WARP in fams and WEFT in fams
    assert len(f.crossings) > 0
    s = fabric_summary(f)
    assert s["LK_over"] + s["LK_under"] == len(f.crossings)


def test_aligned_has_one_family():
    a = generate_fabric(woven=False, seed=3)
    assert set(np.unique(a.family)) == {WARP}
    assert len(a.crossings) == 0


# ---------------- Phase 2 : topology ----------------

def test_p_sig_contrast_positive():
    w = generate_fabric(seed=5)
    a = generate_fabric(woven=False, seed=5)
    c = p_sig_contrast(w.points, a.points, seed=5)
    assert c["ratio"] > 1.5


def test_compute_persistence_subsamples():
    rng = np.random.default_rng(0)
    big = rng.normal(size=(5000, 3))
    r = compute_persistence(big, n_max=800, seed=1)
    assert r["n_points_used"] <= 800


# ---------------- Phase 3 : laser ----------------

def test_laser_removes_monotonically_with_INTENSITY():
    f = generate_fabric(seed=7)
    n_weft = (f.family == WEFT).sum()
    rem_low = disentangle(f, peak=0.5, threshold=0.5)[2]
    rem_high = disentangle(f, peak=3.0, threshold=0.5)[2]
    assert rem_high >= rem_low
    assert rem_low >= 0.0 and rem_high <= 1.0


def test_vulnerability_map_shape():
    f = generate_fabric(seed=9)
    v = vulnerability_map(f)
    assert len(v) == len(f.crossings)


# ---------------- Phase 4 : thermal ----------------

def test_loop_area_positive_and_powerlaw():
    t_c = np.linspace(0, 10, 50)
    p_c = np.clip((t_c - 2) / 6.0, 0, 1)
    t_h = t_c
    p_h = np.clip((t_h + 1.0 - 2) / 6.0, 0, 1)
    area = loop_area(t_c, p_c, t_h, p_h)
    assert area > 0
    rates = [1.0, 2.0, 4.0]
    areas = [v * area / 1.0 for v in rates]
    alpha, A = power_law_fit(rates, areas)
    assert abs(alpha - 1.0) < 0.2


# ---------------- Phase 5 : circuit (optional qiskit) ----------------

def test_circuit_contrast_if_qiskit():
    pytest.importorskip("qiskit")
    import ktn.circuit as kcirc
    if not kcirc.HAVE_QISKIT:
        pytest.skip("qiskit_aer unavailable")
    res = kcirc.contrast_on_aer(n=4, kinds=("ring", "chain"))
    assert res["contrast"] > 0.0
