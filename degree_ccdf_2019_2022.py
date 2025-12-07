import sys
import os
import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def compute_ccdf_from_degrees(degrees_array):
    """
    Recebe um array de graus (numpy) e retorna:
    - degrees_sorted: graus únicos ordenados crescentemente
    - ccdf: P(K >= k) para cada grau
    """
    unique_degrees, counts = np.unique(degrees_array, return_counts=True)
    total = counts.sum()

    # ordenar por grau crescente
    sorted_idx = np.argsort(unique_degrees)
    degrees_sorted = unique_degrees[sorted_idx]
    counts_sorted = counts[sorted_idx]

    # CCDF: P(K >= k)
    ccdf = []
    tail = total
    for c in counts_sorted:
        p = tail / total
        ccdf.append(p)
        tail -= c

    return degrees_sorted, np.array(ccdf)


def analyze_network(gexf_path, output_prefix=None):
    if output_prefix is None:
        base = os.path.basename(gexf_path)
        output_prefix = os.path.splitext(base)[0]

    print(f"Lendo rede de: {gexf_path}")
    G = nx.read_gexf(gexf_path)

    print(f"N nós: {G.number_of_nodes()}")
    print(f"N arestas: {G.number_of_edges()}")

    # graus não ponderados
    deg_unweighted = np.array([d for _, d in G.degree()])
    print("\n=== Grau NÃO ponderado ===")
    print(f"min: {deg_unweighted.min()}")
    print(f"max: {deg_unweighted.max()}")
    print(f"médio: {deg_unweighted.mean():.3f}")

    # graus ponderados (usando atributo 'weight')
    deg_weighted = np.array([d for _, d in G.degree(weight="weight")])
    print("\n=== Grau ponderado (weight) ===")
    print(f"min: {deg_weighted.min()}")
    print(f"max: {deg_weighted.max()}")
    print(f"médio: {deg_weighted.mean():.3f}")

    # ----------------------------------------------------
    # Distribuições de grau
    # ----------------------------------------------------
    # não ponderado
    u_degs, u_counts = np.unique(deg_unweighted, return_counts=True)
    total_nodes = len(deg_unweighted)
    df_deg_unweighted = pd.DataFrame({
        "grau": u_degs,
        "freq": u_counts,
        "prob": u_counts / total_nodes
    })

    # ponderado
    w_degs, w_counts = np.unique(deg_weighted, return_counts=True)
    df_deg_weighted = pd.DataFrame({
        "grau": w_degs,
        "freq": w_counts,
        "prob": w_counts / total_nodes
    })

    # ----------------------------------------------------
    # CCDFs (lineares)
    # ----------------------------------------------------
    u_k, u_ccdf = compute_ccdf_from_degrees(deg_unweighted)
    df_ccdf_unweighted = pd.DataFrame({
        "grau": u_k,
        "ccdf": u_ccdf
    })

    w_k, w_ccdf = compute_ccdf_from_degrees(deg_weighted)
    df_ccdf_weighted = pd.DataFrame({
        "grau": w_k,
        "ccdf": w_ccdf
    })

    # ----------------------------------------------------
    # Salvar CSVs
    # ----------------------------------------------------
    deg_unw_csv = f"{output_prefix}_degree_unweighted.csv"
    deg_w_csv = f"{output_prefix}_degree_weighted.csv"
    ccdf_unw_csv = f"{output_prefix}_ccdf_unweighted.csv"
    ccdf_w_csv = f"{output_prefix}_ccdf_weighted.csv"

    df_deg_unweighted.to_csv(deg_unw_csv, index=False)
    df_deg_weighted.to_csv(deg_w_csv, index=False)
    df_ccdf_unweighted.to_csv(ccdf_unw_csv, index=False)
    df_ccdf_weighted.to_csv(ccdf_w_csv, index=False)

    print(f"\nDistribuição de grau NÃO ponderado salva em: {deg_unw_csv}")
    print(f"Distribuição de grau ponderado salva em: {deg_w_csv}")
    print(f"CCDF NÃO ponderada salva em: {ccdf_unw_csv}")
    print(f"CCDF ponderada salva em: {ccdf_w_csv}")

    # ----------------------------------------------------
    # Gráficos CCDF (lineares, sem log-log)
    # ----------------------------------------------------
    # CCDF não ponderada
    plt.figure()
    plt.plot(df_ccdf_unweighted["grau"], df_ccdf_unweighted["ccdf"],
             marker="o", linestyle="none")
    plt.xlabel("Grau k (não ponderado)")
    plt.ylabel("P(K ≥ k)")
    plt.title(f"CCDF do grau não ponderado - {output_prefix}")
    plt.grid(True)
    ccdf_unw_png = f"{output_prefix}_ccdf_unweighted_linear.png"
    plt.savefig(ccdf_unw_png, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Gráfico CCDF NÃO ponderada salvo em: {ccdf_unw_png}")

    # CCDF ponderada
    plt.figure()
    plt.plot(df_ccdf_weighted["grau"], df_ccdf_weighted["ccdf"],
             marker="o", linestyle="none")
    plt.xlabel("Grau k (ponderado)")
    plt.ylabel("P(K ≥ k)")
    plt.title(f"CCDF do grau ponderado - {output_prefix}")
    plt.grid(True)
    ccdf_w_png = f"{output_prefix}_ccdf_weighted_linear.png"
    plt.savefig(ccdf_w_png, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Gráfico CCDF ponderada salvo em: {ccdf_w_png}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python degree_ccdf_both.py caminho_para_rede.gexf")
        sys.exit(1)

    gexf_path = sys.argv[1]
    analyze_network(gexf_path)
