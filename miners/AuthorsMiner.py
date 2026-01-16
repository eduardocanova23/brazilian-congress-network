from .AbstractMiner import Miner
import pandas as pd
import requests
import os


class AuthorsMiner(Miner):
    download_link = "https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-{year}.csv"
    output_path = "./data/authors/"
    infos = []

    def mineData(self):
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        for year in self.years:
            response = requests.get(self.download_link.format(year=year))
            response.raise_for_status()
            file_name = f"proposicoesAutores-{year}.csv"
            full_path = os.path.join(self.output_path, file_name)
            with open(full_path, "wb") as f:
                f.write(response.content)

    def createDataframe(self):
        self.infos = []

        for year in self.years:
            proposal_authors = pd.read_csv(
                f"./data/authors/proposicoesAutores-{year}.csv",
                sep=";"
            )
            proposal_authors = proposal_authors[["idProposicao", "idDeputadoAutor", "codTipoAutor"]]
            proposal_authors = proposal_authors.dropna()
            proposal_authors["idDeputadoAutor"] = proposal_authors["idDeputadoAutor"].astype(int)
            proposal_authors.rename(columns={"idDeputadoAutor": "idAutor"}, inplace=True)
            self.infos.append(proposal_authors)

    def save2CSV(self):
        data = pd.concat(self.infos, ignore_index=True)

        # Filtra para manter só proposições que estão em proposals_info.csv (tipos PL/PEC/PLN/PLP/PLV/PLC)
        proposals_path = "./data/proposals_info.csv"
        if os.path.exists(proposals_path):
            p = pd.read_csv(proposals_path)
            allowed_ids = set(p["id"].astype(int).tolist())
            data = data[data["idProposicao"].astype(int).isin(allowed_ids)]
        else:
            print("Aviso: ./data/proposals_info.csv não encontrado. Salvando authors_info.csv sem filtro por tipo.")

        data.to_csv("./data/authors_info.csv", header=True, index=False)
