from .AbstractMiner import Miner
import pandas as pd
import requests
import os


class VotesMiner(Miner):
    """
    Baixa e prepara dados de votações e votos por parlamentar.

    Também gera um mapa simples de proposições que aparecem no arquivo de votações
    (isto é, que tiveram alguma votação registrada no período):
      - ./data/proposals_voted_map.csv com coluna idProposicao
    """

    summary_link = "https://dadosabertos.camara.leg.br/arquivos/votacoes/csv/votacoes-{year}.csv"
    detail_link = "https://dadosabertos.camara.leg.br/arquivos/votacoesVotos/csv/votacoesVotos-{year}.csv"

    output_raw_path = "./data/votes/raw/"

    # Parâmetros do filtro de "votação divisiva"
    division_threshold = 0.60     # máximo da fração de Sim ou Não
    min_total_votes = 20          # mínimo de votos válidos (Sim + Não)

    def __init__(self, years=None, legislatures=None):
        super().__init__(years, legislatures)
        self.votes_summary = []
        self.votes_detail = []
        self.proposals_voted_rows = []

    def mineData(self):
        """
        Baixa os arquivos brutos de votações para cada ano solicitado:
          - votacoes-{ano}.csv
          - votacoesVotos-{ano}.csv
        """
        os.makedirs(self.output_raw_path, exist_ok=True)

        for year in self.years:
            # 1) Arquivo com placar agregado
            summary_url = self.summary_link.format(year=year)
            summary_filename = f"votacoes-{year}.csv"
            summary_path = os.path.join(self.output_raw_path, summary_filename)

            print(f"Baixando {summary_url} -> {summary_path}")
            r = requests.get(summary_url)
            r.raise_for_status()
            with open(summary_path, "wb") as f:
                f.write(r.content)

            # 2) Arquivo com votos por parlamentar
            detail_url = self.detail_link.format(year=year)
            detail_filename = f"votacoesVotos-{year}.csv"
            detail_path = os.path.join(self.output_raw_path, detail_filename)

            print(f"Baixando {detail_url} -> {detail_path}")
            r = requests.get(detail_url)
            r.raise_for_status()
            with open(detail_path, "wb") as f:
                f.write(r.content)

    def createDataframe(self):
        """
        Lê os CSVs brutos e gera dois dataframes consolidados:
          - self.votes_summary: apenas votações "divisivas"
          - self.votes_detail: votos dos deputados nessas votações filtradas

        Em paralelo, constrói um mapa de idProposicao que aparecem no arquivo
        votacoes-{ano}.csv (indício de proposição votada no período).
        """
        for year in self.years:
            summary_path = os.path.join(self.output_raw_path, f"votacoes-{year}.csv")
            detail_path = os.path.join(self.output_raw_path, f"votacoesVotos-{year}.csv")

            if not os.path.exists(summary_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {summary_path}")
            if not os.path.exists(detail_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {detail_path}")

            df_sum = pd.read_csv(summary_path, sep=";", low_memory=False)
            df_det = pd.read_csv(detail_path, sep=";", low_memory=False)

            # 1) Construir mapa de proposições com votação (antes de qualquer filtro)
            prop_col = "ultimaApresentacaoProposicao_idProposicao"
            if prop_col in df_sum.columns:
                tmp = df_sum[[prop_col]].dropna().copy()
                tmp[prop_col] = tmp[prop_col].astype(int)
                tmp["ano_votacao"] = year
                self.proposals_voted_rows.append(tmp)
            else:
                print(
                    f"Aviso: coluna {prop_col} não encontrada em {summary_path}. "
                    "Mapa proposals_voted_map pode ficar incompleto."
                )

            # 2) Filtro de votações divisivas
            required_cols = ["id", "votosSim", "votosNao"]
            for c in required_cols:
                if c not in df_sum.columns:
                    raise ValueError(
                        f"Não encontrei coluna {c} em {summary_path}. "
                        f"Colunas disponíveis: {list(df_sum.columns)}"
                    )

            df_sum["votosSim"] = pd.to_numeric(df_sum["votosSim"], errors="coerce").fillna(0).astype(int)
            df_sum["votosNao"] = pd.to_numeric(df_sum["votosNao"], errors="coerce").fillna(0).astype(int)

            df_sum["total_validos"] = df_sum["votosSim"] + df_sum["votosNao"]
            df_sum = df_sum[df_sum["total_validos"] >= self.min_total_votes].copy()

            if len(df_sum) == 0:
                continue

            df_sum["frac_sim"] = df_sum["votosSim"] / df_sum["total_validos"]
            df_sum["frac_nao"] = df_sum["votosNao"] / df_sum["total_validos"]

            df_sum_div = df_sum[
                (df_sum["frac_sim"] <= self.division_threshold) &
                (df_sum["frac_nao"] <= self.division_threshold)
            ].copy()

            if len(df_sum_div) == 0:
                continue

            # Achar nome da coluna de id de votação no detalhe
            id_col_detail = None
            for cand in ["idVotacao", "idVotação", "idVotacao", "id"]:
                if cand in df_det.columns:
                    id_col_detail = cand
                    break
            if id_col_detail is None:
                raise ValueError(
                    f"Não encontrei coluna de id de votação em {detail_path}. "
                    f"Colunas: {list(df_det.columns)}"
                )

            divisive_ids = df_sum_div["id"].unique().tolist()
            df_det_div = df_det[df_det[id_col_detail].isin(divisive_ids)].copy()

            # Marca o ano explicitamente
            df_sum_div["ano_votacao"] = year
            df_det_div["ano_votacao"] = year

            self.votes_summary.append(df_sum_div)
            self.votes_detail.append(df_det_div)

    def save2CSV(self):
        """
        Salva:
          - ./data/votes_info.csv            (resumo das votações divisivas)
          - ./data/votes_detail_info.csv     (votos dos deputados nas votações filtradas)
          - ./data/proposals_voted_map.csv   (ids de proposições que tiveram votação registrada no período)
        """
        os.makedirs("./data", exist_ok=True)

        # 1) Salvar votes_info e votes_detail_info (apenas divisivas, como antes)
        if self.votes_summary and self.votes_detail:
            summary = pd.concat(self.votes_summary, ignore_index=True)
            detail = pd.concat(self.votes_detail, ignore_index=True)

            summary.to_csv("./data/votes_info.csv", index=False)
            detail.to_csv("./data/votes_detail_info.csv", index=False)

            print(f"Resumo de votações salvo em ./data/votes_info.csv com {len(summary)} linhas.")
            print(f"Votos por deputado salvos em ./data/votes_detail_info.csv com {len(detail)} linhas.")
        else:
            print("VotesMiner: nenhuma votação divisiva para salvar em votes_info/votes_detail_info.")

        # 2) Salvar proposals_voted_map (todas as proposições que aparecem nas votações)
        if self.proposals_voted_rows:
            voted = pd.concat(self.proposals_voted_rows, ignore_index=True)
            voted = voted.rename(columns={"ultimaApresentacaoProposicao_idProposicao": "idProposicao"})
            voted = voted[["idProposicao"]].drop_duplicates().sort_values("idProposicao")

            voted.to_csv("./data/proposals_voted_map.csv", index=False)
            print(f"Mapa de proposições votadas salvo em ./data/proposals_voted_map.csv com {len(voted)} ids.")
        else:
            print("VotesMiner: nenhum idProposicao coletado para proposals_voted_map.csv.")
