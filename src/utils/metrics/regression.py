import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


import pandas as pd
import numpy as np
from sklearn.metrics import r2_score
from scipy.stats import pearsonr

def calculate_metrics_regression(
    df_real: pd.DataFrame,
    df_pred: pd.DataFrame,
    col_real: str,
    col_pred: str,
    on: list[str] | None = None,
) -> tuple[dict, pd.DataFrame]:
    """
    Calcula métricas de regressão usando as colunas
    especificadas em 'on' para alinhamento.

    Padrão: cálculo diário (on=["date"])
    """

    if on is None:
        on = ["date"]
        
    print(df_real.columns)
    print(df_pred.columns)

    df_merged = pd.merge(
        df_real[on + [col_real]],
        df_pred[on + [col_pred]],
        on=on,
        how="inner",
    )

    if df_merged.empty:
        raise ValueError(
            f"Nenhuma correspondência encontrada para merge usando {on}"
        )

    y_true = df_merged[col_real].to_numpy()
    y_pred = df_merged[col_pred].to_numpy()

    df_erros = df_merged.copy()

    df_erros["erro_absoluto"] = np.abs(y_true - y_pred)
    df_erros["erro_quadrado"] = (y_true - y_pred) ** 2

    df_erros["erro_percentual"] = np.where(
        y_true != 0,
        np.abs((y_true - y_pred) / y_true) * 100,
        np.nan,
    )

    mae = df_erros["erro_absoluto"].mean()
    mse = df_erros["erro_quadrado"].mean()
    rmse = np.sqrt(mse)
    mape = df_erros["erro_percentual"].mean()

    r2 = r2_score(y_true, y_pred)

    corr_pearson = (
        pearsonr(y_true, y_pred)[0]
        if len(df_merged) > 1
        else np.nan
    )

    metricas = {
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "MAPE (%)": mape,
        "R²": r2,
        "Pearson": corr_pearson,
        "N": len(df_merged),
    }

    return metricas, df_erros