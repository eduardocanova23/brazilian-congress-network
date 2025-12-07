import pandas as pd
import os

BASE_PROPOSALS = "data/proposals"
BASE_AUTHORS = "data/authors"

TIPOS_VALIDOS = ["PL", "PLP", "PLN", "PLV", "PEC"]


def resumo_coautoria_raw(ano: int):
    # caminhos dos arquivos brutos
    path_props = os.path.join(BASE_PROPOSALS, f"proposicoes-{ano}.csv")
    path_auth = os.path.join(BASE_AUTHORS, f"proposicoesAutores-{ano}.csv")

    if not os.path.exists(path_props):
        print(f"[{ano}] Arquivo de proposições não encontrado: {path_props}")
        return
    if not os.path.exists(path_auth):
        print(f"[{ano}] Arquivo de autores não encontrado: {path_auth}")
        return

    # ler proposições brutas
    props = pd.read_csv(path_props, sep=";")

    # filtrar só tipos substantivos
    props = props[props["siglaTipo"].isin(TIPOS_VALIDOS)].copy()
    if props.empty:
        print(f"[{ano}] Nenhuma proposição dos tipos {TIPOS_VALIDOS}.")
        return

    props["id"] = props["id"].astype(int)
    prop_ids = set(props["id"].unique())
    total_proposicoes = len(prop_ids)

    # ler autores brutos
    auth = pd.read_csv(path_auth, sep=";")

    # garantir tipos
    auth["idProposicao"] = auth["idProposicao"].astype(int)

    # restringir autores às proposições filtradas
    auth = auth[auth["idProposicao"].isin(prop_ids)].copy()

    # ===== 1) VER SE "PELO MENOS 1 AUTOR = TODAS AS PROPOSIÇÕES" É VERDADE =====

    # construímos uma chave de autor (independente de ser deputado ou não)
    # para contar autores distintos por proposição
    cols_autor = []
    for col in ["codTipoAutor", "idDeputadoAutor", "nomeAutor"]:
        if col in auth.columns:
            cols_autor.append(col)

    if not cols_autor:
        print(f"[{ano}] Não há colunas suficientes para identificar autores.")
        return

    auth["autor_key"] = auth[cols_autor].astype(str).agg("|".join, axis=1)

    counts_any = auth.groupby("idProposicao")["autor_key"].nunique()
    total_com_qualquer_autor = len(counts_any)
    total_sem_qualquer_autor = total_proposicoes - total_com_qualquer_autor

    # ===== 2) COAUTORIA SÓ ENTRE DEPUTADOS (codTipoAutor == 10000) =====

    if "codTipoAutor" in auth.columns:
        auth_dep = auth[auth["codTipoAutor"] == 10000].copy()
    else:
        auth_dep = auth.copy()  # fallback, mas no seu caso tem codTipoAutor sim

    # se não houver deputados autores, nada a fazer
    if auth_dep.empty:
        print(f"[{ano}] Nenhuma autoria com codTipoAutor == 10000.")
        return

    # garantir tipo
    auth_dep["idDeputadoAutor"] = auth_dep["idDeputadoAutor"].astype(int)

    counts_dep = auth_dep.groupby("idProposicao")["idDeputadoAutor"].nunique()

    # stats só nas proposições que têm ao menos 1 deputado autor
    total_com_dep_autor = len(counts_dep)

    ge2 = (counts_dep >= 2).sum()
    ge5 = (counts_dep >= 5).sum()
    ge10 = (counts_dep >= 10).sum()

    desc = counts_dep.describe()  # count, mean, std, min, 25%, 50%, 75%, max

    media = desc["mean"]
    desvio = desc["std"]
    minimo = desc["min"]
    q25 = desc["25%"]
    q50 = desc["50%"]
    q75 = desc["75%"]
    maximo = desc["max"]

    # ===== 3) IMPRIMIR RESULTADO COMPLETO =====

    print(f"=== Ano {ano} ===")
    print(f"Total proposições (tipos {TIPOS_VALIDOS}): {total_proposicoes}")
    print(f"Proposições com QUALQUER autor registrado: {total_com_qualquer_autor}")
    print(f"Proposições SEM nenhum autor na base: {total_sem_qualquer_autor}")
    print(f"Proposições com pelo menos 1 DEPUTADO autor (codTipoAutor=10000): {total_com_dep_autor}")
    print()

    # linha sintética no formato que você pediu
    print("ano\ttotal_proposicoes\t>=2_autores\t>=5_autores\t>=10_autores\tmedia_coautores\tdesvio_padrao\tmin\tq25\tq50\tq75\tmax")
    print(
        f"{ano}\t"
        f"{total_com_dep_autor}\t"
        f"{ge2}\t"
        f"{ge5}\t"
        f"{ge10}\t"
        f"{media:.3f}\t"
        f"{desvio:.3f}\t"
        f"{int(minimo)}\t"
        f"{q25:.1f}\t"
        f"{q50:.1f}\t"
        f"{q75:.1f}\t"
        f"{int(maximo)}"
    )


if __name__ == "__main__":
    # exemplo: rodar para um ano
    ANO = 2024
    resumo_coautoria_raw(ANO)

    # se quiser para vários anos:
    # for ano in [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]:
    #     resumo_coautoria_raw(ano)
    #     print()

