import sys
import ast
import pandas as pd
import os

BASE_AUTHORS = "data/authors"
BASE_PROPOSALS = "data/proposals"

# mesmos tipos de proposição que o ProposalsMiner usa
PROPOSAL_TYPES = ["PL", "PEC", "PLN", "PLP", "PLV", "PLC"]


def prepare_info(years):
    years = list(sorted(set(int(y) for y in years)))
    print(f"Montando authors_info.csv e proposals_info.csv para anos: {years}")

    authors_infos = []
    proposals_infos = []

    for year in years:
        path_auth = os.path.join(BASE_AUTHORS, f"proposicoesAutores-{year}.csv")
        path_prop = os.path.join(BASE_PROPOSALS, f"proposicoes-{year}.csv")

        if not os.path.exists(path_auth):
            print(f"Aviso: {path_auth} não encontrado, pulando ano {year}")
            continue
        if not os.path.exists(path_prop):
            print(f"Aviso: {path_prop} não encontrado, pulando ano {year}")
            continue

        print(f"Lendo autores {year}...")
        auth = pd.read_csv(path_auth, sep=";")
        # mesma transformação do AuthorsMiner
        auth = auth[["idProposicao", "idDeputadoAutor", "codTipoAutor"]].dropna()
        auth["idDeputadoAutor"] = auth["idDeputadoAutor"].astype(int)
        auth.rename(columns={"idDeputadoAutor": "idAutor"}, inplace=True)
        # opcional: guardar o ano
        auth["ano"] = year
        authors_infos.append(auth)

        print(f"Lendo proposições {year}...")
        prop = pd.read_csv(path_prop, sep=";")
        # filtra tipos relevantes
        prop = prop[prop["siglaTipo"].isin(PROPOSAL_TYPES)].copy()
        # garante tipo inteiro em ultimoStatus_idSituacao
        prop["ultimoStatus_idSituacao"] = prop["ultimoStatus_idSituacao"].fillna(0.0).astype(int)
        prop["ano"] = year
        proposals_infos.append(prop)

    if not authors_infos or not proposals_infos:
        print("Nenhum dado válido encontrado para os anos informados.")
        return

    authors_all = pd.concat(authors_infos, ignore_index=True)
    proposals_all = pd.concat(proposals_infos, ignore_index=True)

    # salvar exatamente nos caminhos esperados por data_readers.getAuthors/getProposals
    authors_all.to_csv("data/authors_info.csv", index=False)
    proposals_all.to_csv("data/proposals_info.csv", index=False)

    print(f"Salvo authors_info.csv com {len(authors_all)} linhas.")
    print(f"Salvo proposals_info.csv com {len(proposals_all)} linhas.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python prepare_info_for_years.py \"[2019,2020,2021,2022]\"")
        sys.exit(1)

    years_arg = ast.literal_eval(sys.argv[1])
    prepare_info(years_arg)
