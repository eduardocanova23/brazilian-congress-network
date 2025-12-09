from .AbstractMiner import Miner
import pandas as pd
import requests
import os


class VotesMiner(Miner):
    """
    Baixa e prepara dados de votações e votos por parlamentar.

    Lógica principal:
      - Para cada ano em self.years:
        1) Baixa votacoes-{ano}.csv (placar agregado)
        2) Baixa votacoesVotos-{ano}.csv (votos por deputado)
      - Usa o arquivo de votações para:
        * calcular quão "divisiva" foi cada votação
        * manter apenas votações com:
            - total de votos válidos (Sim + Não) >= min_total_votes
            - lado vencedor com participação <= division_threshold (ex: 0.7)
      - Filtra o arquivo de votos detalhados para manter somente essas votações.
      - Concatena tudo em:
          ./data/votes_info.csv          -> resumo das votações divisivas
          ./data/votes_detail_info.csv   -> votos dos deputados nessas votações
    """

    # Arquivos agregados de votações por ano
    summary_link = "https://dadosabertos.camara.leg.br/arquivos/votacoes/csv/votacoes-{year}.csv"

    # Votos nominais por parlamentar, por ano
    detail_link = "https://dadosabertos.camara.leg.br/arquivos/votacoesVotos/csv/votacoesVotos-{year}.csv"

    # Pasta para armazenar os CSVs brutos baixados por ano
    output_raw_path = "./data/votes/raw/"

    # Parâmetros do filtro de "votação divisiva"
    division_threshold = 0.60     # máximo da fração de Sim ou Não
    min_total_votes = 20           # mínimo de votos válidos (Sim + Não)

    def __init__(self, years=None, legislatures=None):
        super().__init__(years, legislatures)
        self.votes_summary = []
        self.votes_detail = []

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
          - self.votes_detail: votos dos deputados nessas votações
        O filtro de divisividade é feito aqui, antes de mexer com a rede.
        """
        for year in self.years:
            summary_path = os.path.join(self.output_raw_path, f"votacoes-{year}.csv")
            detail_path = os.path.join(self.output_raw_path, f"votacoesVotos-{year}.csv")

            if not os.path.exists(summary_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {summary_path}")
            if not os.path.exists(detail_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {detail_path}")

            # Normalmente o separador da Câmara é ponto e vírgula
            df_sum = pd.read_csv(summary_path, sep=";")

            # As colunas abaixo vêm da documentação oficial de votações:
            #  - id
            #  - votosSim
            #  - votosNao
            #  - votosOutros
            # Se algum nome estiver diferente na prática, isso vai explodir aqui
            # e a gente ajusta depois olhando as colunas reais.
            expected_cols = ["id", "votosSim", "votosNao"]
            for col in expected_cols:
                if col not in df_sum.columns:
                    raise ValueError(
                        f"Coluna esperada '{col}' não encontrada em {summary_path}.\n"
                        f"Colunas disponíveis: {list(df_sum.columns)}"
                    )

            df_sum["votosSim"] = df_sum["votosSim"].fillna(0).astype(int)
            df_sum["votosNao"] = df_sum["votosNao"].fillna(0).astype(int)

            if "votosOutros" in df_sum.columns:
                df_sum["votosOutros"] = df_sum["votosOutros"].fillna(0).astype(int)
            else:
                # Garante a coluna mesmo que não exista no arquivo
                df_sum["votosOutros"] = 0

            # Total de votos válidos: só Sim + Não (padrão para ver polarização)
            df_sum["total_validos"] = df_sum["votosSim"] + df_sum["votosNao"]
            df_sum = df_sum[df_sum["total_validos"] > 0]

            # Fração do lado vencedor
            max_share = df_sum[["votosSim", "votosNao"]].max(axis=1) / df_sum["total_validos"]

            # Filtro de "votação divisiva"
            mask_divisive = (
                (df_sum["total_validos"] >= self.min_total_votes)
                & (max_share <= self.division_threshold)
            )

            df_sum_div = df_sum[mask_divisive].copy()

            print(
                f"Ano {year}: {len(df_sum)} votações no total, "
                f"{len(df_sum_div)} após filtro de divisividade."
            )

            # Agora filtra o arquivo com votos nominais
            df_det = pd.read_csv(detail_path, sep=";")

            # A coluna de id da votação no arquivo de votos costuma ser algo como
            # 'idVotacao'. Para não chutar muito, tentamos alguns candidatos.
            id_col_detail = None
            for candidate in ["idVotacao", "idvotacao", "id_votacao"]:
                if candidate in df_det.columns:
                    id_col_detail = candidate
                    break

            if id_col_detail is None:
                raise ValueError(
                    f"Não encontrei coluna de id de votação em {detail_path}.\n"
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
          - ./data/votes_info.csv          (resumo das votações divisivas)
          - ./data/votes_detail_info.csv   (votos dos deputados nas votações filtradas)
        """
        if not self.votes_summary or not self.votes_detail:
            print("VotesMiner: nada para salvar, execute createDataframe() primeiro.")
            return

        os.makedirs("./data", exist_ok=True)

        summary = pd.concat(self.votes_summary, ignore_index=True)
        detail = pd.concat(self.votes_detail, ignore_index=True)

        summary.to_csv("./data/votes_info.csv", index=False)
        detail.to_csv("./data/votes_detail_info.csv", index=False)

        print(f"Resumo de votações salvo em ./data/votes_info.csv "
              f"com {len(summary)} linhas.")
        print(f"Votos por deputado salvos em ./data/votes_detail_info.csv "
              f"com {len(detail)} linhas.")
