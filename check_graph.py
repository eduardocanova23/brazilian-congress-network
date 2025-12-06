import networkx as nx

# ajuste o nome do arquivo para o .gexf mais recente
G = nx.read_gexf("data/networks/coauthorship-network-2025-12-05.gexf")

print("N nós:", G.number_of_nodes())
print("M arestas:", G.number_of_edges())
print("Dirigido?:", G.is_directed())
print("Tipo:", type(G))

avg_degree = 2 * G.number_of_edges() / G.number_of_nodes()
print("Grau médio:", avg_degree)
