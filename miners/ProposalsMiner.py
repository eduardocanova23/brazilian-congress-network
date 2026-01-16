from .AbstractMiner import Miner
import pandas as pd
import requests
import os


class ProposalsMiner(Miner):
    proposal_types = ["PL", "PEC", "PLN", "PLP", "PLV", "PLC"]
    infos = []
    download_link = "https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-{year}.csv"
    output_path = "./data/proposals/"

    def mineData(self):
        # garantir que a pasta exista
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        for year in self.years:
            response = requests.get(self.download_link.format(year=year))
            response.raise_for_status()
            file_name = f"proposicoes-{year}.csv"
            path = self.output_path
            with open(os.path.join(path, file_name), "wb") as f:
                f.write(response.content)

    def createDataframe(self):
        self.infos = []

        for year in self.years:
            proposal = pd.read_csv(f"./data/proposals/proposicoes-{year}.csv", sep=";", low_memory=False)

            # manter colunas necessárias para o filtro por votação e para auditoria
            keep_cols = [
                "id",
                "siglaTipo",
                "numero",
                "ano",
                "ementa",
                "keywords",
                "ultimoStatus_idSituacao",
                "ultimoStatus_descricaoSituacao",
            ]
            existing = [c for c in keep_cols if c in proposal.columns]
            proposal = proposal[existing].copy()

            # filtro por tipo
            proposal = proposal[proposal["siglaTipo"].isin(self.proposal_types)].copy()

            # normalizações
            proposal["id"] = pd.to_numeric(proposal["id"], errors="coerce").astype("Int64")
            proposal = proposal.dropna(subset=["id"]).copy()
            proposal["id"] = proposal["id"].astype(int)

            if "ultimoStatus_idSituacao" in proposal.columns:
                proposal["ultimoStatus_idSituacao"] = (
                    pd.to_numeric(proposal["ultimoStatus_idSituacao"], errors="coerce")
                    .fillna(0)
                    .astype(int)
                )

            if "ultimoStatus_descricaoSituacao" in proposal.columns:
                proposal["ultimoStatus_descricaoSituacao"] = proposal["ultimoStatus_descricaoSituacao"].fillna("")
            else:
                proposal["ultimoStatus_descricaoSituacao"] = ""

            self.infos.append(proposal)

    def save2CSV(self):
        data = pd.concat(self.infos, ignore_index=True)

        # ler mapa de proposições votadas, gerado pelo VotesMiner
        voted_path = "./data/proposals_voted_map.csv"
        if not os.path.exists(voted_path):
            raise FileNotFoundError(
                "Arquivo ./data/proposals_voted_map.csv não encontrado. "
                "Execute o VotesMiner antes do ProposalsMiner."
            )

        voted_df = pd.read_csv(voted_path)
        if "idProposicao" not in voted_df.columns:
            raise ValueError(
                "proposals_voted_map.csv não contém coluna idProposicao. "
                f"Colunas: {list(voted_df.columns)}"
            )

        voted_ids = set(pd.to_numeric(voted_df["idProposicao"], errors="coerce").dropna().astype(int).tolist())

        # status que contam como aprovadas finais
        approved_status = {"Transformado em Norma Jurídica"}

        # filtro principal
        status = data["ultimoStatus_descricaoSituacao"].fillna("")
        is_approved = status.isin(approved_status)
        is_archived = status.eq("Arquivada")
        has_vote = data["id"].isin(voted_ids)

        keep = is_approved | (is_archived & has_vote)
        data = data[keep].copy()

        # coluna explícita de resultado (para não depender do texto depois)
        data["resultado_votacao"] = ""
        data.loc[is_approved & keep, "resultado_votacao"] = "aprovada"
        data.loc[(is_archived & has_vote) & keep, "resultado_votacao"] = "rejeitada"

        data.to_csv("./data/proposals_info.csv", header=True, index=False)

    def setProposalTypes(self, proposal_types):
        self.proposal_types = proposal_types

    def getProposalTypes(self):
        return self.proposal_types
