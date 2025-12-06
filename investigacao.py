import pandas as pd

# 1) Ler o arquivo bruto de autores de 2022
auth = pd.read_csv("data/authors/proposicoesAutores-2022.csv", sep=";")

print("Colunas em proposicoesAutores-2022.csv:")
print(auth.columns)

# Garantir tipos
auth["idProposicao"] = auth["idProposicao"].astype(int)

# 2) Construir uma chave única de autor (independente do tipo)
cols_autor = []
for col in ["codTipoAutor", "idDeputadoAutor", "nomeAutor"]:
    if col in auth.columns:
        cols_autor.append(col)

if not cols_autor:
    raise RuntimeError("Nenhuma coluna adequada para identificar autores encontrada.")

auth["autor_key"] = auth[cols_autor].astype(str).agg("|".join, axis=1)

# 3) Contar autores distintos por proposição
counts = auth.groupby("idProposicao")["autor_key"].nunique()

max_autores = counts.max()
print(f"Máximo de autores distintos encontrado em 2022: {max_autores}")

ids_max = counts[counts == max_autores].index.tolist()
print(f"IDs de proposições com {max_autores} autores:")
print(ids_max)

