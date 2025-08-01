import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.dates import DateFormatter

logger = logging.getLogger(__name__)


def plot_tif(tif_path, bandas=None, titulo="Imagem .tif", binarization_gt=None):
    """
    Exibe uma imagem .tif usando rasterio e matplotlib.

    Parâmetros:
    - tif_path (str): caminho para o arquivo .tif
    - bandas (list[int] ou None): lista com os índices das bandas a exibir (ex: [4, 3, 2] para RGB do Sentinel-2).
                                  Se None, exibe a primeira banda como imagem em escala de cinza.
    - titulo (str): título da imagem exibida
    - binarization_gt (float): se diferente de 0, aplica binarização na imagem (1 se > binarization_gt, senão 0)
    """
    with rasterio.open(tif_path) as src:
        if bandas:
            img = np.stack([src.read(b) for b in bandas], axis=-1).astype(np.float32)

            # Normalizar para [0, 1]
            img -= img.min()
            img /= img.max()

            if binarization_gt is not None:
                # Converter imagem para escala de cinza antes de binarizar
                gray = img.mean(axis=-1)
                binary = (gray > binarization_gt).astype(np.uint8)

                plt.figure(figsize=(10, 10))
                plt.imshow(binary, cmap="gray")
            else:
                plt.figure(figsize=(10, 10))
                plt.imshow(img)
        else:
            img = src.read(1).astype(np.float32)

            if binarization_gt is not None:
                binary = (img > binarization_gt).astype(np.uint8)
                plt.imshow(binary, cmap="gray")
            else:
                plt.imshow(img, cmap="gray")

        plt.title(titulo)
        plt.axis("off")
        plt.show()


def plot_year_x_variable(
    data: pd.DataFrame,
    year: str,
    year_column: str = "year",
    month_column: str = "month",
    y_varible: str = "CLOUDY_PIXEL_PERCENTAGE",
) -> None:
    filtered_data = data.loc[data[year_column] == year]
    plt.plot(filtered_data[month_column], filtered_data[y_varible])
    plt.title(f"{y_varible} - {year}")


def plot_water_x_cloud_percent_filter(
    data: pd.DataFrame,
    year: int = None,
    y_varible: str = "CLOUDY_PIXEL_PERCENTAGE",
    cloud_percent: int = 0,
) -> None:
    filtered_data = data.loc[data["CLOUDY_PIXEL_PERCENTAGE"] <= cloud_percent]
    if year is not None:
        filtered_data = filtered_data.loc[data["year"] == year]

    water_media_data = filtered_data.groupby("month")[y_varible].mean()
    water_media_data = water_media_data.to_dict()

    water_months = {x: 0 for x in range(1, 13)}
    water_months.update(water_media_data)

    plt.plot(list(water_months.keys()), list(water_months.values()))
    plt.title(f"{y_varible} - {year} (cloud: {cloud_percent}%)")


def plot_water_x_cloud_percent(
    data: pd.DataFrame, year: int = None, y_variable: str = "CLOUDY_PIXEL_PERCENTAGE"
) -> None:
    """
    Plota a média mensal da variável `y_variable` para diferentes faixas de cobertura de nuvens (0 a 100%, de 10 em 10%).

    Parâmetros:
    - data (pd.DataFrame): DataFrame com colunas 'CLOUDY_PIXEL_PERCENTAGE', 'year', 'month', e a variável desejada.
    - year (int, opcional): Ano a ser filtrado.
    - y_variable (str): Nome da variável a ser analisada (default: 'CLOUDY_PIXEL_PERCENTAGE').
    """
    plt.figure(figsize=(12, 8))

    for cloud_percent in range(0, 101, 10):
        filtered_data = data[data["CLOUDY_PIXEL_PERCENTAGE"] <= cloud_percent]

        if year is not None:
            filtered_data = filtered_data[filtered_data["year"] == year]

        # Calcula a média mensal da variável
        monthly_means = filtered_data.groupby("month")[y_variable].mean().to_dict()

        # Garante que todos os meses (1 a 12) estejam presentes, mesmo que com valor 0
        all_months = {month: 0 for month in range(1, 13)}
        all_months.update(monthly_means)

        plt.plot(
            list(all_months.keys()),
            list(all_months.values()),
            label=f"≤ {cloud_percent}%",
        )

    plt.title(
        f"Média mensal de {y_variable} ({f'ano ' + str(year) if year else 'todos os anos'})\npara diferentes filtros de cobertura de nuvem"
    )
    plt.xlabel("Mês")
    plt.ylabel(f"Média de {y_variable}")
    plt.xticks(range(1, 13))
    plt.legend(title="Cobertura de Nuvem")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_water_x_cloud_percent_over_time(
    data: pd.DataFrame, y_variable: str = "CLOUDY_PIXEL_PERCENTAGE"
) -> None:
    """
    Plota a média mensal da variável `y_variable` ao longo do tempo (ano + mês),
    para diferentes faixas de cobertura de nuvens (0 a 100%, de 10 em 10%).

    Parâmetros:
    - data (pd.DataFrame): DataFrame com colunas 'CLOUDY_PIXEL_PERCENTAGE', 'year', 'month' e a variável desejada.
    - y_variable (str): Nome da variável a ser analisada.
    """
    # Garante que a coluna de tempo esteja ordenada corretamente
    data = data.copy()
    data["date"] = pd.to_datetime(data[["year", "month"]].assign(day=1))
    data.sort_values("date", inplace=True)

    plt.figure(figsize=(14, 7))

    for cloud_percent in range(0, 101, 10):
        filtered_data = data[data["CLOUDY_PIXEL_PERCENTAGE"] <= cloud_percent]

        # Média mensal da variável para essa faixa de nuvem
        grouped = filtered_data.groupby("date")[y_variable].mean().sort_index()

        plt.plot(grouped.index, grouped.values, label=f"≤ {cloud_percent}%")

    plt.title(f"Média mensal de {y_variable} por faixa de cobertura de nuvens")
    plt.xlabel("Tempo (Ano/Mês)")
    plt.ylabel(f"Média de {y_variable}")
    plt.grid(True)
    plt.legend(title="Cobertura de Nuvem (%)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plot_water_over_time(
    data: pd.DataFrame,
    y_variables: list[str] = [
        "water_area"
    ],  # Altere conforme o nome real da sua variável
    labels: list[str] = ["water_area"],  # Altere conforme o nome real da sua variável
    title: str = "Média mensal ao longo do tempo",
) -> None:
    """
    Plota a média mensal da variável `y_variable` ao longo do tempo (ano + mês).

    Parâmetros:
    - data (pd.DataFrame): DataFrame com colunas 'year', 'month' e a variável desejada.
    - y_variable (str): Nome da variável a ser analisada.
    """
    # Cria a coluna de data (1º dia de cada mês)
    data = data.copy()
    data["date"] = pd.to_datetime(data[["year", "month"]].assign(day=1))

    plt.figure(figsize=(14, 7))
    for y_variable, label in zip(y_variables, labels):
        # Calcula a média mensal
        monthly_mean = data.groupby("date")[y_variable].mean().sort_index()

        # Plot
        plt.plot(monthly_mean.index, monthly_mean.values, marker="o", label=label)

    plt.title(title)
    plt.xlabel("Tempo (Ano/Mês)")
    plt.ylabel(f"Média de ")
    plt.legend(title="Cobertura de Nuvem")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.ticklabel_format(style="plain", axis="y")
    # plt.tight_layout()
    plt.show()


