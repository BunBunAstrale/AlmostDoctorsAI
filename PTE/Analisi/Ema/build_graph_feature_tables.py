#!/usr/bin/env python3
"""
Crea un unico CSV "wide" (final.csv) con:
- id, label
- tutti gli edge (triangolo superiore): edge_0..edge_{E-1}
- tutte le metriche globali: gf_*
- tutte le metriche nodali (NON aggregate), appiattite: *_n%03d

Dipendenze: numpy, pandas, networkx
"""

import os
import re
import glob
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx


# ============================
# CONFIG (MODIFICA QUI)
# ============================
LABELS_CSV = "labels_claudia.csv"   
MAT_DIR    = "./PTE"                      
OUT_CSV    = "final.csv"                      

EDGE_MIN_FOR_METRICS = 0.0    # soglia usata SOLO per calcolare metriche (non per salvare edge_*)
ZERO_DIAG = True             
CLIP_NEGATIVES = True         # mette a 0 i pesi negativi
ZSCORE_FINAL = False          # se vuoi z-score sulle feature finali (esclusi id/label)

# Se vuoi forzare le colonne del labels file:
ID_COL_HINT = None            # es: "Paziente"
LABEL_COL_HINT = None         # es: "Label"
# ============================


# -------------------------- Utility ID --------------------------
def canon_id(s: str) -> str:
    """Estrae un id canonico da stringa/nome file."""
    s = str(s).strip()
    b = os.path.splitext(os.path.basename(s))[0]
    digs = re.findall(r"\d+", b)
    if digs:
        d = "".join(digs).lstrip("0")
        return d if d else "0"

    b = re.sub(r"[\s\-_]+", "", b.lower())
    for pref in ("sub", "subject", "pt", "pte", "id", "patient", "paziente"):
        if b.startswith(pref):
            b = b[len(pref):]
    b = b.lstrip("0")
    return b if b else "0"


def load_labels(labels_csv: str, id_col_hint=None, label_col_hint=None) -> dict:
    """
    Carica labels da CSV e restituisce dict {canon_id: label}.
    Auto-detect colonne comuni, oppure puoi passarle in hint.
    """
    df = pd.read_csv(labels_csv, dtype=str)

    id_col = id_col_hint or next(
        (c for c in ["Paziente", "ID", "Id", "Subject", "subject", "patient", "Patient"] if c in df.columns),
        None
    )
    label_col = label_col_hint or next(
        (c for c in ["Label", "label", "y", "Y", "Class", "class", "Classe"] if c in df.columns),
        None
    )

    if id_col is None or label_col is None:
        raise ValueError(
            f"labels_csv deve avere colonne ID e LABEL. "
            f"Colonne trovate: {list(df.columns)}. "
            f"Puoi forzare ID_COL_HINT e LABEL_COL_HINT nel config."
        )

    df[id_col] = df[id_col].astype(str).str.strip()
    df[label_col] = df[label_col].astype(str).str.strip()

    df["__canon__"] = df[id_col].map(canon_id)
    df = df.drop_duplicates(subset="__canon__", keep="last")

    return dict(zip(df["__canon__"], df[label_col]))


# -------------------------- IO matrice --------------------------
def load_connectivity_csv(fp: str, zero_diag: bool = True, clip_negatives: bool = True) -> np.ndarray:
    """
    Carica matrice NxN da CSV. Robusto a:
    - header presenti (si tenta coercizione numerica)
    - NaN (riempiti a 0)
    """
    raw = pd.read_csv(fp, header=None)

    # coercizione numerica: eventuali stringhe -> NaN
    A = raw.apply(pd.to_numeric, errors="coerce").values.astype(float)
    A = np.nan_to_num(A, nan=0.0, posinf=0.0, neginf=0.0)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError(f"Matrice non quadrata in {fp}: shape={A.shape}")

    # simmetrizza
    A = 0.5 * (A + A.T)

    if zero_diag:
        np.fill_diagonal(A, 0.0)
    if clip_negatives:
        A[A < 0] = 0.0

    return A


def upper_triangle_vector(A: np.ndarray, k: int = 1):
    iu, ju = np.triu_indices_from(A, k=k)
    return A[iu, ju].astype(float), iu, ju


# -------------------------- Grafi & metriche --------------------------
def build_graphs_from_matrix(A: np.ndarray, edge_min: float = 0.0):
    """
    G_w: pesato (weight=w)
    G_b: binario (weight=1)
    H_len: pesato con 'length' = 1/w per distanze
    """
    n = A.shape[0]
    G_w = nx.Graph(); G_w.add_nodes_from(range(n))
    G_b = nx.Graph(); G_b.add_nodes_from(range(n))
    H_len = nx.Graph(); H_len.add_nodes_from(range(n))

    for i in range(n):
        for j in range(i + 1, n):
            w = float(A[i, j])
            if w > edge_min:
                G_w.add_edge(i, j, weight=w)
                G_b.add_edge(i, j, weight=1.0)
                H_len.add_edge(i, j, weight=w, length=(1.0 / w))

    return G_w, G_b, H_len


