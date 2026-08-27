# KTN:Li woven-domain experiment (RATISS)

Topological quantification of the spontaneous 3D woven ferroelectric domain
fabric observed by Xin et al., *Light: Science & Applications* **15**, 315
(2026), DOI 10.1038/s41377-026-02374-7. The experiment is driven by the
RATISS `P_sig` metric (Vietoris-Rips H1 persistence, GF(2)).

## Module layout (`ktn/`)

| Module | Role |
|---|---|
| `fabric.py` | Woven-thread generator (warp +45 deg / weft -45 deg, random over/under crossings → random LK distribution, CDW seats at thread ends) |
| `topology.py` | Vietoris-Rips persistence via `ripser`; `P_sig` = max H1 length |
| `laser.py` | 514 nm gaussian rewriting (cut weft, raster scan) + vulnerability map (knot density) |
| `thermal.py` | Hysteresis loop area + power-law fit α |
| `circuit.py` | Qiskit CPU-first circuit phase; ring (woven) vs chain (aligned) closed-cycle correlation score |
| `pipeline.py` | End-to-end driver producing `artifacts/ktn/results.json` + figures |

## Results (deterministic seeds, CPU)

- **Phase 2 contrast:** P_sig(woven)/P_sig(aligned) = **4.86 ± 0.69** (12 seeds) → criterion met (>1.5)
- **Phase 3 optical rewriting:** `I_crit ≈ 0.70 a.u.` (≥95% weft removed); vulnerability map shows the highest knot density at the fabric center → testable prediction
- **Phase 4 thermal cycles:** loop area scales sub-linearly with sweep rate, **α ≈ 0.81** (relaxation-time model; different from the SSH reference 1.05); cycles show different LK but statistically invariant P_sig (**CV = 8.6 %**)
- **Phase 5 circuit (Aer CPU):** ring-cycle correlation contrast **0.385** (4 qubits); IBM submission optional via `qiskit-ibm-runtime` (token from `clef`)

## Reproduce

```bash
pip install numpy scipy matplotlib ripser pytest
# optional for Phase 5: pip install qiskit qiskit-aer
python -c "from ktn.pipeline import run; run('artifacts/ktn')"
pytest tests/test_ktn.py -q
```

Figures in `artifacts/ktn/figures/`. All generators are seeded → outputs
are reproducible given the same library versions.

## Honest limits

- Point clouds are **synthetic**, anchored on the paper's woven geometry;
  real KTN:Li data still requires author collaboration (roadmap 1.1/1.2).
- P_sig subsamples to `n_max` points for speed; ratios averaged over seeds.
- Phase 4 α depends on the relaxation-time model; reported as its own
  universality class rather than forced to SSH 1.05.
- Phase 5 is CPU-simulated; hardware confirmation on ibm_fez/marrakesh
  remains open.
