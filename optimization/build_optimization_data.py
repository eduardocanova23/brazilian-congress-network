import networkx as nx
import pandas as pd
from typing import Tuple

def build_optimization_data(
    G_vote: nx.Graph,
    G_auth: nx.Graph,
    alpha: float = 0.035,   # peso da covotação no grau combinado (para custo)
    gamma: float = 0.035,   # peso da covotação no peso de aresta combinado (para coesão)
    epsilon: float = 1e-6 # para evitar divisão por zero
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    A partir de duas redes (covotação e coautoria), constrói:
      - nodes_df: id, c, v
      - edges_df: u, v, w_vote, w_auth, w_comb

    G_vote: grafo de covotação (nx.Graph) com atributo 'weight' nas arestas
    G_auth: grafo de coautoria (nx.Graph) com atributo 'weight' nas arestas
    alpha: peso da covotação no grau combinado (para custo)
    gamma: peso da covotação no peso combinado de aresta (para coesão)
    """

    # 1. Conjunto de nós: união dos dois grafos
    all_nodes = sorted(set(G_vote.nodes()) | set(G_auth.nodes()))

    # 2. Construir dicionários de pesos de aresta para cada rede
    #    Usamos tupla ordenada (min, max) para garantir consistência
    def edge_weight_dict(G: nx.Graph) -> dict:
        w = {}
        for u, v, data in G.edges(data=True):
            a, b = sorted((u, v))
            w[(a, b)] = w.get((a, b), 0.0) + float(data.get("weight", 0.0))
        return w

    w_vote_dict = edge_weight_dict(G_vote)
    w_auth_dict = edge_weight_dict(G_auth)

    # 3. Conjunto de arestas: união das arestas das duas redes
    all_edges = sorted(set(w_vote_dict.keys()) | set(w_auth_dict.keys()))

    # 4. Montar DataFrame de arestas com w_vote, w_auth e w_comb
    rows_edges = []
    for (u, v) in all_edges:
        w_vote = w_vote_dict.get((u, v), 0.0)
        w_auth = w_auth_dict.get((u, v), 0.0)
        w_comb = gamma * w_vote + (1.0 - gamma) * w_auth
        rows_edges.append({
            "u": u,
            "v": v,
            "w_vote": w_vote,
            "w_auth": w_auth,
            "w_comb": w_comb,
        })

    edges_df = pd.DataFrame(rows_edges)

    # 5. Graus ponderados nas duas redes (usando w_vote e w_auth)
    #    Como já temos edges_df, calculamos os graus a partir dela.
    #    Lembrando que o grafo é não dirigido: cada aresta contribui para u e para v.
    deg_vote = {node: 0.0 for node in all_nodes}
    deg_auth = {node: 0.0 for node in all_nodes}

    for _, row in edges_df.iterrows():
        u = row["u"]
        v = row["v"]
        wv = row["w_vote"]
        wa = row["w_auth"]
        deg_vote[u] += wv
        deg_vote[v] += wv
        deg_auth[u] += wa
        deg_auth[v] += wa

    # 6. Grau combinado por nó
    #    d_comb = alpha * d_vote + (1 - alpha) * d_auth
    rows_nodes = []
    for node in all_nodes:
        d_vote = deg_vote[node]
        d_auth = deg_auth[node]
        d_comb = alpha * d_vote + (1.0 - alpha) * d_auth

        # Custo inversamente proporcional ao grau combinado
        c_i = 1.0 / (d_comb + epsilon)

        # Peso do voto (para PEC, tipicamente 1 para todos)
        v_i = 1

        rows_nodes.append({
            "id": node,
            "c": c_i,
            "v": v_i,
        })

    nodes_df = pd.DataFrame(rows_nodes)

    return nodes_df, edges_df