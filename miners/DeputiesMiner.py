from .AbstractMiner import Miner
from .utils import printProgressBar

import os
import time
import requests
import pandas as pd


class DeputiesMiner(Miner):
    """
    Minerador de deputados para uma ou mais legislaturas.

    Funciona em duas etapas:
      1) Lista deputados por legislatura via /deputados (paginado)
      2) Busca detalhes de cada deputado via /deputados/{id}

    Saída:
      ./data/deputies_info.csv
    """

    BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

    LIST_ENDPOINT = "/deputados"
    DETAIL_ENDPOINT = "/deputados/{id}"

    OUTPUT_PATH = "./data/deputies_info.csv"

    # Config padrão de paginação
    ITENS_POR_PAGINA = 100

    # Robustez de rede
    TIMEOUT = 30
    RETRIES = 6

    # Debug opcional
    DEBUG_PAGINATION_TEST_ACTIVE = False
    DEBUG_MAX_PAGES = 1

    def __init__(self, years=None, legislatures=None):
        super().__init__(years, legislatures)
        self.deputies_rows = []

    def mineData(self):
        self.loadDeputiesInfo()

    def createDataframe(self):
        # Já montamos o dataframe em loadDeputiesInfo
        pass

    def save2CSV(self):
        if not self.deputies_rows:
            print("DeputiesMiner: nenhum deputado para salvar.")
            return

        df = pd.DataFrame(self.deputies_rows)

        os.makedirs("./data", exist_ok=True)
        df.to_csv(self.OUTPUT_PATH, index=False, encoding="utf-8")
        print(f"DeputiesMiner: arquivo salvo em {self.OUTPUT_PATH} com {len(df)} linhas.")

    def loadDeputiesInfo(self):
        if not self.legislatures or len(self.legislatures) == 0:
            raise ValueError("DeputiesMiner: nenhuma legislatura fornecida.")

        all_ids = set()

        for leg in self.legislatures:
            ids_leg = self._list_deputies_ids_by_legislature(leg)
            if len(ids_leg) == 0:
                print(f"0 deputies mined on legislature {leg}")
            else:
                print(f"{len(ids_leg)} deputies mined on legislature {leg}")
            all_ids.update(ids_leg)

        ids_list = sorted(list(all_ids))

        if len(ids_list) == 0:
            print("Aviso: nenhum deputado retornado pela API. Interrompendo DeputiesMiner sem salvar.")
            self.deputies_rows = []
            return

        rows = []
        printProgressBar(0, len(ids_list), prefix="Detailed info about deputies:", suffix="Complete", length=50)

        for i, dep_id in enumerate(ids_list, start=1):
            detail = self._get_deputy_detail(dep_id)

            if detail is not None:
                rows.append(detail)

            printProgressBar(i, len(ids_list), prefix="Detailed info about deputies:", suffix="Complete", length=50)

        self.deputies_rows = rows
        self.save2CSV()

    def _list_deputies_ids_by_legislature(self, legislature_id: int):
        ids = []
        page = 1

        if self.DEBUG_PAGINATION_TEST_ACTIVE:
            print("DEBUG DeputiesMiner: PAGINATION TEST ACTIVE")

        while True:
            if self.DEBUG_PAGINATION_TEST_ACTIVE and page > self.DEBUG_MAX_PAGES:
                break

            url = self.BASE_URL + self.LIST_ENDPOINT
            params = {
                "idLegislatura": legislature_id,
                "itens": self.ITENS_POR_PAGINA,
                "pagina": page,
            }

            r = self._get_with_retries(url, params=params)
            if r is None:
                print(f"Error on page {page} legislature {legislature_id} status 504")
                break

            data = r.json()

            # Estrutura típica:
            # { "dados": [ { "id":..., ...}, ... ], "links": [ {"rel":"next",...}, ... ] }
            deputados = data.get("dados", [])
            if not deputados:
                break

            for d in deputados:
                dep_id = d.get("id", None)
                if dep_id is not None:
                    ids.append(int(dep_id))

            links = data.get("links", [])
            has_next = any((isinstance(x, dict) and x.get("rel") == "next") for x in links)
            if not has_next:
                break

            page += 1

        return ids

    def _get_deputy_detail(self, dep_id: int):
        url = self.BASE_URL + self.DETAIL_ENDPOINT.format(id=dep_id)

        r = self._get_with_retries(url)
        if r is None:
            return None

        payload = r.json()
        d = payload.get("dados", None)
        if not isinstance(d, dict):
            return None

        # Campos comumente presentes
        last_status = d.get("ultimoStatus", {}) if isinstance(d.get("ultimoStatus", {}), dict) else {}

        row = {
            "id": d.get("id", dep_id),
            "nome": d.get("nome", ""),
            "nomeCivil": d.get("nomeCivil", ""),
            "siglaPartido": last_status.get("siglaPartido", d.get("siglaPartido", "")),
            "siglaUf": last_status.get("siglaUf", d.get("siglaUf", "")),
            "idLegislatura": last_status.get("idLegislatura", None),
            "situacao": last_status.get("situacao", ""),
            "condicaoEleitoral": last_status.get("condicaoEleitoral", ""),
            "email": d.get("email", ""),
            "uri": d.get("uri", ""),
            "uriPartido": last_status.get("uriPartido", ""),
            "urlFoto": last_status.get("urlFoto", d.get("urlFoto", "")),
        }

        # Alguns campos podem não existir em todos os deputados
        if "sexo" in d:
            row["sexo"] = d.get("sexo", "")
        if "dataNascimento" in d:
            row["dataNascimento"] = d.get("dataNascimento", "")
        if "municipioNascimento" in d:
            row["municipioNascimento"] = d.get("municipioNascimento", "")
        if "ufNascimento" in d:
            row["ufNascimento"] = d.get("ufNascimento", "")
        if "escolaridade" in d:
            row["escolaridade"] = d.get("escolaridade", "")

        return row

    def _get_with_retries(self, url, params=None):
        last_status = None
        last_exc = None

        for attempt in range(1, self.RETRIES + 1):
            try:
                r = requests.get(url, params=params, timeout=self.TIMEOUT)

                last_status = r.status_code

                # Retry em erros transitórios
                if r.status_code in (429, 502, 503, 504):
                    time.sleep(min(2 ** attempt, 30))
                    continue

                r.raise_for_status()
                return r

            except Exception as e:
                last_exc = e
                time.sleep(min(2 ** attempt, 30))

        # Mantém log compatível com o seu output quando 504 ocorre
        if last_status == 504:
            return None

        # Se falhar por outro motivo, levanta a exceção para não mascarar bug de endpoint
        if last_exc is not None:
            raise last_exc

        return None

