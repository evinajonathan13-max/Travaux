"""Phase 5 QPU circuit encoding (CPU-first using Qiskit Aer; IBM submission
optional). The 'woven' circuit entangles qubits in a closed ring (image of
the domain weave), the 'aligned' circuit entangles an open chain. Bitstring
samples from counts are embedded in R^N and their H1 P_sig compared.
"""

import numpy as np

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    HAVE_QISKIT = True
except ImportError:
    HAVE_QISKIT = False

from .topology import compute_persistence


def build_weave_circuit(n=4, kind="ring", angle=np.pi / 3, seed=0):
    """Woven = closed RZZ ring; aligned = open RZZ chain; product = no entangle."""
    if not HAVE_QISKIT:
        raise ImportError("qiskit not installed")
    qc = QuantumCircuit(n)
    for q in range(n):
        qc.h(q)
    if kind == "ring":
        for q in range(n):
            qc.rzz(angle, q, (q + 1) % n)
    elif kind == "chain":
        for q in range(n - 1):
            qc.rzz(angle, q, q + 1)
    elif kind == "product":
        pass
    else:
        raise ValueError(kind)
    # read in the X basis: diagonal RZZ gates must rotate before measurement,
    # otherwise bit-flip probabilities remain exactly uniform (no signal)
    for q in range(n):
        qc.h(q)
    qc.measure_all()
    rng = np.random.default_rng(seed)
    meta = {"n": n, "kind": kind, "angle": float(angle),
            "edges": ([(q, (q + 1) % n) for q in range(n)] if kind == "ring"
                      else [(q, q + 1) for q in range(n - 1)] if kind == "chain"
                      else [])}
    return qc, meta


def _correlation_matrix(counts, n):
    """Pairwise correlation |c_ij| over samples with weights from counts."""
    total = sum(counts.values())
    uniq = [(np.array([int(b) for b in bs.replace(" ", "")][::-1], float), c)
            for bs, c in counts.items()]
    p = np.array([c for _, c in uniq]) / total
    x = np.vstack([u for u, _ in uniq])
    C = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            pi = np.sum(p * x[:, i])
            pj = np.sum(p * x[:, j])
            pij = np.sum(p * x[:, i] * x[:, j])
            C[i, j] = C[j, i] = abs(pij - pi * pj)
    return C


def _longest_cycle_score(C, thresh=1e-6):
    """Detect a closed cycle in the correlation graph (DFS); score = sum of
    correlation weights on the cycle edges. 0 if graph is acyclic."""
    n = C.shape[0]
    edges = [(i, j, C[i, j]) for i in range(n) for j in range(i + 1, n)
             if C[i, j] > thresh]
    adj = {i: [] for i in range(n)}
    for i, j, w in edges:
        adj[i].append((j, w))
        adj[j].append((i, w))
    best = [0.0]

    def dfs(u, start, visited, acc):
        for v, w in adj[u]:
            if v == start and len(visited) >= 3:
                best[0] = max(best[0], acc + w)
                continue
            if v in visited:
                continue
            visited.add(v)
            dfs(v, start, visited, acc + w)
            visited.discard(v)

    for s in range(n):
        dfs(s, s, {s}, 0.0)
    return float(best[0])


def contrast_on_aer(qc=None, shots=4096, seed=42, n=4, angle=np.pi / 3,
                    kinds=("ring", "chain")):
    """Woven (ring) vs aligned (chain) compared via the closed-cycle score
    of their sample-correlation graphs. Positive contrast = ring topology."""
    if not HAVE_QISKIT:
        raise ImportError("qiskit not installed")
    sim = AerSimulator(seed_simulator=seed)
    scores = {}
    for kind in kinds:
        qc, _ = build_weave_circuit(n=n, kind=kind, angle=angle)
        res = sim.run(qc, shots=shots).result()
        C = _correlation_matrix(res.get_counts(), n)
        cmax = float(C.max())
        thresh = 0.25 * cmax if cmax > 0 else 1e-6
        scores[kind] = _longest_cycle_score(C, max(thresh, 1e-9))
    woven = scores[kinds[0]]
    aligned = scores[kinds[1]]
    return {"woven_score": float(woven), "aligned_score": float(aligned),
            "contrast": float(woven - aligned), "kinds": list(kinds),
            "n_qubits": n, "shots": shots,
            "metric": "closed-cycle correlation-graph score"}


def submit_to_ibm(token, backend_name, qc, shots=1024):
    """Optional IBM submission. Not run by default (credits are scarce)."""
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    except ImportError:
        raise ImportError("qiskit-ibm-runtime not installed")
    service = QiskitRuntimeService(token=token, channel="ibm_quantum_platform")
    backend = service.backend(backend_name)
    sampler = SamplerV2(backend)
    job = sampler.run([qc], shots=shots)
    job_id = job.job_id()
    return {"job_id": job_id, "backend": backend_name}
