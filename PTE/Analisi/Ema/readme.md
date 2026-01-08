## Numero totale di feature estratte

Sia **N** il numero di nodi della matrice di connettività (matrice \(N \times N\)).

### Edge features (triangolo superiore)

Poiché le matrici sono simmetriche con diagonale nulla, il numero di edge salvati è:

E = N(N − 1) / 2

Colonne:
- `edge_0, edge_1, ..., edge_{E-1}`

---

### 3. Metriche globali (`gf_*`)

Metriche globali estratte per ogni paziente:
 
1. `gf_binary_density`
2. `gf_total_strength`
3. `gf_mean_strength`
4. `gf_charpath_len_w`
5. `gf_global_eff_w`
6. `gf_transitivity_bin`
7. `gf_avg_weighted_clust`
8. `gf_n_communities`
9. `gf_modularity_bin`

**Numero di feature globali: 9**

---

### 4. Metriche nodali “flattened” (`*_nXXX`)

Per ogni nodo vengono calcolate **6 metriche nodali**:

- `degree_bin`
- `strength`
- `clustering_w`
- `betweenness_len`
- `eigenvector_w`
- `local_eff_bin`

Poiché ogni metrica viene salvata **per ciascun nodo**, il numero totale di feature nodali è: 6N

---

## 🔢 Numero totale di feature (feature space)

 N(N − 1) / 2 + 6N + 10


