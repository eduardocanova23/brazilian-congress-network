import ast
import os
import sys
from datetime import datetime

from source.CovotingNetworkBuilder import CovotingNetworkBuilder


def parse_list_arg(arg_str, name="anos"):
    """
    Converte uma string tipo "[2019,2020]" em [2019, 2020].
    Aceita também "2019" -> [2019].
    """
    try:
        value = ast.literal_eval(arg_str)
    except Exception:
        raise SystemExit(
            f'Erro ao interpretar {name}. Use algo como "[2019,2020]" ou "2019".'
        )

    if isinstance(value, int):
        return [value]
    if isinstance(value, (list, tuple)):
        return [int(x) for x in value]

    raise SystemExit(
        f"Formato inválido para {name}: {arg_str!r}. "
        f"Use uma lista, ex: \"[2019,2020]\"."
    )


def main():
    if len(sys.argv) < 2:
        print(
            "Uso:\n"
            "  python prepare_covoting_for_years.py \"[2019,2020]\"\n\n"
            "ATENÇÃO: este script NÃO roda o VotesMiner.\n"
            "Ele usa o arquivo data/votes_detail_info.csv que você já tiver preparado\n"
            "antes com o cli.py (VotesMiner) para os anos desejados."
        )
        sys.exit(1)

    years = parse_list_arg(sys.argv[1], name="anos")
    years_str = "_".join(str(y) for y in years)

    print(f"Construindo rede de covotação para anos já presentes em votes_detail_info.csv: {years_str}")

    # 1) Muda cwd para ./source, como no build_covoting_network.py
    original_cwd = os.getcwd()
    try:
        os.chdir("./source")

        builder = CovotingNetworkBuilder(
            votes_detail_path="../data/votes_detail_info.csv",
            min_common_votes=1,
            consider_votes=("Sim", "Não"),
        )

        builder.build_network()

        # 2) Monta nome do arquivo com anos + timestamp, controlando diretamente
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        network_name = f"covoting-{years_str}-{timestamp}"

        builder.save_network(
            network_name=network_name,
            use_version=False,          # já colocamos o timestamp no nome
            output_dir="../data/networks",
        )

    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()
