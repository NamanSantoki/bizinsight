import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb

def evaluate_forecast_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes MAE, RMSE, MAPE, R2 with robust handling of zero divisions.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    
    # Avoid div by zero in MAPE
    non_zeros = y_true != 0
    if np.any(non_zeros):
        mape = float(np.mean(np.abs((y_true[non_zeros] - y_pred[non_zeros]) / y_true[non_zeros])) * 100)
    else:
        mape = 0.0

    # R2
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 2),
        "r2": round(r2, 4)
    }

def run_chronological_forecasting(
    df: pd.DataFrame,
    date_col: str,
    target_col: str,
    forecast_horizon: int = 14,
    frequency: str = "D"
) -> Dict[str, Any]:
    """
    Strict Leakage-Free Chronological Time-Series Forecasting:
    - Verifies sufficient historical data (>20 observations)
    - Validates target and date columns
    - Aggregates by chosen frequency (daily/monthly/weekly)
    - Chronological Train/Test split (e.g. 80% train past, 20% test future)
    - Evaluates:
        1. Naive Baseline (predicts previous day / last observed)
        2. Moving Average Baseline (rolling mean)
        3. Linear Regression with Lag & Calendar features
        4. Random Forest Regressor
        5. XGBoost Regressor
    - Model comparison against baseline
    - Forecast into horizon with uncertainty bands (prediction intervals)
    """
    # 1. Verification of prerequisites
    if date_col not in df.columns:
        return {"error": f"Date column '{date_col}' does not exist in dataset."}
    if target_col not in df.columns:
        return {"error": f"Target column '{target_col}' does not exist in dataset."}

    # Prepare time-series
    ts_df = df[[date_col, target_col]].copy()
    ts_df[date_col] = pd.to_datetime(ts_df[date_col], errors='coerce')
    ts_df[target_col] = pd.to_numeric(ts_df[target_col], errors='coerce')
    ts_df = ts_df.dropna().sort_values(by=date_col)

    if len(ts_df) == 0:
        return {"error": "No valid observations after parsing date and numeric target."}

    # Aggregate by frequency
    agg_df = ts_df.groupby(pd.Grouper(key=date_col, freq=frequency))[target_col].sum().reset_index()
    agg_df = agg_df.dropna()

    if len(agg_df) < 20:
        return {
            "error": (
                f"Insufficient temporal observations: Dataset has {len(agg_df)} {frequency}-frequency aggregated periods. "
                "Reliable time-series modeling requires at least 20 historical periods to prevent deceptive predictions."
            )
        }

    # Feature engineering (strictly lag & calendar-based to prevent future leakage)
    agg_df['target'] = agg_df[target_col]
    agg_df['day_of_week'] = agg_df[date_col].dt.dayofweek
    agg_df['day_of_month'] = agg_df[date_col].dt.day
    agg_df['month'] = agg_df[date_col].dt.month
    agg_df['lag_1'] = agg_df['target'].shift(1)
    agg_df['lag_2'] = agg_df['target'].shift(2)
    agg_df['lag_7'] = agg_df['target'].shift(7 if len(agg_df) > 30 else 3)
    agg_df['rolling_mean_3'] = agg_df['target'].shift(1).rolling(window=3).mean()

    # Drop rows with NaN from lags
    clean_series = agg_df.dropna().reset_index(drop=True)
    if len(clean_series) < 15:
        return {"error": "Insufficient continuous observations after constructing lag features."}

    feature_cols = ['day_of_week', 'day_of_month', 'month', 'lag_1', 'lag_2', 'lag_7', 'rolling_mean_3']

    # Chronological Split (strictly 80% train, 20% holdout test)
    split_idx = int(len(clean_series) * 0.8)
    train_data = clean_series.iloc[:split_idx]
    test_data = clean_series.iloc[split_idx:]

    X_train = train_data[feature_cols].values
    y_train = train_data['target'].values
    X_test = test_data[feature_cols].values
    y_test = test_data['target'].values

    # 1. Naive Baseline (predicts lag_1)
    y_pred_naive = test_data['lag_1'].values
    metrics_naive = evaluate_forecast_metrics(y_test, y_pred_naive)

    # 2. Moving Average Baseline (predicts rolling_mean_3)
    y_pred_ma = test_data['rolling_mean_3'].values
    metrics_ma = evaluate_forecast_metrics(y_test, y_pred_ma)

    models_dict = {
        "Baseline (Naive Last Value)": (None, y_pred_naive, metrics_naive),
        "Baseline (Moving Average)": (None, y_pred_ma, metrics_ma)
    }

    # 3. Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred_lr = lr.predict(X_test)
    models_dict["Linear Regression"] = (lr, y_pred_lr, evaluate_forecast_metrics(y_test, y_pred_lr))

    # 4. Random Forest
    rf = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=6)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    models_dict["Random Forest"] = (rf, y_pred_rf, evaluate_forecast_metrics(y_test, y_pred_rf))

    # 5. XGBoost
    xg = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=42)
    xg.fit(X_train, y_train)
    y_pred_xg = xg.predict(X_test)
    models_dict["XGBoost"] = (xg, y_pred_xg, evaluate_forecast_metrics(y_test, y_pred_xg))

    # Model Comparison Table
    comparison_table = []
    baseline_mae = metrics_naive["mae"]

    best_model_name = "Baseline (Naive Last Value)"
    lowest_mae = baseline_mae
    best_estimator = None

    for m_name, (estimator, preds, mets) in models_dict.items():
        imp = round(((baseline_mae - mets["mae"]) / baseline_mae) * 100, 2) if baseline_mae > 0 else 0.0
        comparison_table.append({
            "model": m_name,
            "mae": mets["mae"],
            "rmse": mets["rmse"],
            "mape": mets["mape"],
            "r2": mets["r2"],
            "improvement_vs_baseline_pct": imp
        })
        if mets["mae"] < lowest_mae:
            lowest_mae = mets["mae"]
            best_model_name = m_name
            best_estimator = estimator

    # Sort comparison table by MAE ascending
    comparison_table.sort(key=lambda x: x["mae"])

    # Uncertainty & Residual standard deviation for Prediction Intervals
    if best_estimator is not None:
        best_preds_test = models_dict[best_model_name][1]
        residuals = y_test - best_preds_test
        residual_std = float(np.std(residuals)) if len(residuals) > 1 else float(np.std(y_train)) * 0.1
    else:
        residual_std = float(np.std(y_test - y_pred_naive))

    # Future recursive multi-step forecasting
    last_date = clean_series[date_col].max()
    future_forecasts = []
    
    # Carry forward historical state
    cur_history = list(clean_series['target'].values)
    cur_date = last_date

    delta = timedelta(days=1) if frequency == "D" else timedelta(days=7) if frequency == "W" else timedelta(days=30)

    for step in range(1, forecast_horizon + 1):
        cur_date += delta
        # construct lag features
        l1 = cur_history[-1]
        l2 = cur_history[-2] if len(cur_history) >= 2 else l1
        l7_idx = 7 if len(clean_series) > 30 else 3
        l7 = cur_history[-l7_idx] if len(cur_history) >= l7_idx else l1
        r3 = float(np.mean(cur_history[-3:]))

        row_feat = np.array([[
            cur_date.weekday(),
            cur_date.day,
            cur_date.month,
            l1,
            l2,
            l7,
            r3
        ]])

        if best_estimator is not None:
            pred_val = float(best_estimator.predict(row_feat)[0])
        else:
            pred_val = float(l1)

        # Ensure sensible bounds (non-negative if historical is non-negative)
        if np.all(y_train >= 0):
            pred_val = max(0.0, pred_val)

        # 95% Confidence Interval based on validation residual distribution (+- 1.96 * residual_std)
        ci_spread = 1.96 * residual_std * (1 + 0.05 * step) # interval widens as we look further ahead
        lower_bound = max(0.0 if np.all(y_train >= 0) else -np.inf, pred_val - ci_spread)
        upper_bound = pred_val + ci_spread

        future_forecasts.append({
            "step": step,
            "date": cur_date.strftime("%Y-%m-%d"),
            "forecast": round(pred_val, 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "is_estimate": True
        })
        cur_history.append(pred_val)

    # Historical curve points for visualization (last 30)
    historical_points = [
        {"date": r[date_col].strftime("%Y-%m-%d"), "actual": round(float(r['target']), 2)}
        for _, r in clean_series.tail(40).iterrows()
    ]

    return {
        "status": "success",
        "best_model": best_model_name,
        "validation_strategy": "Chronological (80% Train, 20% Holdout Test)",
        "train_period": f"{train_data[date_col].min().strftime('%Y-%m-%d')} to {train_data[date_col].max().strftime('%Y-%m-%d')}",
        "test_period": f"{test_data[date_col].min().strftime('%Y-%m-%d')} to {test_data[date_col].max().strftime('%Y-%m-%d')}",
        "model_comparison": comparison_table,
        "selected_model_metrics": next(m for m in comparison_table if m["model"] == best_model_name),
        "residual_std": round(residual_std, 4),
        "historical_series": historical_points,
        "forecast_horizon_periods": forecast_horizon,
        "future_predictions": future_forecasts,
        "uncertainty_note": "Intervals represent estimated 95% confidence bounds calculated from chronological validation residuals. These are empirical estimates, not guaranteed outcomes."
    }
