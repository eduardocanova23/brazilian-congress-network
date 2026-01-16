import numpy as np
import networkx as nx
import pydot
import random
import ast
from .model_parameters import *
from .data_readers import *
import random
import ast
import os
from datetime import date
from .utils import calculateAge
from .utils import getAgeRange
from .utils import generateEdges
from .utils import getUfRegion

class NetworkBuilder():
    deputies = None
    deputies_ids = None
    proposals = None
    legislative_roles = None
    parties = None
    proposal_authors = None
    tse_info = None

    deputies_proposals = None
    deputies_proposals_pertinence = None
    roles_relevance = None

    G = None
    collab_weights = {}
    collab_pertinence = {}

    def __init__(self):
        print("Carregando informações...")

    # Deputados "globais" (todas as legislaturas mineradas)
        self.deputies = getDeputies()
        all_deputy_ids = set(int(k) for k in self.deputies.keys())

    # Proposições, cargos, partidos e autores dos ANOS selecionados
        self.proposals = getProposals()
        self.legislative_roles = getRoles()
        self.parties = getParties()
        self.proposal_authors = getAuthors()
        self.tse_info = getInfoTSE()

    # Deputados que aparecem como autores nas proposições selecionadas
        author_ids = set()
        for authors in self.proposal_authors.values():
            for a in authors:
                try:
                    author_ids.add(int(a))
                except (ValueError, TypeError):
                    continue

    # Interseção: só entram na rede deputados que:
    # - existem em deputies_info.csv
    # - aparecem em authors_info.csv (anos que você escolheu)
        self.deputies_ids = sorted(all_deputy_ids | author_ids)

        print(f"Deputados em deputies_info: {len(all_deputy_ids)}")
        print(f"Deputados que aparecem como autores (anos selecionados): {len(author_ids)}")
        print(f"Deputados efetivamente usados na rede (união Lucas): {len(self.deputies_ids)}")

        # A partir daqui, tudo usa só esses ids ativos
        self.setDeputiesRegion()
        self.setDeputiesIndividualProposals()
        self.setDeputiesRoleInfluence()


    def buildNetwork(self, weighted = True):
        self.weighted_network = weighted
        self.G = nx.Graph()
        self.addNodes()
        self.addEdges()

    def saveNetWork(self, network_name="coauthorship-network", use_version=True):
        import os
        from datetime import datetime
        import pandas as pd

        print("Salvando a rede...")

    # Sanear atributos: GEXF não aceita None
        for node, data in self.G.nodes(data=True):
            for k, v in list(data.items()):
                if v is None:
                    data[k] = ''  # ou 'NA', se preferir

        for u, v, data in self.G.edges(data=True):
            for k, vv in list(data.items()):
                if vv is None:
                    data[k] = ''

    # Inferir anos a partir de ../data/proposals_info.csv
        years_str = "unknown_years"
        try:
            props = pd.read_csv("../data/proposals_info.csv")
            if "ano" in props.columns:
                anos = sorted(props["ano"].dropna().unique())
                if len(anos) > 0:
                    years_str = "_".join(str(int(a)) for a in anos)
        except Exception as e:
            print("Aviso: não foi possível inferir anos a partir de proposals_info.csv:", e)

    # Montar nome base
        base_name = f"{network_name}-{years_str}"

    # Adicionar timestamp se use_version=True
        if use_version:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{base_name}-{timestamp}.gexf"
        else:
            filename = f"{base_name}.gexf"

    # Garantir que a pasta ../data/networks exista
        os.makedirs("../data/networks", exist_ok=True)

    # Caminho final
        path = os.path.join("../data/networks", filename)

    # Salvar GEXF
        nx.write_gexf(self.G, path)
        print("Rede salva em: {}".format(path))


    def addNodes(self):
        print("Gerando vértices...")
        out_of_date_deputies = []

        for deputy_id in self.deputies_ids:
            deputy_id = int(deputy_id)

            if deputy_id in self.deputies:
                cpf = self.deputies[deputy_id].get('cpf')
                party = self.deputies[deputy_id].get('party', '')
                uf = self.deputies[deputy_id].get('uf', '')
                region = self.deputies[deputy_id].get('region', '')
                label = self.deputies[deputy_id].get('name', '')
                sex = self.deputies[deputy_id].get('sex', '')
                education = self.deputies[deputy_id].get('education', '')
                birthdate = self.deputies[deputy_id].get('birthdate')

                tse_record = self.tse_info.get(cpf, {}) if isinstance(self.tse_info, dict) else {}
                education_tse = tse_record.get('DS_GRAU_INSTRUCAO', '')
                ethnicity = tse_record.get('DS_COR_RACA', '')

                age = calculateAge(birthdate) if birthdate else ''
                age_range = getAgeRange(age) if age != '' else ''

                individual_proposals = (
                    self.deputies_proposals.get(deputy_id, 0) * node_parameters['proposal']
                )

                role_relevance = (
                    self.roles_relevance.get(deputy_id, 0) * node_parameters['role']
                )

                deputy_weight = individual_proposals + role_relevance

                self.G.add_node(
                    deputy_id,
                    label=label,
                    style='filled',
                    weight=deputy_weight,
                    party=party,
                    uf=uf,
                    age_range=age_range,
                    sex=sex,
                    education=education,
                    age=age,
                    education_tse=education_tse,
                    ethnicity=ethnicity,
                    region=region
                )

            else:
                # Autor que apareceu nas proposições, mas não está em deputies_info
                self.G.add_node(
                    deputy_id,
                    label=str(deputy_id),
                    style='filled',
                    weight=0,
                    party='',
                    uf='',
                    age_range='',
                    sex='',
                    education='',
                    age='',
                    education_tse='',
                    ethnicity='',
                    region=''
                )
                out_of_date_deputies.append(deputy_id)

        print("Deputados fora de deputies_info adicionados como nós:", len(out_of_date_deputies))


    def addEdges(self):
        print("Adicionando arestas...")
        self.setCollaborations()
        self.setCollaborationsSuccess()
        for edge in self.collab_weights.keys():
            if(self.weighted_network):
                weight = self.collab_weights[edge]
            else:
                weight = 1
            self.G.add_edge(
                edge[0], edge[1], weight= weight, success_pertinence=self.collab_pertinence[edge]
            )
    
    def removePastDeputies(self):
        nodes_to_remove = []

        for deputy in list(self.G.nodes()):
            if (deputy not in self.deputies_ids):
                nodes_to_remove.append(deputy)
  
        self.G.remove_nodes_from(nodes_to_remove)
            
    def setCollaborations(self):
        """
        Define pesos das arestas de acordo com número de coautoria entre dois deputados.

        Ajustes principais:
        - usa apenas autores cujo id está em self.deputies_ids
        - remove duplicados de autores por proposição
        - ignora proposições com menos de 2 deputados válidos
        """
        deputies_set = set(self.deputies_ids)

        print("Calculando coautorias (setCollaborations)...")
        for proposal_id in list(self.proposals.keys()):
            if proposal_id not in self.proposal_authors:
                continue

            # lista de autores bruta vinda de getAuthors()
            proposal_authors = self.proposal_authors[proposal_id]

            # filtrar só ids que existem em self.deputies_ids
            filtered_authors = [a for a in proposal_authors if a in deputies_set]

            # remover duplicados (caso o mesmo deputado apareça mais de uma vez)
            filtered_authors = sorted(set(filtered_authors))

            # se sobrou menos de 2, não gera aresta
            if len(filtered_authors) <= 1:
                continue

            # tipo e peso da proposição
            proposal_type = self.proposals[proposal_id]["siglaTipo"]
            if proposal_type not in proposal_weight:
                # se aparecer um tipo estranho, simplesmente ignora
                continue

            n_proposal_weight = proposal_weight[proposal_type]

            # log opcional pra você identificar proposições "monstro"
            if len(filtered_authors) >= 150:
                print(
                    f"[ALERTA] Proposição {proposal_id} tem {len(filtered_authors)} deputados autores "
                    f"(tipo {proposal_type}) – vai gerar muitas arestas."
                )

            # acumular peso de colaboração
            self.collab_weights = self.addCollabEdge(
                self.collab_weights, filtered_authors, n_proposal_weight, False
            )

    def addCollabEdge(self, graph, collab_list, proposal_weight, archived):
        '''
        Calcula o número de colaborações que ocorreu entre os deputados em uma proposicao
        '''
        proposal_weight = proposal_weight
        if bool(archived) is True:
            proposal_weight = proposal_weight * 0.5

        edges = generateEdges(collab_list)
        for edge in edges:
            if edge in graph:
                graph[edge] += proposal_weight
            else:
                graph[edge] = proposal_weight

        return graph

    def addCollabPertinence(self, graph, collab_list, proposal_pertinence):
        '''
        Calcula o quanto propostas isncritas em conjunto entre dois ou mais deputados foram aceitas na câmara
        '''
        edges = generateEdges(collab_list)
        for edge in edges:
            if edge in graph:
                graph[edge] += proposal_pertinence
            else:
                graph[edge] = proposal_pertinence
        return graph

    def setCollaborationsSuccess(self):
        """
        Define atributo de pertinência para cada aresta. Esse atributo representa os projetos entre dois deputados
        que em algum nível foram aceitos pela câmara.

        Ajustes:
        - mesmo filtro de autores válidos e deduplicação usado em setCollaborations
        """
        deputies_set = set(self.deputies_ids)

        print("Calculando pertinência das coautorias (setCollaborationsSuccess)...")
        for proposal_id in list(self.proposals.keys()):
            if proposal_id not in self.proposal_authors:
                continue

            proposal_authors = self.proposal_authors[proposal_id]
            filtered_authors = [a for a in proposal_authors if a in deputies_set]
            filtered_authors = sorted(set(filtered_authors))

            if len(filtered_authors) <= 1:
                continue

            proposal = self.proposals[proposal_id]
            proposal_type = proposal["siglaTipo"]
            if proposal_type not in proposal_weight:
                continue

            proposal_status = int(proposal["ultimoStatus_idSituacao"])
            n_proposal_weight = proposal_weight[proposal_type]

            status_pertinence = 0
            for status in positive_proposal_status:
                if int(proposal_status) == status["status_code"]:
                    status_pertinence = status["positive_pertinence"]
                    break

            pertinence_weighted = n_proposal_weight * status_pertinence

            self.collab_pertinence = self.addCollabPertinence(
                self.collab_pertinence, filtered_authors, pertinence_weighted
            )

    def setDeputiesIndividualProposals(self):
        """
        Propostas individuais escritas por um deputado e ponderadas por peso de acordo com seu tipo.

        Ajustes:
        - considera apenas deputados em self.deputies_ids
        - garante que só propostas com exatamente 1 deputado válido contam como "individuais"
        """
        deputies_set = set(self.deputies_ids)
        deputies_weight = {}

        print("Calculando propostas individuais (setDeputiesIndividualProposals)...")
        for proposal_id, authors_list in self.proposal_authors.items():
            if proposal_id not in self.proposals:
                continue

            # filtrar só deputados válidos
            filtered_authors = [a for a in authors_list if a in deputies_set]
            filtered_authors = sorted(set(filtered_authors))

            # só conta como individual se sobrou exatamente 1 deputado
            if len(filtered_authors) != 1:
                continue

            author_id = filtered_authors[0]
            proposal_type = self.proposals[proposal_id]["siglaTipo"]
            if proposal_type not in proposal_weight:
                continue

            n_proposal_weight = proposal_weight[proposal_type]

            if author_id in deputies_weight:
                deputies_weight[author_id] += n_proposal_weight
            else:
                deputies_weight[author_id] = n_proposal_weight

        self.deputies_proposals = deputies_weight

    def setDeputiesIndividualSuccessProposals(self):
        '''
        Propostas escritas por apenas um deputado que tiveram algum grau de aceitação na camara, ponderadas também
        por peso de acordo com o seu tipo
        '''
        deputies_pertincence = {}
        for proposal_id in list(self.proposals.keys()):
            authors_list = self.proposal_authors[proposal_id]
            n_authors = len(authors_list)
            # checks if the proposal have only one author
            if (n_authors == 1 and (proposal_id in list(self.proposals.keys()))):
                author_id = authors_list[0]
                proposal_type = self.proposals[proposal_id]['siglaTipo']
                proposal_status = int(self.proposals[proposal_id]['ultimoStatus_idSituacao'])
                proposal_weight = proposal_weight[proposal_type]
                status_pertinence = 0

                for status in positive_proposal_status:
                    if(int(proposal_status) == status['status_code']):
                        status_pertinence = status['positive_pertinence']
                pertinence_weighted = proposal_weight * status_pertinence

                if(author_id in deputies_pertincence):
                    deputies_pertincence[author_id] += pertinence_weighted
                else:
                    deputies_pertincence[author_id] = pertinence_weighted

        self.deputies_proposals_pertinence = deputies_pertincence

    def setDeputiesRoleInfluence(self):
        '''
        Calcula a influência de um deputado de acordo com os cargos que este ocupo na câmara nos anos
        referentes as legislaturas selecionadas
        '''
        deputies_weight = {}
        role_weight_dict = role_weights
        for deputy_id, role in self.legislative_roles.iterrows():
            role_name = role['role_name']
            deputy_id = str(deputy_id)
            if (deputy_id in self.deputies_ids):
                if(role_name in role_weight_dict.keys()):
                    weight = role_weight_dict[role_name]
                elif("Líder" in role_name):
                    party_id = role['role_place_id']
                    party_weight = (self.parties[party_id]["members_number"]/513) * 30
                    weight = role_weight_dict["Líder de partido"] * party_weight
                if(deputy_id in deputies_weight):
                    deputies_weight[deputy_id] += weight
                else:
                    deputies_weight[deputy_id] = weight

        self.roles_relevance = deputies_weight

    def setDeputiesRegion(self):
    
        for deputy_id in self.deputies_ids:
            if deputy_id in self.deputies and "uf" in self.deputies[deputy_id]:
                uf = self.deputies[deputy_id]["uf"]
                self.deputies[deputy_id]["region"] = getUfRegion(uf)
