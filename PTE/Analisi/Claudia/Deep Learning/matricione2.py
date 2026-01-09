import os
import numpy as np
import pandas as pd
import networkx as nx
import torch
from torch_geometric.data import Data
from tqdm import tqdm  # <-- barra di avanzamento

# Se c'è GPU, usa quella
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# ----------------------------
# Leggi Excel e file
# ----------------------------
df = pd.read_excel(
    "C:/Users/yuyuy/Desktop/Cartelle/Uni/Magistrale/PTEe/MATPTE/label.xlsx"
)

df["ID_num"] = df["Patient"].str.split("-").str[1].astype(int)
df["ID_num"] = df["ID_num"].apply(lambda x: f"{x:04d}")

base_path = "C:/Users/yuyuy/Desktop/Cartelle/Uni/Magistrale/PTEe/MATPTE"
file_names_only = os.listdir(base_path)

def trova_file(id_num):
    matches = [f for f in file_names_only if f"sub-{id_num}" in f]
    return matches[0] if len(matches) > 0 else np.nan

df["Matadi_File"] = df["ID_num"].apply(trova_file)
df = df.dropna()
dfcut = df[["Label", "Matadi_File"]].copy()

def leggi_matrice(nome_file):
    full_path = os.path.join(base_path, nome_file)
    mat = pd.read_csv(full_path, header=None)
    mat = mat.select_dtypes(include=[np.number])
    return mat.to_numpy()

dfcut["matrice"] = dfcut["Matadi_File"].apply(leggi_matrice)

# ----------------------------
# Funzioni di feature
# ----------------------------
def compute_node_features(A):
    G = nx.from_numpy_array(A)
    for u, v, d in G.edges(data=True):
        w = d.get("weight", 1.0)
        d["inv_weight"] = 1.0 / w if w != 0 else 0.0

    strength_vals = dict(G.degree(weight="weight"))
    closeness_vals = nx.closeness_centrality(G, distance="inv_weight")
    betweenness_vals = nx.betweenness_centrality(G, weight="inv_weight")
    eig_vals = nx.eigenvector_centrality(G, weight="weight", max_iter=1000, tol=1e-6)
    clustering_vals = nx.clustering(G, weight="weight")
    dist_mat = dict(nx.all_pairs_dijkstra_path_length(G, weight="inv_weight"))
    avg_path_len = {node: np.mean(list(dist.values())) for node, dist in dist_mat.items()}

    features = [
        [
            strength_vals[node],
            closeness_vals[node],
            betweenness_vals[node],
            eig_vals[node],
            clustering_vals[node],
            avg_path_len[node],
        ]
        for node in G.nodes()
    ]

    # Sposta su device
    return torch.tensor(features, dtype=torch.float, device=device)

def adj_to_edge_index(A):
    A = torch.tensor(A, dtype=torch.float, device=device)
    mask = A > 0
    edge_index = mask.nonzero(as_tuple=False).t()
    edge_weight = A[mask]
    return edge_index, edge_weight

def build_pyg_graph(A, label):
    x = compute_node_features(A)
    edge_index, edge_weight = adj_to_edge_index(A)

    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_weight,
        y=torch.tensor([label], dtype=torch.long, device=device)
    )
    return data

# ----------------------------
# Costruisci grafi con barra di avanzamento
# ----------------------------
graphs = []

for _, row in tqdm(dfcut.iterrows(), total=len(dfcut), desc="Building graphs"):
    A = row["matrice"]
    label = row["Label"]
    graphs.append(build_pyg_graph(A, label))


import matplotlib.pyplot as plt
from torch_geometric.utils import to_networkx

# Prendi un grafo a caso dalla lista
graph = graphs[0]  # il primo grafo

# Converti da PyG a NetworkX (grafo non diretto)
G_nx = to_networkx(graph, to_undirected=True)

# Aggiungi i pesi degli archi
edge_weights = graph.edge_attr.cpu().numpy() if graph.edge_attr is not None else None

# Disegna il grafo
plt.figure(figsize=(10, 10))
pos = nx.spring_layout(G_nx, seed=42)  # layout tipo “molla”
nx.draw(
    G_nx,
    pos,
    with_labels=True,
    node_color='skyblue',
    node_size=500,
    edge_color='gray',
)
if edge_weights is not None:
    # disegna spessore archi proporzionale al peso
    nx.draw_networkx_edges(G_nx, pos, width=edge_weights*5)

plt.title("Visualizzazione grafo del paziente")
plt.axis('off')
plt.show()