def binary_density(A: np.ndarray, edge_min: float = 0.0) -> float:
    N = A.shape[0]
    if N <= 1:
        return 0.0
    E = int(np.count_nonzero(np.triu(A, 1) > edge_min))
    return E / (N * (N - 1) / 2.0)


def characteristic_path_length_weighted(H_len: nx.Graph) -> float:
    if H_len.number_of_edges() == 0 or H_len.number_of_nodes() <= 1:
        return np.nan

    lengths = dict(nx.all_pairs_dijkstra_path_length(H_len, weight="length"))
    nodes = list(H_len.nodes())

    dists = []
    for i_idx in range(len(nodes)):
        for j_idx in range(i_idx + 1, len(nodes)):
            i, j = nodes[i_idx], nodes[j_idx]
            dij = lengths.get(i, {}).get(j, None)
            if dij is not None:
                dists.append(dij)

    return float(np.mean(dists)) if dists else np.nan


def global_efficiency_weighted(H_len: nx.Graph) -> float:
    if H_len.number_of_edges() == 0 or H_len.number_of_nodes() <= 1:
        return np.nan

    lengths = dict(nx.all_pairs_dijkstra_path_length(H_len, weight="length"))
    nodes = list(H_len.nodes())

    inv_d = []
    for i_idx in range(len(nodes)):
        for j_idx in range(i_idx + 1, len(nodes)):
            i, j = nodes[i_idx], nodes[j_idx]
            dij = lengths.get(i, {}).get(j, None)
            if dij is not None and dij > 0:
                inv_d.append(1.0 / dij)

    return float(np.mean(inv_d)) if inv_d else np.nan


def global_features(A: np.ndarray, edge_min: float = 0.0) -> dict:
    n = A.shape[0]
    G_w, G_b, H_len = build_graphs_from_matrix(A, edge_min=edge_min)

    # strength per nodo (solo archi > edge_min)
    strength_per_node = (A * (A > edge_min)).sum(axis=1)

    gf = {
        "gf_n_nodes": int(n),
        "gf_binary_density": float(binary_density(A, edge_min=edge_min)),
        "gf_total_strength": float(np.sum(np.triu(A, 1) * (np.triu(A, 1) > edge_min))),
        "gf_mean_strength": float(np.mean(strength_per_node)) if n > 0 else np.nan,
        "gf_charpath_len_w": characteristic_path_length_weighted(H_len),
        "gf_global_eff_w": global_efficiency_weighted(H_len),
        "gf_transitivity_bin": nx.transitivity(G_b) if G_b.number_of_edges() > 0 else np.nan,
    }

    # clustering pesato medio
    if G_w.number_of_edges() > 0:
        cl_w = nx.clustering(G_w, weight="weight")
        gf["gf_avg_weighted_clust"] = float(np.mean(list(cl_w.values()))) if cl_w else np.nan
    else:
        gf["gf_avg_weighted_clust"] = np.nan

    # modularità binaria (best effort)
    try:
        from networkx.algorithms.community import greedy_modularity_communities, modularity
        if G_b.number_of_edges() > 0:
            comms = list(greedy_modularity_communities(G_b))
            gf["gf_n_communities"] = int(len(comms))
            gf["gf_modularity_bin"] = float(modularity(G_b, comms))
        else:
            gf["gf_n_communities"] = np.nan
            gf["gf_modularity_bin"] = np.nan
    except Exception:
        gf["gf_n_communities"] = np.nan
        gf["gf_modularity_bin"] = np.nan

    return gf


