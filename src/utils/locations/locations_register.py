from pathlib import Path

from kedro.config import OmegaConfigLoader

conf_path = Path("../../../base")
conf_loader = OmegaConfigLoader(conf_source=conf_path, config_patterns={"parameters": ["parameters*"]})

parameters = conf_loader.get("parameters*")


LOCATIONS = {
    "argemiro": {
        "path_shapefile": "data/00_shapefiles/argemiro_reservatorio.geojson",
        "path_cav": "notebooks/data/cotas/argemiro_cotas.csv",
        "ground_truth_path_df":"notebooks/data/ana/argemiro_ana.csv",
        },
    "engenheiro_avidos": {
        "path_shapefile": "data/00_shapefiles/engenheiro_avidos_reservatorio.geojson",
        "path_cav": "notebooks/data/cotas/engenheiro_avidos_cotas.csv",
        "ground_truth_path_df":"notebooks/data/ana/engenheiro_avidos_ana.csv",
        },
    "mares": {
        "path_shapefile": "data/00_shapefiles/mares_reservatorio.geojson",
        "path_cav": "notebooks/data/cotas/mares_cotas.csv",
        "ground_truth_path_df":"notebooks/data/ana/mares_ana.csv",
        },
    "lagoa_do_arroz": {
        "path_shapefile": "data/00_shapefiles/lagoa_do_arroz_reservatorio.geojson",
        "path_cav": "notebooks/data/cotas/lagoa_do_arroz_cotas.csv",
        "ground_truth_path_df":"notebooks/data/ana/lagoa_do_arroz_ana.csv",
        },
    "sume": {
        "path_shapefile": "data/00_shapefiles/sume_reservatorio.geojson",
        "path_cav": "notebooks/data/cotas/sume_cotas.csv",
        "ground_truth_path_df":"notebooks/data/ana/sume_ana.csv",
        },
    "gramame": {
        "path_shapefile": "data/00_shapefiles/gramame_mamuaba_reservatorio.geojson",
        "path_cav": "notebooks/data/cotas/gramame_mamuaba_cotas.csv",
        "ground_truth_path_df":"notebooks/data/ana/gramame_mamuaba_ana.csv",
        },
}