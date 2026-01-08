# Wide Graph Feature Builder (`final.csv`)

Questo script legge una serie di **matrici di connettività** (una per paziente, salvata come `.csv`) e un file di **etichette** (`labels_claudia.csv`), calcola **feature di grafo** (globali + nodali) e crea un unico dataset in formato **wide** chiamato `final.csv`, pronto per ML.

---

## Input

- **`LABELS_CSV`**: CSV con colonne *ID paziente* e *label* (auto-detect nomi colonna più comuni; oppure puoi forzarli con `ID_COL_HINT` e `LABEL_COL_HINT`).
- **`MAT_DIR`**: cartella contenente le matrici di ogni paziente in formato `*.csv`.
  - Ogni file deve contenere una **matrice quadrata NxN**.

---

## Assunzioni sulle matrici

Le matrici in input sono considerate **già**:
- **simmetriche** (`A = A^T`)
- con **diagonale nulla** (`diag(A) = 0`)

Lo script **non** simmetrizza e **non** forza la diagonale a zero.
Fa solo dei controlli (warning) se trova:
- asimmetrie sopra una tolleranza (`SYMM_TOL`)
- diagonale non ~0 sopra una tolleranza (`SYMM_TOL`)

Opzionale: se `CLIP_NEGATIVES=True`, i valori negativi vengono posti a 0.

---

## Output (`final.csv`)

Ogni riga corrisponde a un paziente e contiene:

1. **Identificativi**
   - `id`: ID canonizzato estratto dal nome file / stringa ID
   - `label`: etichetta associata al paziente

2. **Edge features (triangolo superiore)**
   - `edge_0 ... edge_{E-1}`: tutti i valori della matrice nel **triangolo superiore** (con `k=1`, esclusa la diagonale).
   - Nota: gli edge vengono salvati **sempre tutti** (non sogliati). La soglia `EDGE_MIN_FOR_METRICS` vale solo per calcolare le metriche.

3. **Metriche globali (`gf_*`)**
   - `gf_n_nodes`: numero di nodi (N)
   - `gf_binary_density`: densità binaria del grafo dopo soglia  
     \[
     \frac{E}{N(N-1)/2}
     \]
   - `gf_total_strength`: somma dei pesi (solo archi sopra soglia, triangolo superiore)
   - `gf_mean_strength`: media della **strength** per nodo (somma pesi incidenti al nodo, sopra soglia)
   - `gf_charpath_len_w`: lunghezza media dei cammini minimi pesata  
     - distanza definita come `length = 1/weight`
   - `gf_global_eff_w`: efficienza globale pesata  
     - media di \(1/d_{ij}\) su tutte le coppie connesse
   - `gf_transitivity_bin`: transitività (clustering globale) su grafo binario
   - `gf_avg_weighted_clust`: media del clustering coefficient pesato
   - `gf_n_communities`: numero comunità (greedy modularity su grafo binario, se possibile)
   - `gf_modularity_bin`: modularità delle comunità (grafo binario, se possibile)

4. **Metriche nodali “flattened” (`*_nXXX`)**
   Per ogni nodo vengono create colonne dedicate:
   - `degree_bin_n000`, `strength_n000`, ..., fino a `n{N-1}`

   Metriche nodali:
   - `degree_bin`: grado sul grafo binario (archi sopra soglia)
   - `strength`: somma pesi incidenti (sopra soglia)
   - `clustering_w`: clustering coefficient pesato
   - `betweenness_len`: betweenness su grafo con `length=1/weight`
   - `eigenvector_w`: eigenvector centrality pesata (se fallisce → 0)
   - `local_eff_bin`: efficienza locale binaria del nodo (sui vicini)

---

## Matching ID ↔ label

Gli ID vengono “canonizzati” con `canon_id()`:
- prova a estrarre cifre dal nome file (es. `PTE_001.csv` → `1`)
- altrimenti rimuove prefissi tipo `sub`, `patient`, `pte`, ecc.

Se un file matrice non trova la label corrispondente nel label file, viene **saltato**.

---
