# Wide Graph Feature Builder (`final.csv`)

Questo script legge una serie di **matrici di connettività** (una per paziente, salvata come `.csv`) e un file di **etichette** (`labels.csv`), calcola **feature di grafo** (globali + nodali) e crea un unico dataset in formato **wide** chiamato `final.csv`, pronto per ML.

---

## Input

- **`LABELS_CSV`**: CSV con colonne *ID paziente* e *label* (lo script prova ad auto-detectare i nomi colonna più comuni, oppure puoi forzarli con `ID_COL_HINT` e `LABEL_COL_HINT`).
- **`MAT_DIR`**: cartella contenente le matrici di ogni paziente in formato `*.csv`.
  - Ogni file deve contenere una **matrice quadrata NxN** (pesi delle connessioni tra nodi).

---

## Output (`final.csv`)

Ogni riga corrisponde a un paziente e contiene:

1. **Identificativi**
   - `id`: ID canonizzato estratto dal nome file / stringa ID
   - `label`: etichetta associata al paziente

2. **Edge features (triangolo superiore)**
   - `edge_0 ... edge_{E-1}`: tutti i valori della matrice nel **triangolo superiore** (con `k=1`, quindi esclusa la diagonale).
   - Nota: gli edge vengono salvati **sempre tutti** (non sogliati). La soglia `EDGE_MIN_FOR_METRICS` vale solo per calcolare le metriche.

3. **Metriche globali (`gf_*`)**
   - `gf_n_nodes`: numero di nodi (N)
   - `gf_binary_density`: densità binaria del grafo dopo soglia  
     \[
     \frac{E}{N(N-1)/2}
     \]
     dove \(E\) è il numero di archi con peso > `EDGE_MIN_FOR_METRICS`.
   - `gf_total_strength`: somma dei pesi (solo archi sopra soglia, triangolo superiore)
   - `gf_mean_strength`: media della **strength** per nodo (somma pesi incidenti al nodo, sopra soglia)
   - `gf_charpath_len_w`: **lunghezza media dei cammini minimi** pesata  
     - distanza definita come `length = 1/weight` (più peso ⇒ più “vicino”)
     - calcolata con Dijkstra su tutte le coppie connesse
   - `gf_global_eff_w`: **efficienza globale** pesata  
     - media di \(1/d_{ij}\) su tutte le coppie connesse (con \(d_{ij}\) da `length=1/weight`)
   - `gf_transitivity_bin`: **transitività** (clustering globale) su grafo binario
   - `gf_avg_weighted_clust`: media del **clustering coefficient pesato** (NetworkX)
   - `gf_n_communities`: numero di comunità trovate con greedy modularity (su grafo binario, se possibile)
   - `gf_modularity_bin`: **modularità** delle comunità (su grafo binario, se possibile)

4. **Metriche nodali “flattened” (`*_nXXX`)**
   Le metriche nodali non vengono aggregate: per ogni nodo `n` vengono create colonne dedicate.
   Esempio: `degree_bin_n000`, `degree_bin_n001`, ..., `degree_bin_n{N-1}`

   Metriche calcolate per nodo:
   - `degree_bin`: grado sul grafo binario (numero archi sopra soglia)
   - `strength`: somma pesi degli archi incidenti (sopra soglia)
   - `clustering_w`: clustering coefficient pesato (NetworkX)
   - `betweenness_len`: betweenness centrality calcolata su grafo con `length=1/weight`
   - `eigenvector_w`: eigenvector centrality pesata (se fallisce viene messa a 0)
   - `local_eff_bin`: **efficienza locale binaria** del nodo:
     - si considera il sottografo dei suoi vicini (binario)
     - si calcola l’efficienza media tra i vicini come media di \(1/d\) nel sottografo

---

## Pre-processing della matrice

Per ogni matrice:
- viene forzata la conversione numerica (valori non numerici → 0)
- viene simmetrizzata: `A = 0.5 * (A + A.T)`
- se `ZERO_DIAG=True` la diagonale viene posta a 0
- se `CLIP_NEGATIVES=True` i pesi negativi vengono posti a 0

---

## Matching ID ↔ label

Gli ID vengono “canonizzati” con `canon_id()`:
- tenta di estrarre cifre dal nome file (es. `PTE_001.csv` → `1`)
- altrimenti pulisce prefissi tipo `sub`, `patient`, `pte`, ecc.

Se un file matrice non trova la label corrispondente nel label file, viene **saltato**.

---

## Note ML (anti-leakage)

Lo script può opzionalmente fare z-score finale (`ZSCORE_FINAL=True`), ma in generale:
- **scaling / feature selection** vanno fatti **dentro i fold** di cross-validation,
  per evitare data leakage.

---
