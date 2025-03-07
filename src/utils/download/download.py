from datetime import datetime


def is_TOA(colecao):
    """
    Verifica se a coleção do Google Earth Engine (GEE) é BOA (Bottom of Atmosphere)
    ou TOA (Top of Atmosphere), com base no nome da coleção.

    Parâmetros:
        colecao (str): Nome da coleção no GEE.

    Retorno:
        str: 'BOA' se a coleção for de Reflectância de Superfície,
             'TOA' se a coleção for de Reflectância de Topo da Atmosfera,
             'Desconhecido' se não for possível determinar.
    """
    # Padrões comuns de coleções TOA e BOA
    if "TOA" in colecao.upper() and "SR" not in colecao.upper():
        return True

    return False


def get_original_bands_name(satelite: str, fake_name_bands: list, is_toa: bool):
    band_prefix = "" if is_toa else "SR_"
    band_prefix_thermal = "" if is_toa else "ST_"

    band_mappings = {
        "LT05": {
            "coastal": None,
            "blue": f"{band_prefix}B1",
            "green": f"{band_prefix}B2",
            "red": f"{band_prefix}B3",
            "nir": f"{band_prefix}B4",
            "swir1": f"{band_prefix}B5",
            "swir2": f"{band_prefix}B7",
            "pan": None,
            "cirrus": None,
            "thermal1": f"{band_prefix_thermal}B6",
            "thermal2": None,
            "QA_PIXEL": "QA_PIXEL",
        },
        "LE07": {
            "coastal": None,
            "blue": f"{band_prefix}B1",
            "green": f"{band_prefix}B2",
            "red": f"{band_prefix}B3",
            "nir": f"{band_prefix}B4",
            "swir1": f"{band_prefix}B5",
            "swir2": f"{band_prefix}B7",
            "pan": f"{band_prefix}B8",
            "cirrus": None,
            "thermal1": f"{band_prefix_thermal}B6",
            "thermal2": None,
            "QA_PIXEL": "QA_PIXEL",
        },
        "LC08": {
            "coastal": f"{band_prefix}B1",
            "blue": f"{band_prefix}B2",
            "green": f"{band_prefix}B3",
            "red": f"{band_prefix}B4",
            "nir": f"{band_prefix}B5",
            "swir1": f"{band_prefix}B6",
            "swir2": f"{band_prefix}B7",
            "pan": f"{band_prefix}B8",
            "cirrus": f"{band_prefix}B9",
            "thermal1": f"{band_prefix_thermal}B10",
            "thermal2": f"{band_prefix}B11",
            "QA_PIXEL": "QA_PIXEL",
        },
        "LC09": {
            "coastal": "B1",
            "blue": f"{band_prefix}B2",
            "green": f"{band_prefix}B3",
            "red": f"{band_prefix}B4",
            "nir": f"{band_prefix}B5",
            "swir1": f"{band_prefix}B6",
            "swir2": f"{band_prefix}B7",
            "pan": f"{band_prefix}B8",
            "cirrus": f"{band_prefix}B9",
            "thermal1": f"{band_prefix_thermal}B10",
            "thermal2": f"{band_prefix}B11",
            "QA_PIXEL": "QA_PIXEL",
        },
        "S2": {
            "coastal": "B1",
            "blue": "B2",
            "green": "B3",
            "red": "B4",
            "rededge1": "B5",
            "rededge2": "B6",
            "rededge3": "B7",
            "nir": "B8",
            "nir_narrow": "B8A",
            "swir1": "B11",
            "swir2": "B12",
            "cirrus": "B10",
            "QA_PIXEL": "QA60",
        },
    }

    return (
        [band_mappings[satelite].get(band, None) for band in fake_name_bands]
        if satelite in band_mappings
        else []
    )


def adjust_date(satelite: str, start_date_str: str, end_date_str: str) -> tuple:
    satellite_dates = {
        "LT05": ("1984-03-01", "2013-06-05"),
        "LE07": ("1999-04-15", None),  # Ainda operacional
        "LC08": ("2013-02-11", None),  # Ainda operacional
        "LC09": ("2021-09-27", None),  # Ainda operacional
        "S2": ("2015-06-23", None),  # Sentinel-2A lançado em 2015
    }

    if satelite not in satellite_dates:
        raise ValueError(f"Satélite {satelite} não reconhecido.")

    sat_start_date, sat_end_date = satellite_dates[satelite]
    sat_start_date = datetime.strptime(sat_start_date, "%Y-%m-%d")
    sat_end_date = datetime.strptime(sat_end_date, "%Y-%m-%d") if sat_end_date else None

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    if start_date < sat_start_date:
        start_date = sat_start_date
    if sat_end_date and start_date > sat_end_date:
        start_date = sat_end_date

    if end_date < sat_start_date:
        end_date = sat_start_date
    if sat_end_date and end_date > sat_end_date:
        end_date = sat_end_date

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def validate_date(satelite: str, date_str: str):
    satellite_dates = {
        "LT05": ("1984-03-01", "2013-06-05"),
        "LE07": ("1999-04-15", None),  # Ainda operacional
        "LC08": ("2013-02-11", None),  # Ainda operacional
        "LC09": ("2021-09-27", None),  # Ainda operacional
        "S2": ("2015-06-23", None),  # Sentinel-2A lançado em 2015
    }

    if satelite not in satellite_dates:
        raise ValueError(f"Satélite {satelite} não reconhecido.")

    start_date, end_date = satellite_dates[satelite]
    input_date = datetime.strptime(date_str, "%Y-%m-%d")
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

    if input_date < start_date:
        raise ValueError(
            f"Erro: A data {date_str} é anterior ao início do satélite {satelite} ({start_date.date()})."
        )
    if end_date and input_date > end_date:
        raise ValueError(
            f"Erro: A data {date_str} é posterior ao fim do satélite {satelite} ({end_date.date()})."
        )

    return True
