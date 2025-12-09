import networkx as nx
import pandas as pd
import os
from datetime import datetime

from .data_readers import getDeputies
from .utils import calculateAge, getAgeRange, getUfRegion


class CovotingNetworkBuilder:
    """
    Constrói rede de covotação:
        - nós: deputados
        - arestas: peso = número de votações divisivas em que votaram igual

    Depende de:
        ./data/deputies_info.csv   (lido via getDeputies())
        ./data/votes_detail_info.csv
    """

    def __init__(self,
                 votes_detail_path: str = "./data/votes_detail_info.csv",
                 min_common_votes: int = 1,
                 consider_votes=("Sim", "Não")):

        self.votes_detail_path = votes_detail_path
        self.min_common_votes = min_common_votes
        self.consider_votes = set(consider_votes)

        # Carrega deputados (funciona pois build_covoting_network faz chdir("./source"))
        print("Carregando informações de deputados...")
        self.deputies = getDeputies()
        self.deputies_ids = sorted(int(k) for k in self.deputies.keys())
        print(f"Deputados em deputies_info: {len(self.deputies_ids)}")

        # Carrega votos detalhados
        print(f"Carregando votos detalhados de {self.votes_detail_path}...")
        if not os.path.exists(self.votes_detail_path):
            raise FileNotFoundError(
                f"Arquivo de votos detalhados não encontrado: {self.votes_detail_path}"
            )

        self.votes_detail = pd.read_csv(self.votes_detail_path, sep=",")
        print(f"Linhas de votos carregadas: {len(self.votes_detail)}")

        self.G = nx.Graph()

    def _normalize_columns(self):
        """
        Ajusta nomes padrão de colunas internas para o layout real de
        votes_detail_info.csv gerado pelo VotesMiner.

        Colunas obrigatórias detectadas:
            - idVotacao
            - deputado_id
            - voto
        """
        required = ["idVotacao", "deputado_id", "voto"]

        for col in required:
            if col not in self.votes_detail.columns:
                raise ValueError(
                    f"Coluna obrigatória '{col}' não encontrada.\n"
                    f"Colunas disponíveis: {list(self.votes_detail.columns)}"
                )

        self.col_vote_id = "idVotacao"
        self.col_deputy_id = "deputado_id"
        self.col_vote_type = "voto"

        print("Colunas fixadas para votes_detail_info.csv:")
        print(f"  id votação  -> {self.col_vote_id}")
        print(f"  id deputado -> {self.col_deputy_id}")
        print(f"  tipo voto   -> {self.col_vote_type}")

    def build_network(self):
        self._normalize_columns()

        print("Filtrando apenas votos relevantes (Sim/Não)...")
        df = self.votes_detail.copy()
        df[self.col_vote_type] = df[self.col_vote_type].astype(str).str.strip()

        df = df[df[self.col_vote_type].isin(self.consider_votes)]

        # Convert para int e filtra
        df[self.col_deputy_id] = pd.to_numeric(df[self.col_deputy_id],
                                               errors="coerce").astype("Int64")
        df = df.dropna(subset=[self.col_deputy_id])
        df[self.col_deputy_id] = df[self.col_deputy_id].astype(int)


        print(f"Votos após filtro: {len(df)}")

        print("Adicionando nós...")
        self._add_nodes(df)

        print("Calculando pares de covotação...")
        self._add_edges(df)

        print("Rede construída.")
        print(f"Nós: {self.G.number_of_nodes()}, arestas: {self.G.number_of_edges()}")

    def _add_nodes(self, df_votes):
        """
        Cria nós na rede para todos os deputados que aparecem em df_votes.

        Regra:
          - Se o deputado existir em self.deputies (deputies_info.csv),
            usa os atributos completos (como na NetworkBuilder).
          - Se NÃO existir em self.deputies, cria mesmo assim,
            usando os atributos disponíveis em votes_detail_info.csv.
        """
        deputies_in_votes = sorted(df_votes[self.col_deputy_id].unique())

        for deputy_id in deputies_in_votes:
            if deputy_id in self.deputies:
                # Caminho "completo": usamos deputies_info.csv
                dep = self.deputies[deputy_id]

                cpf = dep.get("cpf")
                party = dep.get("party")
                uf = dep.get("uf")
                region = dep.get("region") or getUfRegion(uf)
                label = dep.get("name")
                sex = dep.get("sex")
                education = dep.get("education")
                birthdate = dep.get("birthdate")

                age = calculateAge(birthdate) if birthdate else None
                age_range = getAgeRange(age) if age is not None else None

            else:
                # Caminho "fallback": o deputado não está em deputies_info.csv.
                # Usamos o que estiver disponível em votes_detail_info.csv.
                sub = df_votes[df_votes[self.col_deputy_id] == deputy_id]

                # Pega uma linha qualquer desse deputado
                row = sub.iloc[0]

                label = row.get("deputado_nome", str(deputy_id))
                party = row.get("deputado_siglaPartido", "")
                uf = row.get("deputado_siglaUf", "")
                region = getUfRegion(uf) if uf else ""
                sex = ""
                education = ""
                cpf = ""
                age = None
                age_range = None

            self.G.add_node(
                deputy_id,
                label=label,
                party=party,
                uf=uf,
                region=region,
                sex=sex,
                education=education,
                age=age,
                age_range=age_range,
            )


    def _add_edges(self, df_votes):
        from itertools import combinations

        edge_weights = {}

        # Agrupa por votação
        for vote_id, df_vot in df_votes.groupby(self.col_vote_id):
            # Agrupa por tipo de voto
            for vote_type, df_group in df_vot.groupby(self.col_vote_type):
                deputies = sorted(df_group[self.col_deputy_id].unique())
                if len(deputies) <= 1:
                    continue

                for a, b in combinations(deputies, 2):
                    if a == b:
                        continue
                    edge = (min(a, b), max(a, b))
                    edge_weights[edge] = edge_weights.get(edge, 0) + 1

        # Adiciona arestas
        for (u, v), w in edge_weights.items():
            if w < self.min_common_votes:
                continue
            self.G.add_edge(u, v, weight=w)

    def save_network(self,
                     network_name: str = "covoting-network",
                     use_version: bool = True,
                     output_dir: str = "./data/networks"):

        print("Sanitizando atributos e salvando rede em GEXF...")

        for _, data in self.G.nodes(data=True):
            for k, v in list(data.items()):
                if v is None:
                    del data[k]

        for _, _, data in self.G.edges(data=True):
            for k, v in list(data.items()):
                if v is None:
                    del data[k]

        os.makedirs(output_dir, exist_ok=True)

        base_name = network_name
        if use_version:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{base_name}-{timestamp}.gexf"
        else:
            filename = f"{base_name}.gexf"

        path = os.path.join(output_dir, filename)
        nx.write_gexf(self.G, path)
        print(f"Rede salva em: {path}")

