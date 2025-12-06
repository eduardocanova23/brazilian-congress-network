import requests

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"

def count_proposals_from_api(ano, sigla_tipos):
    total_ids = set()
    for tipo in sigla_tipos:
        pagina = 1
        while True:
            params = {
                "ano": ano,
                "siglaTipo": tipo,
                "itens": 100,
                "pagina": pagina
            }
            r = requests.get(BASE_URL, params=params)
            r.raise_for_status()
            dados = r.json().get("dados", [])
            if not dados:
                break
            for item in dados:
                total_ids.add(item["id"])
            pagina += 1
    return total_ids

if __name__ == "__main__":
    ano = 2021
    tipos = ["PL", "PLP", "PLN", "PLV", "PEC"]

    ids = count_proposals_from_api(ano, tipos)
    print(f"Ano {ano}, tipos {tipos}: {len(ids)} proposições distintas na API")
