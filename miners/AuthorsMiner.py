from .AbstractMiner import Miner
import pandas as pd
import ast
import sys
import numpy as np
import requests
import os


class AuthorsMiner(Miner):
    download_link = "https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-{year}.csv"
    output_path = "./data/authors/"
    data = None
    infos = []


    def mineData(self):
        # garante que a pasta ./data/authors/ exista (relativo a miners/)
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        for year in self.years:
            response = requests.get(self.download_link.format(year=year))
            file_name = "proposicoesAutores-{}.csv".format(year)
            full_path = os.path.join(self.output_path, file_name)
            with open(full_path, 'wb') as f:
                f.write(response.content)


    def createDataframe(self):
        for year in self.years:
            proposal_authors = pd.read_csv("./data/authors/proposicoesAutores-{}.csv".format(year), sep=';')
            proposal_authors = proposal_authors[['idProposicao', 'idDeputadoAutor', 'codTipoAutor']]
            proposal_authors = proposal_authors.dropna()
            proposal_authors['idDeputadoAutor'] = proposal_authors['idDeputadoAutor'].astype(int)
            proposal_authors.rename(columns={'idDeputadoAutor': 'idAutor'}, inplace=True)
            self.infos.append(proposal_authors)

    def save2CSV(self):
        data = pd.concat(self.infos)
        data.to_csv('./data/authors_info.csv', header=True, index=False)