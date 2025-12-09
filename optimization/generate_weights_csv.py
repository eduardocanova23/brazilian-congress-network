# build_data.py
import networkx as nx
from build_optimization_data import build_optimization_data   # a função que fiz para você

G_vote = nx.read_gexf("../data/networks/covoting-2019_2020_2021_2022-20251208-051415.gexf")
G_auth = nx.read_gexf("../data/networks/coauthorship-network-2019_2020_2021_2022-20251208-051609.gexf")

nodes_df, edges_df = build_optimization_data(G_vote, G_auth)

nodes_df.to_csv("../data/optimization/nodes.csv", index=False)
edges_df.to_csv("../data/optimization/edges.csv", index=False)

print("Arquivos gerados com sucesso!")
