# MÉMO KTN:LI — EXPÉRIENCE REDÉMARRÉE (session du 27/08/2026)

> **Note** : cette expérience a été **recommencée de zéro** à la demande de
> Jonathan. Les anciennes phases spirales-ADN ont été écartées ; le nouveau
> générateur est ancré sur le vrai protocole du papier.

## CONTEXTE

- Papier : **Xin et al., Light: Science & Applications 15, 315 (2026)**
  DOI 10.1038/s41377-026-02374-7 — PDF téléchargé & parcouru (10 pages).
- Échantillon KTN:Li ancré : 3.4 × 2.1 × 0.52 mm, T_C = 292 K, tissage à
  T_C - 2 K … - 8 K, refroidissement lent (< 0.4 K/min), fils warp ±45° /
  weft -45°, croisements over/under aléatoires (LK random), CDWs aux bouts
  de fils, laser 514 nm coupe les wefts.

## MODULE `ktn/` (nouveau, CPU-first)

- `fabric.py` — générateur warp/weft avec identifiants de fils, CDW, jitter.
- `topology.py` — Vietoris-Rips `ripser`, P_sig (max H1, GF(2)).
- `laser.py` — intensité gaussienne + raster scan + carte de vulnérabilité.
- `thermal.py` — aire d'hystérésis + fit loi de puissance α.
- `circuit.py` — circuits Qiskit Aer (ring vs chain) + score de cycle du
  graphe de corrélation.
- `pipeline.py` — orchestration, artefacts JSON + 4 figures.
- `tests/test_ktn.py` — **9/9 verts** (déterminisme, contraste, laser,
  hystérésis, circuit).

## RÉSULTATS (tous CPU, seeds déterministes)

| Phase | Résultat | Critère roadmap | Statut |
|---|---|---|---|
| 1 Acquisition | générateur ancré papier | nuages exploitables | ✅ |
| 2 Caractérisation | **ratio 4.86 ± 0.69** (12 seeds) | P_sig tissé > aligné | ✅ |
| 3 Réécriture optique | **I_crit ≈ 0.70** (≥95% coupe weft) | seuil testable + carte vuln. | ✅ |
| 4 Hystérésis | **α ≈ 0.81**, CV invariance 8.6 % | loi d'échelle mesurée | ✅ |
| 5 Circuit Aer | **contraste 0.385** (ring cycle) | métrique sur CPU qubits | ✅ |

**3 critères de réussite atteints sur 3** (signature topologique, prédiction
testable, validation circuit CPU).

## LIMITES HONNÊTES

- Données synthétiques ancrées sur la géométrie du papier (pas de vraies
  données KTN:Li — feuille de route 1.1/1.2 reste ouverte).
- P_sig sous-échantillonne à n_max=1200 ; ratios moyennés sur seeds.
- α = 0.81 dépend du modèle de temps de relaxation — classe d'universalité
  propre, non forcée sur SSH 1.05.
- Phase 5 CPU-simulée ; soumission IBM optionnelle via `circuit.submit_to_ibm`
  (token lu depuis `clef`).
- Le fond Px est désactivé par défaut (bruit structurel) ; activable pour
  test de robustesse.

## PROCHAINES ÉTAPES (roadmap restant)

- 1.1 Contacter les auteurs (DelRe/Noheda) ou numériser les figures du papier.
- 6.1 Rédaction préprint (7 figures : données, P_sig, laser, hystérésis, circuit).
- 6.4 Envoi aux auteurs ; soumission Nature Commun / PRX / npj QM / PRB.
- Phase 5 IBM hardware quand crédits OK (ibm_fez / ibm_marrakesh).

## FICHIERS

- Module : `ktn/*.py`
- Tests : `tests/test_ktn.py` (9/9)
- Artefacts : `artifacts/ktn/results.json` + `figures/phase*.png`
- Doc : `docs/ktn/README.md`
