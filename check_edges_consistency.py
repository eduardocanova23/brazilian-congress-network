import pandas as pd
import networkx as nx
from collections import defaultdict

# 1) Ajuste aqui o nome do arquivo GEXF que você quer testar
GEXF_PATH = "data/networks/coauthorship-network-2025-12-05.gexf"

print("Carregando grafo...")
G = nx.read_gexf(GEXF_PATH)
print(f"Nós no grafo: {G.number_of_nodes()}")
print(f"Arestas no grafo: {G.number_of_edges()}")

# 2) Conjunto de nós do grafo (ids de deputados, como strings no GEXF)
graph_nodes = set(G.nodes())
print(f"Exemplo de nós no grafo: {list(graph_nodes)[:5]}")

print("\nCarregando authors_info.csv...")
authors = pd.read_csv("data/authors_info.csv")

# 3) Garantir tipos das colunas
authors["idAutor"] = authors["idAutor"].astype(int)
authors["idProposicao"] = authors["idProposicao"].astype(int)

print("Carregando proposals_info.csv...")
proposals = pd.read_csv("data/proposals_info.csv", encoding="utf-8")

# Vamos usar apenas as proposições que aparecem no proposals_info
valid_proposals = set(proposals["id"].astype(int))
print(f"Total de proposições em proposals_info: {len(valid_proposals)}")

# 4) Construir mapa: proposicao -> lista de autores
print("Agrupando autores por proposição...")
prop_to_authors = defaultdict(list)

for _, row in authors.iterrows():
    pid = int(row["idProposicao"])
    aid = int(row["idAutor"])
    if pid in valid_proposals:
        prop_to_authors[pid].append(aid)

# 5) A partir de prop_to_authors, gerar o conjunto de pares de coautores reais
print("Construindo conjunto de pares de coautores reais (ground truth)...")
real_pairs = set()
for pid, authors_list in prop_to_authors.items():
    # interessam apenas proposições com mais de um autor
    if len(authors_list) > 1:
        # todos os pares não direcionados
        n = len(authors_list)
        for i in range(n):
            for j in range(i + 1, n):
                a = str(authors_list[i])
                b = str(authors_list[j])
                # só vamos considerar pares em que ambos aparecem no grafo
                if a in graph_nodes and b in graph_nodes:
                    if a < b:
                        real_pairs.add((a, b))
                    else:
                        real_pairs.add((b, a))

print(f"Total de pares de coautores reais (restritos a nós presentes no grafo): {len(real_pairs)}")

# 6) Extrair pares de arestas do grafo como pares não direcionados
print("Extraindo pares de arestas do grafo...")
graph_pairs = set()
for u, v in G.edges():
    u = str(u)
    v = str(v)
    if u < v:
        graph_pairs.add((u, v))
    else:
        graph_pairs.add((v, u))

print(f"Total de pares no grafo (não direcionados): {len(graph_pairs)}")

# 7) Comparações

only_in_graph = graph_pairs - real_pairs
only_in_real = real_pairs - graph_pairs

print("\nResumo da comparação:")
print(f"Arestas no grafo que NÃO aparecem como coautoria real: {len(only_in_graph)}")
print(f"Pares de coautoria real que NÃO viraram aresta no grafo: {len(only_in_real)}")

# Mostrar alguns exemplos, se houver
max_show = 10

if only_in_graph:
    print("\nExemplos de arestas no grafo sem coautoria real (até 10):")
    for i, (a, b) in enumerate(list(only_in_graph)[:max_show]):
        print(f"  ({a}, {b})")
        if i + 1 >= max_show:
            break

if only_in_real:
    print("\nExemplos de coautorias reais que não viraram aresta no grafo (até 10):")
    for i, (a, b) in enumerate(list(only_in_real)[:max_show]):
        print(f"  ({a}, {b})")
        if i + 1 >= max_show:
            break

print("\nTeste concluído.")
import pandas as pd
import networkx as nx
from collections import defaultdict

# 1) Ajuste aqui o nome do arquivo GEXF que você quer testar
GEXF_PATH = "data/networks/coauthorship-network-2025-12-05.gexf"

print("Carregando grafo...")
G = nx.read_gexf(GEXF_PATH)
print(f"Nós no grafo: {G.number_of_nodes()}")
print(f"Arestas no grafo: {G.number_of_edges()}")

# 2) Conjunto de nós do grafo (ids de deputados, como strings no GEXF)
graph_nodes = set(G.nodes())
print(f"Exemplo de nós no grafo: {list(graph_nodes)[:5]}")

print("\nCarregando authors_info.csv...")
authors = pd.read_csv("data/authors_info.csv")

# 3) Garantir tipos das colunas
authors["idAutor"] = authors["idAutor"].astype(int)
authors["idProposicao"] = authors["idProposicao"].astype(int)

print("Carregando proposals_info.csv...")
proposals = pd.read_csv("data/proposals_info.csv", encoding="utf-8")

# Vamos usar apenas as proposições que aparecem no proposals_info
valid_proposals = set(proposals["id"].astype(int))
print(f"Total de proposições em proposals_info: {len(valid_proposals)}")

# 4) Construir mapa: proposicao -> lista de autores
print("Agrupando autores por proposição...")
prop_to_authors = defaultdict(list)

for _, row in authors.iterrows():
    pid = int(row["idProposicao"])
    aid = int(row["idAutor"])
    if pid in valid_proposals:
        prop_to_authors[pid].append(aid)

# 5) A partir de prop_to_authors, gerar o conjunto de pares de coautores reais
print("Construindo conjunto de pares de coautores reais (ground truth)...")
real_pairs = set()
for pid, authors_list in prop_to_authors.items():
    # interessam apenas proposições com mais de um autor
    if len(authors_list) > 1:
        # todos os pares não direcionados
        n = len(authors_list)
        for i in range(n):
            for j in range(i + 1, n):
                a = str(authors_list[i])
                b = str(authors_list[j])
                # só vamos considerar pares em que ambos aparecem no grafo
                if a in graph_nodes and b in graph_nodes:
                    if a < b:
                        real_pairs.add((a, b))
                    else:
                        real_pairs.add((b, a))

print(f"Total de pares de coautores reais (restritos a nós presentes no grafo): {len(real_pairs)}")

# 6) Extrair pares de arestas do grafo como pares não direcionados
print("Extraindo pares de arestas do grafo...")
graph_pairs = set()
for u, v in G.edges():
    u = str(u)
    v = str(v)
    if u < v:
        graph_pairs.add((u, v))
    else:
        graph_pairs.add((v, u))

print(f"Total de pares no grafo (não direcionados): {len(graph_pairs)}")

# 7) Comparações

only_in_graph = graph_pairs - real_pairs
only_in_real = real_pairs - graph_pairs

print("\nResumo da comparação:")
print(f"Arestas no grafo que NÃO aparecem como coautoria real: {len(only_in_graph)}")
print(f"Pares de coautoria real que NÃO viraram aresta no grafo: {len(only_in_real)}")

# Mostrar alguns exemplos, se houver
max_show = 10

if only_in_graph:
    print("\nExemplos de arestas no grafo sem coautoria real (até 10):")
    for i, (a, b) in enumerate(list(only_in_graph)[:max_show]):
        print(f"  ({a}, {b})")
        if i + 1 >= max_show:
            break

if only_in_real:
    print("\nExemplos de coautorias reais que não viraram aresta no grafo (até 10):")
    for i, (a, b) in enumerate(list(only_in_real)[:max_show]):
        print(f"  ({a}, {b})")
        if i + 1 >= max_show:
            break

print("\nTeste concluído.")
