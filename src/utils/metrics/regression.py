import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


import pandas as pd
import numpy as np
from sklearn.metrics import r2_score
from scipy.stats import pearsonr


def calculate_metrics_regression_by_month(
    df_real: pd.DataFrame,
    df_pred: pd.DataFrame,
    col_real: str,
    col_pred: str,
    on: list,  # colunas de junção como ['ano', 'mes'] ou ['data']
) -> tuple[dict, pd.DataFrame]:
    """
    Calcula métricas de regressão considerando apenas meses presentes em ambos os DataFrames.

    Parâmetros:
    - df_real: DataFrame com os valores reais.
    - df_pred: DataFrame com os valores previstos.
    - col_real: Nome da coluna com os valores reais.
    - col_pred: Nome da coluna com os valores previstos.
    - on: Lista com as colunas para fazer o merge (ex: ['ano', 'mes'] ou ['data']).

    Retorna:
    - dicionário com as métricas MAE, MSE, RMSE, MAPE, R² e Correlação de Pearson.
    - DataFrame com colunas real, previsto e os erros ponto a ponto.
    """

    # Merge interno (apenas datas/mês que existem em ambos)
    df_merged = pd.merge(
        df_real[on + [col_real]], df_pred[on + [col_pred]], on=on, how="inner"
    )

    print(df_merged.columns)
    print(df_merged.columns)
    print(df_merged.columns)
    print(df_merged.columns)
    print(df_merged.columns)
    print(df_merged.columns)

    # Extrair vetores
    y_true = df_merged[col_real].values
    y_pred = df_merged[col_pred].values

    # Cálculo dos erros ponto a ponto
    df_erros = df_merged.copy()
    df_erros["erro_absoluto"] = np.abs(y_true - y_pred)
    df_erros["erro_quadrado"] = (y_true - y_pred) ** 2
    df_erros["erro_percentual"] = np.abs((y_true - y_pred) / y_true) * 100

    # Métricas globais
    mae = df_erros["erro_absoluto"].mean()
    mse = df_erros["erro_quadrado"].mean()
    rmse = np.sqrt(mse)
    mape = df_erros["erro_percentual"].mean()
    r2 = r2_score(y_true, y_pred)
    corr_pearson, _ = pearsonr(y_true, y_pred)

    metricas = {
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "MAPE (%)": mape,
        "R²": r2,
        "Pearson": corr_pearson,
    }

    return metricas, df_erros
