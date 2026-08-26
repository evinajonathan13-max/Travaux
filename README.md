# RATISS — Transition de phase photo-induite détectée par signal topologique

**Auteurs :** Jonathan Evina ([ORCID 0009-0000-4092-5313](https://orcid.org/0009-0000-4092-5313)) & JOHNKING0

## Question de recherche

Quand un laser pilote la réorganisation structurelle d'un cristal (ici la
dimérisation d'une chaîne SSH), est-ce que le **signal topologique P_sig**
(persistance Vietoris-Rips H1 des corrélations quantiques) détecte la
transition de phase — et avec quel avance ou retard par rapport aux signaux
classiques (gap spectral, corrélation bord-bord) ?

## Méthode

- **Modèle** : chaîne SSH (Su-Schrieffer-Heeger), N=16 sites, bords ouverts,
  mi-remplissage. Transition topologique exacte à δ=0 (vérité analytique :
  winding number, gap).
- **"Laser"** : rampe temporelle δ(t) = 0.4 → −0.4 en temps T.
- **État réel** : propagation temps réel RK4 de i dψ/dt = H(t) ψ.
- **Signal topologique** : P_sig = plus longue vie H1 finie du complexe de
  Vietoris-Rips construit sur les profils de corrélation |C_ij| de l'état
  (moteur RATISS, GF(2), déterministe).
- **Références** : P_sig adiabatique (état fondamental instantané), gap
  spectral, corrélation bord-bord |C(0,N−1)|.

## Résultats (artefacts régénérables, `python3 -m ratiss_photoinduced.*`)

### Sweep statique (`experiment_static.py`, `fig_static_sweep.png`)

- **P_sig est un détecteur binaire de la phase topologique** : strictement nul
  pour tout δ > −0.06, non nul (0.02–0.12) dans la phase topologique. Validé
  contre le winding number analytique.
- **La corrélation bord-bord est un précurseur** : elle croît de façon
  continue *avant* δ=0 (longueur de corrélation qui diverge), là où P_sig est
  encore exactement nul.

### Rampe pilotée (`experiment_driven.py`, `fig_driven_transition.png`)

- Transition du Hamiltonien à t = 100 (δ=0).
- **La corrélation bord-bord bascule à t = 96.4 — 3.6 unités de temps AVANT
  la transition** : c'est le signal d'alerte précoce.
- P_sig bascule à t ≈ 121 (seuil 0.02) : détecteur de confirmation, pas de
  prédiction.
- L'état réel suit l'adiabatique quasi parfaitement à cette vitesse de rampe
  (P_sig final : 0.0814 réel vs 0.0814 adiabatique).

### Multi-vitesses (`experiment_ramp_speeds.py`, `fig_ramp_speeds.png`)

- Retard P_sig réel − adiabatique < 1 pas de temps pour T_ramp ∈ [50, 400] :
  le suivi est robuste sur une décade de vitesses de balayage laser.

### Hystérésis dynamique (`experiment_hysteresis.py`, `fig_hysteresis.png`)

- Rampe aller-retour (trivial → topologique → trivial).
- **Rampe lente (T_leg=400) : hystérésis quasi nulle** — l'état revient à son
  point de départ, cycle réversible (adiabatique).
- **Rampe rapide : boucle d'hystérésis ouverte** — l'état retour ≠ l'état
  aller au même δ, avec oscillations non-adiabatiques (Stückelberg).
- **Loi d'échelle mesurée : aire d'hystérésis ∝ vitesse^1.05** (loi de
  puissance, fit log-log sur T_leg ∈ [10, 400], aire ×63). Apparenté au
  mécanisme de Kibble-Zurek : le système "gèle" près de la transition et rate
  le basculement instantané.

### Décohérence (`experiment_decoherence.py`)

- Équation maîtresse de Lindblad, déphasage local (canaux n_k = |k><k|).
- **Le signal topologique survit au bruit** : transition détectée à tous les
  taux testés, de gamma=0 (pur) à gamma=0.05.
- À gamma=0.05 (pureté finale 50%), P_sig_max = 0.038 — encore ~2× le seuil.
- P_sig décroît doucement avec gamma (0.125 → 0.038), pas de chute brutale :
  **le détecteur topologique est robuste**, c'est ce qui autorise le passage
  au QPU réel.

## Lecture honnête des limites

1. **P_sig ne prédit pas, il confirme.** Le précurseur est la corrélation
   bord-bord (observable classique de taille finie), pas la persistance.
2. Chaîne SSH = modèle jouet 1D soluble. L'extension à TaS₂ ou aux CDW 2D
   demande un vrai Hamiltonien électron-phonon.
3. N=16 : effets de taille finie présents (précurseur bord-bord en est un).
4. Pas de dissipation ni de décoherence : circuit fermé, état pur.
5. Le "laser" est une rampe de δ, pas un couplage Peierls réaliste A(t).

## Résultats QPU IBM Marrakesh (hardware réel)

**Job ID** : `da7ke8c6l22c73dnn2mg` + job corrélations
**Backend** : ibm_marrakesh (156 qubits)
**Circuits** : 9 (2 deltas × 4 paires × 2 bases + 2 Z)
**Shots** : 4096 par circuit

| Phase | P_sig QPU | P_sig exact | Écart |
|---|---|---|---|
| Topologique (δ=-0.5) | 0.0000 | 0.0665 | 0.0665 |
| Triviale (δ=+0.5) | 0.0187 | 0.0012 | 0.0175 |

**Conclusion honnête** : le bruit QPU **inverse le contraste topologique** à N=4.
P_sig sur hardware réel est trop sensible au bruit pour cette taille. Solutions :
plus de qubits, correction d'erreur, ou métrique topologique plus robuste.

## Prochaines étapes

- [x] Rampe aller-retour (hystérésis dynamique, loi d'échelle mesurée : aire ∝ vitesse^1.05).
- [x] Bruit/décoherence (Lindblad) → P_sig survit jusqu'à gamma=0.05 (pureté 50%).
- [x] Circuit SSH sur IBM QPU (ibm_marrakesh) → bruit inverse le contraste à N=4.
- [ ] Embedding de Takens sur P_sig(t) comme EWS (inspiré des signaux
      topologiques d'alerte en finance, MDPI Computers 2025).
- [ ] Métrique topologique robuste au bruit (filtration par densité, pas par corrélation).

## Reproduction

```bash
pip install numpy scipy matplotlib pytest
python3 -m ratiss_photoinduced.experiment_static     # sweep statique
python3 -m ratiss_photoinduced.experiment_driven     # rampe pilotée
python3 -m ratiss_photoinduced.experiment_ramp_speeds  # multi-vitesses
python3 -m ratiss_photoinduced.experiment_hysteresis    # hysteresis
python3 -m ratiss_photoinduced.experiment_decoherence  # decoherence
python3 -m ratiss_photoinduced.qpu_ssh               # circuit QPU
python3 -m ratiss_photoinduced.qpu_correlations      # P_sig QPU
python3 -m ratiss_photoinduced.make_figures          # figures
python3 -m pytest tests/ -q                          # 18 tests
```

## Structure

```
ratiss_photoinduced/
  ssh_model.py              chaîne SSH + propagation RK4
  topology.py               Vietoris-Rips GF(2) (moteur RATISS) + P_sig
  experiment_static.py      sweep statique
  experiment_driven.py      rampe laser
  experiment_ramp_speeds.py multi-vitesses
  experiment_hysteresis.py  rampe aller-retour (Kibble-Zurek)
  experiment_decoherence.py Lindblad (robustesse au bruit)
  qpu_ssh.py              circuit SSH pour QPU
  qpu_correlations.py     mesure correlations croisees QPU
  make_figures.py           figures
tests/test_photoinduced.py  18 tests (vérité analytique SSH)
artifacts/                  JSON + NPZ + PNG régénérés
```