def plot_monthly_water(
    data: pd.DataFrame,
    year: int = None,
    y_variable: str = "m2_area",  # Altere para o nome da sua variável de interesse
) -> None:
    """
    Plota a média mensal da variável `y_variable`.

    Parâmetros:
    - data (pd.DataFrame): DataFrame com colunas 'year', 'month' e a variável desejada.
    - year (int, opcional): Ano a ser filtrado (default: None = todos os anos).
    - y_variable (str): Nome da variável a ser analisada.
    """
    if year is not None:
        data = data[data["year"] == year]

    # Calcula a média mensal da variável
    monthly_means = data.groupby("month")[y_variable].mean().to_dict()

    # Garante que todos os meses (1 a 12) estejam presentes
    all_months = {month: 0 for month in range(1, 13)}
    all_months.update(monthly_means)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(list(all_months.keys()), list(all_months.values()), marker="o")

    plt.title(
        f"Média mensal de {y_variable} "
        + (f"(ano {year})" if year else "(todos os anos)")
    )
    plt.xlabel("Mês")
    plt.ylabel(f"Média de {y_variable}")
    plt.xticks(range(1, 13))
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_series_ano_mes(series_dict, volume_columns, data_inicio, data_fim, titulo=None):
    """
    Plota séries temporais com colunas separadas de 'ano' e 'mês' e diferentes comprimentos.

    Parâmetros:
        series_dict (dict): {'nome_série': DataFrame com colunas ['ano', 'mes', 'valor']}.
        data_inicio (str): Data inicial no formato "mm/yyyy".
        data_fim (str): Data final no formato "mm/yyyy".
        titulo (str): Título do gráfico (opcional).
    """
    # Converte as datas para datetime
    data_inicio = pd.to_datetime(f"01/{data_inicio}", format="%d/%m/%Y")
    data_fim = pd.to_datetime(
        f"01/{data_fim}", format="%d/%m/%Y"
    ) + pd.offsets.MonthEnd(0)

    # Inicia figura
    figure = plt.figure(figsize=(12, 5))

    for i, (nome, df) in enumerate(series_dict.items()):
        # Cria coluna de datas com ano e mês
        df = df.copy()
        df["data"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
        df = df.set_index("data")

        # Filtra pelo intervalo
        df_plot = df[(df.index >= data_inicio) & (df.index <= data_fim)]

        try:
            # Plota
            plt.plot(df_plot.index, df_plot[volume_columns[i]], label=nome)
        except Exception as e:
            logger.warning(f"Error to plot {volume_columns[i]} of {nome}: {e}")

    # Formatação
    plt.xlabel("Data")
    plt.ylabel("Volume de água (10⁶ m³)")
    plt.title(titulo or "Séries Temporais")
    plt.legend()
    plt.grid(True)

    # Eixo X no formato mm/yyyy
    plt.gca().xaxis.set_major_formatter(DateFormatter("%m/%Y"))

    plt.tight_layout()
    # plt.show()
    return figure
