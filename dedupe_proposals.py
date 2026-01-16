import pandas as pd
import requests
import time

p = pd.read_csv("./data/proposals_info.csv")

# 1) escolhe um ID por ementa
rep = (
    p.groupby("ementa", as_index=False)
     .first()[["id", "ementa"]]
)

print("IDs representativos:", len(rep))

API_URL = "https://dadosabertos.camara.leg.br/api/v2/proposicoes/{}"
session = requests.Session()

rows = []

for i, row in rep.iterrows():
    pid = int(row["id"])
    r = session.get(API_URL.format(pid), headers={"Accept": "application/json"})
    r.raise_for_status()
    dados = r.json()["dados"]

    rows.append({
        "ementa": row["ementa"],
        "siglaTipo": dados.get("siglaTipo"),
        "numero": dados.get("numero"),
        "ano": dados.get("ano"),
    })

    if i % 200 == 0:
        print(i)
        time.sleep(0.5)

df_key = pd.DataFrame(rows)

# 2) junta de volta
p2 = p.merge(df_key, on="ementa", how="left")

# 3) conta proposições canônicas
canon = p2.drop_duplicates(subset=["siglaTipo", "numero", "ano"])
print("Proposições canônicas:", canon.shape[0])
