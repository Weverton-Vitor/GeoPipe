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
