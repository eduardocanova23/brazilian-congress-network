import click
import ast
from miners import MinerFactory
from source import NetworkBuilder
import os

# Mapa oficial ano - legislatura (Câmara dos Deputados)
LEGISLATURE_PERIODS = {
    54: range(2011, 2015),
    55: range(2015, 2019),
    56: range(2019, 2023),
    57: range(2023, 2027),
}

def validate_years_legislatures(years, legislatures):
    """
    Garante que todos os anos informados pertencem a pelo menos
    uma das legislaturas informadas. Se não pertencerem, levanta erro.
    """
    allowed_years = set()
    for leg in legislatures:
        if leg not in LEGISLATURE_PERIODS:
            raise click.BadParameter(
                f"Legislatura {leg} não está mapeada em LEGISLATURE_PERIODS. "
                f"Use uma das: {sorted(LEGISLATURE_PERIODS.keys())}."
            )
        allowed_years.update(LEGISLATURE_PERIODS[leg])

    invalid_years = [y for y in years if y not in allowed_years]
    if invalid_years:
        raise click.BadParameter(
            f"Anos {invalid_years} não pertencem às legislaturas {legislatures}. "
            f"Mapa usado: { {k: list(v) for k, v in LEGISLATURE_PERIODS.items()} }"
        )


def dateStringInterval(dates):
    min_year = min(dates)
    max_year = max(dates)
    min_string = "{}-01-01".format(min_year)
    max_string = "{}-01-01".format(max_year)
    return min_string, max_string

@click.command()
@click.option(
    '--extract_data',
    nargs=3,
    type=str,
    default=None,
    help="""
Extrai os dados desejados no intervalo de tempo fornecido.

Recebe como argumento uma lista de miners, uma lista de anos e uma lista de legislaturas.

[miners] [anos] [legislaturas]

Os miners disponíveis são:
APIProposalMiner -> proposições usando API,
AuthorsMiner -> autores das proposições,
DeputiesMiner -> deputados ativos,
PartiesMiner -> partidos representados,
ProposalsMiner -> proposições apresentadas,
RolesMiner -> cargos dos deputados,
TSEMiner -> características pessoais.
"""
)
@click.option(
    '--build_network',
    type=click.Choice(['weighted', 'not_weighted']),
    help='Constrói a rede de coautoria de projetos. Pode ou não considerar arestas com peso.'
)
def exec_task(extract_data, build_network):
    if extract_data:
        miners = ast.literal_eval(extract_data[0])
        years = ast.literal_eval(extract_data[1])
        legislatures = ast.literal_eval(extract_data[2])
        start_date, end_date = dateStringInterval(years)

        validate_years_legislatures(years, legislatures)

        mf = MinerFactory.MinerFactory(miners, years, legislatures, start_date, end_date)
        mf.buildAll()

    if build_network:
        os.chdir('./source')
        nb = NetworkBuilder.NetworkBuilder()
        if build_network == 'weighted':
            nb.buildNetwork(True)
        else:
            nb.buildNetwork(False)
        nb.saveNetWork()

if __name__ == '__main__':
    exec_task()

