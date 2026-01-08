import os
import numpy as np
import pandas as pd
import networkx as nx

# Leggo il file Excel
df = pd.read_excel(
    "C:/Users/yuyuy/Desktop/Cartelle/Uni/Magistrale/Articolo/MATPTE/label.xlsx"
)

# Estrai la parte numerica dell'ID paziente
df["ID_num"] = df["Patient"].str.split("-").str[1].astype(int)

# Converto in formato a 4 cifre con zeri iniziali
df["ID_num"] = df["ID_num"].apply(lambda x: f"{x:04d}")

# Prendo i file dalla cartella
base_path = "C:/Users/yuyuy/Desktop/Cartelle/Uni/Magistrale/Articolo/MATPTE"
path_matadi = [os.path.join(base_path, f) for f in os.listdir(base_path)]
file_names_only = [os.path.basename(f) for f in path_matadi]

# Associa pazienti e matrici
def trova_file(id_num):
    matches = [f for f in file_names_only if f"sub-{id_num}" in f]
    return matches[0] if len(matches) > 0 else np.nan

df["Matadi_File"] = df["ID_num"].apply(trova_file)

# Rimuovo NA
df = df.dropna()

# Tengo solo ciò che serve
dfcut = df[["Label", "Matadi_File"]].copy()

def leggi_matrice(nome_file):
    full_path = os.path.join(base_path, nome_file)
    try:
        mat = pd.read_csv(full_path, header=None)
        mat = mat.select_dtypes(include=[np.number])
        return mat.to_numpy()
    except Exception as e:
        print(f"Errore nel file {nome_file}: {e}")
        return None

dfcut["matrice"] = dfcut["Matadi_File"].apply(leggi_matrice)
matrici_sani = dfcut.loc[dfcut["Label"] == 0, "matrice"].tolist()
matrici_ad   = dfcut.loc[dfcut["Label"] == 1, "matrice"].tolist()


def rendi_simmetrica(mat):
    mat = mat.copy()
    i_lower = np.tril_indices_from(mat, -1)
    mat[i_lower] = mat.T[i_lower]
    return mat

matrici_sani = [rendi_simmetrica(m) for m in matrici_sani]
matrici_ad   = [rendi_simmetrica(m) for m in matrici_ad]

def metr_dens_nodi(gruppo, dens, nome_gruppo):
    risultati = []

    for i, mat in enumerate(gruppo, start=1):
        print(f"Analisi del paziente: {i}")

        mat = mat.copy()
        np.fill_diagonal(mat, 0)
        n = mat.shape[0]

        # --- Threshold come nel secondo programma ---
        upper_idx = np.triu_indices(n, 1)
        upper_vals = mat[upper_idx]

        n_total = len(upper_vals)
        n_keep = int(np.floor(n_total * dens))
        keep_idx = np.argsort(upper_vals)[::-1][:n_keep]

        mat_sparse = np.zeros_like(mat)
        for k in keep_idx:
            ii = upper_idx[0][k]
            jj = upper_idx[1][k]
            mat_sparse[ii, jj] = mat[ii, jj]
            mat_sparse[jj, ii] = mat[ii, jj]

        # --- Crea grafo ---
        G = nx.from_numpy_array(mat_sparse)
        for u, v, d in G.edges(data=True):
            d["weight"] = mat_sparse[u, v]
            d["inv_weight"] = 1.0 / d["weight"]
        

        # --- Metriche ---
        strength_vals = dict(G.degree(weight="weight"))
        closeness_vals = nx.closeness_centrality(G, distance="inv_weight")
        betweenness_vals = nx.betweenness_centrality(G, weight="inv_weight")

        eig_vals = nx.eigenvector_centrality(
            G,
            weight="weight",
            max_iter=1000,
            tol=1e-6
            )

        clustering_vals = nx.clustering(G, weight="weight")

        dist_mat = dict(nx.all_pairs_dijkstra_path_length(G, weight="inv_weight"))
        avg_path_len = {
            node: np.mean(list(dist.values())) for node, dist in dist_mat.items()
        }

        # --- Costruisco dataframe ---
        row = {
            "Paziente": i,
            "Diagnosi": nome_gruppo,
            "Densita": dens
        }

        for nodo in range(n):
            row[f"Strength_{nodo+1}"] = strength_vals.get(nodo, np.nan)
            row[f"Closeness_{nodo+1}"] = closeness_vals.get(nodo, np.nan)
            row[f"Betweenness_{nodo+1}"] = betweenness_vals.get(nodo, np.nan)
            row[f"Eigenvector_{nodo+1}"] = eig_vals.get(nodo, np.nan)
            row[f"Clustering_{nodo+1}"] = clustering_vals.get(nodo, np.nan)
            row[f"AvgPathLen_{nodo+1}"] = avg_path_len.get(nodo, np.nan)

        risultati.append(pd.DataFrame([row]))

    return pd.concat(risultati, ignore_index=True)

#Select the density range you want.
for d in np.arange(0.25, 0.27, 0.01):
    normal = metr_dens_nodi(matrici_sani, d, "noPTE")
    ad = metr_dens_nodi(matrici_ad, d, "PTE")

    tabella_completa = pd.concat([normal, ad], ignore_index=True)

    nome_file = f"matricePTE{int(d*100)}.csv"
    tabella_completa.to_csv(nome_file, index=False)

    print("Creato file:", nome_file)

