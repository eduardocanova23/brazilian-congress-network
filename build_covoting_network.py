from source.CovotingNetworkBuilder import CovotingNetworkBuilder
import os

def main():
    # imita a lógica do cli.py antes de construir a rede
    os.chdir("./source")

    builder = CovotingNetworkBuilder(
        votes_detail_path="../data/votes_detail_info.csv",  # nota o ../data, já que agora estamos em ./source
        min_common_votes=1,
        consider_votes=("Sim", "Não"),
    )
    builder.build_network()
    builder.save_network(
    network_name="covoting-network",
    use_version=True,
    output_dir="../data/networks"   # <<< mude para isso
)


if __name__ == "__main__":
    main()