def nodal_metrics(A: np.ndarray, edge_min: float = 0.0) -> pd.DataFrame:
    G_w, G_b, H_len = build_graphs_from_matrix(A, edge_min=edge_min)
    n = A.shape[0]
    all_nodes = list(range(n))

    deg_bin = pd.Series(dict(G_b.degree())).reindex(all_nodes).fillna(0).astype(float)
    strength = pd.Series(dict(G_w.degree(weight="weight"))).reindex(all_nodes).fillna(0.0)

    if G_w.number_of_edges() > 0:
        clust_w = pd.Series(nx.clustering(G_w, weight="weight")).reindex(all_nodes).fillna(0.0)
    else:
        clust_w = pd.Series(index=all_nodes, dtype=float).fillna(0.0)

    if H_len.number_of_edges() > 0:
        btw_len = pd.Series(nx.betweenness_centrality(H_len, weight="length", normalized=True)) \
            .reindex(all_nodes).fillna(0.0)
    else:
        btw_len = pd.Series(index=all_nodes, dtype=float).fillna(0.0)

    try:
        if G_w.number_of_edges() > 0:
            eig_cent = pd.Series(nx.eigenvector_centrality_numpy(G_w, weight="weight")) \
                .reindex(all_nodes).fillna(0.0)
        else:
            eig_cent = pd.Series(index=all_nodes, dtype=float).fillna(0.0)
    except Exception:
        eig_cent = pd.Series(index=all_nodes, dtype=float).fillna(0.0)

    # local efficiency per nodo su binario
    def node_local_efficiency_binary(Gb: nx.Graph):
        eff = {}
        for u in Gb.nodes():
            nbrs = set(Gb.neighbors(u))
            if len(nbrs) <= 1:
                eff[u] = 0.0
                continue

            sub = Gb.subgraph(nbrs).copy()
            lengths = dict(nx.all_pairs_shortest_path_length(sub))

            inv_d = []
            nodes = list(sub.nodes())
            for i_idx in range(len(nodes)):
                for j_idx in range(i_idx + 1, len(nodes)):
                    i, j = nodes[i_idx], nodes[j_idx]
                    dij = lengths.get(i, {}).get(j, None)
                    if dij is not None and dij > 0:
                        inv_d.append(1.0 / dij)

            m = len(nodes) * (len(nodes) - 1) / 2.0
            eff[u] = float(np.sum(inv_d) / m) if m > 0 else 0.0
        return eff

    loc_eff_bin = pd.Series(node_local_efficiency_binary(G_b)).reindex(all_nodes).fillna(0.0)

    return pd.DataFrame({
        "node": all_nodes,
        "degree_bin": deg_bin.values,
        "strength": strength.values,
        "clustering_w": clust_w.values,
        "betweenness_len": btw_len.values,
        "eigenvector_w": eig_cent.values,
        "local_eff_bin": loc_eff_bin.values,
    })


# -------------------------- Flatten nodal -> wide --------------------------
def flatten_nodal_wide(df_nodes: pd.DataFrame, fmt="{:03d}") -> dict:
    """
    Converte il dataframe per-nodo in dict {col_wide: valore}, con suffissi *_n000, *_n001, ...
    """
    out = {}
    for _, row in df_nodes.iterrows():
        n_id = fmt.format(int(row["node"]))
        for c in df_nodes.columns:
            if c == "node":
                continue
            v = row[c]
            out[f"{c}_n{n_id}"] = float(v) if pd.notna(v) else 0.0
    return out


# -------------------------- MAIN  --------------------------
def run():
    label_map = load_labels(LABELS_CSV, id_col_hint=ID_COL_HINT, label_col_hint=LABEL_COL_HINT)

    files = sorted(glob.glob(os.path.join(MAT_DIR, "*.csv")))
    if not files:
        raise FileNotFoundError(f"Nessun CSV trovato in MAT_DIR={MAT_DIR}")

    rows = []
    used, skipped_no_label, skipped_errors = 0, 0, 0
    edge_cols = None

    for fp in files:
        pid = canon_id(fp)
        lab = label_map.get(pid)

        if lab is None:
            skipped_no_label += 1
            continue

        try:
            # Matrice & edges
            A = load_connectivity_csv(fp, zero_diag=ZERO_DIAG, clip_negatives=CLIP_NEGATIVES)
            edge_vec, _, _ = upper_triangle_vector(A, k=1)

            if edge_cols is None:
                edge_cols = [f"edge_{k}" for k in range(edge_vec.size)]

            # Metriche
            gf = global_features(A, edge_min=EDGE_MIN_FOR_METRICS)
            nodes_df = nodal_metrics(A, edge_min=EDGE_MIN_FOR_METRICS)
            node_wide = flatten_nodal_wide(nodes_df, fmt="{:03d}")

            # Riga
            row = {"id": pid, "label": lab}
            row.update({edge_cols[k]: float(edge_vec[k]) for k in range(edge_vec.size)})
            row.update(gf)
            row.update(node_wide)

            rows.append(row)
            used += 1

        except Exception as e:
            skipped_errors += 1
            print(f"[WARN] Skip {fp} (id={pid}) per errore: {e}")

    if used == 0:
        raise RuntimeError("Nessun paziente processato: controlla matching ID tra labels e nomi file delle matrici.")

    df_all = pd.DataFrame(rows).sort_values("id").reset_index(drop=True)

    # Z-score finale (opzionale)
    if ZSCORE_FINAL:
        num_cols = df_all.columns.difference(["id", "label"])
        df_all[num_cols] = (df_all[num_cols] - df_all[num_cols].mean()) / (df_all[num_cols].std(ddof=0) + 1e-12)

    Path(os.path.dirname(OUT_CSV) or ".").mkdir(parents=True, exist_ok=True)
    df_all.to_csv(OUT_CSV, index=False)

    print(f"[OK] Pazienti processati: {used}")
    print(f"[OK] Saltati senza label: {skipped_no_label}")
    print(f"[OK] Saltati per errori: {skipped_errors}")
    print(f"[OK] Colonne finali: {df_all.shape[1]}  |  Edge per soggetto: {len(edge_cols)}")
    print(f"[OK] Salvato: {OUT_CSV}")
    print("[TIP] Scaling/feature selection falli dentro i fold di CV (anti-leakage).")


if __name__ == "__main__":
    run()
