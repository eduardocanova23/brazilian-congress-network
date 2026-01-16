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
      - ./data/votes_detail_info.csv (gerado pelo VotesMiner, já com filtro de 60%)
      - ./data/deputies_info.csv (lido via getDeputies)
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
        if not os.path.exists(self.votes_detail_path):
            raise FileNotFoundError(
                f"Arquivo de votos detalhados não encontrado: {self.votes_detail_path}"
            )

        self.votes_detail = pd.read_csv(self.votes_detail_path, sep=",")
        print(f"Linhas de votos carregadas: {len(self.votes_detail)}")

        self.G = nx.Graph()

        self.col_vote_id = "idVotacao"
        self.col_deputy_id = "deputado_id"
        self.col_vote_type = "voto"

        self._fix_column_names()

    def _fix_column_names(self):
        # Compatibilidade com colunas antigas se existirem
        rename_map = {}
        if "id votação" in self.votes_detail.columns:
            rename_map["id votação"] = self.col_vote_id
        if "id deputado" in self.votes_detail.columns:
            rename_map["id deputado"] = self.col_deputy_id
        if "tipo voto" in self.votes_detail.columns:
            rename_map["tipo voto"] = self.col_vote_type

        if rename_map:
            self.votes_detail.rename(columns=rename_map, inplace=True)

        # Garante que as colunas necessárias existam
        missing = [c for c in [self.col_vote_id, self.col_deputy_id, self.col_vote_type]
                   if c not in self.votes_detail.columns]
        if missing:
            raise ValueError(f"Colunas ausentes em votes_detail_info.csv: {missing}")

        print("Colunas fixadas para votes_detail_info.csv:")
        for old, new in rename_map.items():
            print(f"  {old}  -> {new}")

    def _normalize_columns(self):
        # Normaliza strings de voto
        self.votes_detail[self.col_vote_type] = (
            self.votes_detail[self.col_vote_type].astype(str).str.strip()
        )

    def build_network(self):
        self._normalize_columns()

        # 1) Universo completo de nós:
        #    - todos os deputados em deputies_info.csv
        #    - mais todos que aparecem no votes_detail_info.csv (qualquer tipo de voto)
        df_all = self.votes_detail.copy()
        df_all[self.col_vote_type] = df_all[self.col_vote_type].astype(str).str.strip()

        df_all[self.col_deputy_id] = pd.to_numeric(
            df_all[self.col_deputy_id],
            errors="coerce"
        ).astype("Int64")
        df_all = df_all.dropna(subset=[self.col_deputy_id])
        df_all[self.col_deputy_id] = df_all[self.col_deputy_id].astype(int)

        print("Adicionando nós (incluindo grau 0)...")
        self._add_nodes_universe(df_all)

        # 2) Arestas continuam restritas a Sim/Não
        print("Filtrando apenas votos relevantes (Sim/Não)...")
        df = df_all[df_all[self.col_vote_type].isin(self.consider_votes)].copy()

        print(f"Votos após filtro: {len(df)}")

        print("Calculando pares de covotação...")
        self._add_edges(df)

        print("Rede construída.")
        print(f"Nós: {self.G.number_of_nodes()}, arestas: {self.G.number_of_edges()}")

    def _add_nodes_universe(self, df_votes_all):
        """
        Adiciona nós para um universo amplo, sem alterar a regra das arestas.

        Nós incluídos:
          - todos os deputados presentes em deputies_info.csv (self.deputies)
          - todos os deputados que aparecem em votes_detail_info.csv, mesmo com votos fora de Sim/Não

        Resultado: deputados sem votos Sim/Não (ou ausentes das votações divisivas) entram com grau 0.
        """
        universe_ids = set(self.deputies_ids)
        universe_ids.update(df_votes_all[self.col_deputy_id].unique().tolist())

        universe_ids = sorted(int(x) for x in universe_ids)

        for deputy_id in universe_ids:
            if deputy_id in self.G:
                continue

            if deputy_id in self.deputies:
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
                # Fallback: tenta usar atributos disponíveis no votes_detail_info.csv
                sub = df_votes_all[df_votes_all[self.col_deputy_id] == deputy_id]
                if len(sub) > 0:
                    row = sub.iloc[0]
                    label = row.get("deputado_nome", str(deputy_id))
                    party = row.get("deputado_siglaPartido", "")
                    uf = row.get("deputado_siglaUf", "")
                    region = getUfRegion(uf) if uf else ""
                else:
                    label = str(deputy_id)
                    party = ""
                    uf = ""
                    region = ""

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

    def _add_nodes(self, df_votes):
        """
        Mantido por compatibilidade: cria nós só para deputados presentes em df_votes.
        (Não é mais usado como universo principal, pois agora usamos _add_nodes_universe.)
        """
        deputies_in_votes = sorted(df_votes[self.col_deputy_id].unique())

        for deputy_id in deputies_in_votes:
            if deputy_id in self.deputies:
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
                sub = df_votes[df_votes[self.col_deputy_id] == deputy_id]
                if len(sub) > 0:
                    row = sub.iloc[0]
                    label = row.get("deputado_nome", str(deputy_id))
                    party = row.get("deputado_siglaPartido", "")
                    uf = row.get("deputado_siglaUf", "")
                    region = getUfRegion(uf) if uf else ""
                else:
                    label = str(deputy_id)
                    party = ""
                    uf = ""
                    region = ""

                sex = ""
                education = ""
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
        # Agrupa por votação, e cria pares entre deputados que votaram igual
        grouped = df_votes.groupby(self.col_vote_id)

        for _, group in grouped:
            deputies = group[self.col_deputy_id].tolist()
            votes = group[self.col_vote_type].tolist()

            n = len(deputies)
            for i in range(n):
                for j in range(i + 1, n):
                    if votes[i] != votes[j]:
                        continue

                    u = deputies[i]
                    v = deputies[j]

                    if self.G.has_edge(u, v):
                        self.G[u][v]["weight"] += 1
                    else:
                        self.G.add_edge(u, v, weight=1)

    def sanitize(self):
        # Mantido caso você use em outras partes do fluxo
        # Aqui não removemos nós isolados (você quer grau 0)
        pass

    def save_network(self,
                     output_dir: str = "../data/networks",
                     network_name: str = "covoting-network",
                     use_version: bool = True):

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
