"""Tests de l\'expérience photoinduite — vérité analytique SSH comme référence."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ratiss_photoinduced.ssh_model import (
    correlation_matrix,
    edge_weight,
    ground_state_orbitals,
    spectral_gap,
    ssh_hamiltonian,
    winding_number,
    evolve_orbitals,
)
from ratiss_photoinduced.topology import psig_from_correlation, rips_persistence


class TestSSHModel:
    def test_hamiltonian_hermitian(self):
        h = ssh_hamiltonian(16, -0.3)
        assert np.allclose(h, h.T)

    def test_hamiltonian_requires_even_sites(self):
        with pytest.raises(ValueError):
            ssh_hamiltonian(15, 0.1)

    def test_winding_topological(self):
        assert abs(winding_number(-0.5) - (-1.0)) < 0.01

    def test_winding_trivial(self):
        assert abs(winding_number(0.5)) < 0.01

    def test_gap_closes_at_transition(self):
        # le gap en delta=0 est bien plus petit que dans la phase triviale profonde
        assert spectral_gap(ssh_hamiltonian(16, 0.0)) < 0.25 * spectral_gap(ssh_hamiltonian(16, 0.5))

    def test_topological_gap_smaller_than_trivial(self):
        assert spectral_gap(ssh_hamiltonian(16, -0.5)) < 0.01 * spectral_gap(ssh_hamiltonian(16, 0.5))

    def test_correlation_idempotent(self):
        c = correlation_matrix(ground_state_orbitals(ssh_hamiltonian(16, -0.4)))
        assert np.allclose(c @ c, c, atol=1e-10)

    def test_edge_weight_phase_contrast(self):
        c_topo = correlation_matrix(ground_state_orbitals(ssh_hamiltonian(16, -0.5)))
        c_triv = correlation_matrix(ground_state_orbitals(ssh_hamiltonian(16, 0.5)))
        assert edge_weight(c_topo) > 100 * edge_weight(c_triv)


class TestTopology:
    def test_rips_square_has_h1_loop(self):
        # 4 points en carré : un cycle H1 de vie positive
        pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
        dist = np.linalg.norm(pts[:, None] - pts[None, :], axis=2)
        res = rips_persistence(dist, max_edge=2.0)
        assert res["psig"] > 0

    def test_psig_zero_in_trivial_phase(self):
        c = correlation_matrix(ground_state_orbitals(ssh_hamiltonian(16, 0.5)))
        assert psig_from_correlation(c) == pytest.approx(0.0, abs=1e-9)

    def test_psig_positive_in_topological_phase(self):
        c = correlation_matrix(ground_state_orbitals(ssh_hamiltonian(16, -0.5)))
        assert psig_from_correlation(c) > 0.01

    def test_psig_monotone_marker_near_transition(self):
        # P_sig nul du côté trivial, non nul du côté topologique (N=16)
        ps = [psig_from_correlation(correlation_matrix(ground_state_orbitals(ssh_hamiltonian(16, d))))
              for d in (0.3, 0.1, -0.3, -0.5)]
        assert ps[0] == pytest.approx(0.0, abs=1e-9)
        assert ps[1] == pytest.approx(0.0, abs=1e-9)
        assert ps[2] > 0.01 and ps[3] > 0.01


class TestDrivenDynamics:
    def test_evolution_preserves_orthonormality(self):
        # dt = 0.1 (dt de production) : erreur RK4 d'orthonormalité < 1e-3
        orb0 = ground_state_orbitals(ssh_hamiltonian(16, 0.4))
        traj = evolve_orbitals(orb0, lambda t: 0.4 - 0.8 * min(t / 200.0, 1.0), 0.1, 200)
        gram = traj[-1].conj().T @ traj[-1]
        assert np.allclose(gram, np.eye(gram.shape[0]), atol=1e-3)

    def test_evolved_state_tracks_adiabatic_psig(self):
        # rampe lente : le P_sig de l\'état réel suit l\'adiabatique à 10 %
        orb0 = ground_state_orbitals(ssh_hamiltonian(16, 0.4))
        t_ramp = 200.0
        traj = evolve_orbitals(orb0, lambda t: 0.4 - 0.8 * min(t / t_ramp, 1.0), 0.2, int(t_ramp / 0.2))
        psig_real = psig_from_correlation(correlation_matrix(traj[-1]))
        psig_ad = psig_from_correlation(correlation_matrix(ground_state_orbitals(ssh_hamiltonian(16, -0.4))))
        assert abs(psig_real - psig_ad) / psig_ad < 0.1
