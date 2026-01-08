## Numero totale di feature estratte

Sia **N** il numero di nodi della matrice di connettività (matrice \(N \times N\)).

---

### 1. Identificativi (NON feature)

Queste colonne sono metadati e **non fanno parte del feature space**:

- `id`
- `label`

---

### 2. Edge features (triangolo superiore)

Poiché le matrici sono simmetriche con diagonale nulla, il numero di edge salvati è:

\[
E = \frac{N(N-1)}{2}
\]

Colonne:
- `edge_0, edge_1, ..., edge_{E-1}`

**Numero di edge feature:**

\[
\boxed{\frac{N(N-1)}{2}}
\]

---

### 3. Metriche globali (`gf_*`)

Metriche globali estratte per ogni paziente:

1. `gf_n_nodes`
2. `gf_binary_density`
3. `gf_total_strength`
4. `gf_mean_strength`
5. `gf_charpath_len_w`
6. `gf_global_eff_w`
7. `gf_transitivity_bin`
8. `gf_avg_weighted_clust`
9. `gf_n_communities`
10. `gf_modularity_bin`

**Numero di feature globali:**

\[
\boxed{10}
\]

---

### 4. Metriche nodali “flattened” (`*_nXXX`)

Per ogni nodo vengono calcolate **6 metriche nodali**:

- `degree_bin`
- `strength`
- `clustering_w`
- `betweenness_len`
- `eigenvector_w`
- `local_eff_bin`

Poiché ogni metrica viene salvata **per ciascun nodo**, il numero totale di feature nodali è:

\[
\boxed{6 \times N}
\]

---

## 🔢 Numero totale di feature (feature space)

Escludendo `id` e `label`, il numero totale di feature per ogni paziente è:

\[
\boxed{
\frac{N(N-1)}{2}
\;+\;
6N
\;+\;
10
}
\]


