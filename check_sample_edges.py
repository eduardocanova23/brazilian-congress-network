import pandas as pd
import networkx as nx
import random

GEXF_PATH = "data/networks/coauthorship-network-2025-12-05.gexf"

print("Carregando grafo...")
G = nx.read_gexf(GEXF_PATH)

authors = pd.read_csv("data/authors_info.csv")
authors["idAutor"] = authors["idAutor"].astype(int)
authors["idProposicao"] = authors["idProposicao"].astype(int)

proposals = pd.read_csv("data/proposals_info.csv", encoding="utf-8")
valid_proposals = set(proposals["id"].astype(int))

def coauthored_count(dep1, dep2):
    d1 = int(dep1)
    d2 = int(dep2)
    p1 = set(authors.loc[authors["idAutor"] == d1, "idProposicao"])
    p2 = set(authors.loc[authors["idAutor"] == d2, "idProposicao"])
    # restringe às proposições de proposals_info (tipos filtrados)
    p1 = p1 & valid_proposals
    p2 = p2 & valid_proposals
    return len(p1 & p2)

edges = list(G.edges(data=True))
print(f"Total de arestas: {len(edges)}")

print("\nAmostra de 10 arestas:")
for _ in range(10):
    u, v, data = random.choice(edges)
    w = data.get("weight", None)
    c = coauthored_count(u, v)
    print(f"({u}, {v}) -> weight no grafo = {w}, coautorias reais = {c}")
