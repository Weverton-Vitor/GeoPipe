import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def calculate_metrics_regression(
    df_real: pd.DataFrame,
    df_pred: pd.DataFrame,
    col_real: str,
    col_pred: str
) -> dict:

    """
    Calculate regression metrics between two columns of two DataFrames.

    Parameters:
    - df_real: DataFrame with the actual values.
    - df_pred: DataFrame with the predicted values.
    - col_real: Name of the column in the actual values.
    - col_pred: Name of the column in the predicted values.

    Returns:
    - dictionary with metrics MAE, MSE, RMSE, MAPE, R², and Pearson correlation.
    - df_erros: DataFrame with real, predicted, and point-wise errors.
    """

    # Extrair os vetores
    y_true = df_real[col_real].values
    y_pred = df_pred[col_pred].values

    # Verificação de tamanho
    if len(y_true) != len(y_pred):
        raise ValueError("As colunas devem ter o mesmo número de elementos.")

    # DataFrame com erros por ponto
    df_erros = pd.DataFrame({
        'real': y_true,
        'previsto': y_pred,
        'erro_absoluto': np.abs(y_true - y_pred),
        'erro_quadrado': (y_true - y_pred)**2,
        'erro_percentual': np.abs((y_true - y_pred) / y_true) * 100
    })

    # Métricas globais
    mae = df_erros['erro_absoluto'].mean()
    mse = df_erros['erro_quadrado'].mean()
    rmse = np.sqrt(mse)
    mape = df_erros['erro_percentual'].mean()
    r2 = r2_score(y_true, y_pred)
    corr_pearson, _ = pearsonr(y_true, y_pred)

    metricas = {
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "MAPE (%)": mape,
        "R²": r2,
        "Pearson": corr_pearson
    }

    return metricas, df_erros

