import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, roc_auc_score

workspace_dir = r"c:\Users\HP\OneDrive\Desktop\SocBiz"
acn_proc_dir = os.path.join(workspace_dir, "processed_acn")
urbanev_proc_dir = os.path.join(workspace_dir, "processed_urbanev")

# We will save model outputs here
output_metrics_path = os.path.join(workspace_dir, "demand_prediction_metrics.csv")

def feature_engineering_acn():
    print("--- Feature Engineering for ACN ---")
    occ = pd.read_csv(os.path.join(acn_proc_dir, "acn_occupancy.csv"), parse_dates=['Unnamed: 0']).rename(columns={'Unnamed: 0': 'timestamp'})
    vol = pd.read_csv(os.path.join(acn_proc_dir, "acn_volume.csv"), parse_dates=['Unnamed: 0']).rename(columns={'Unnamed: 0': 'timestamp'})
    dur = pd.read_csv(os.path.join(acn_proc_dir, "acn_duration.csv"), parse_dates=['Unnamed: 0']).rename(columns={'Unnamed: 0': 'timestamp'})
    chg = pd.read_csv(os.path.join(acn_proc_dir, "acn_charging_time.csv"), parse_dates=['Unnamed: 0']).rename(columns={'Unnamed: 0': 'timestamp'})
    
    # Melt dataframes to long format
    stations = [c for c in occ.columns if c != 'timestamp']
    
    melted_list = []
    for station in stations:
        df_st = pd.DataFrame({
            'timestamp': occ['timestamp'],
            'station_id': station,
            'occupancy': occ[station],
            'volume': vol[station],
            'duration': dur[station],
            'charging_time': chg[station]
        })
        melted_list.append(df_st)
    
    df_long = pd.concat(melted_list, ignore_index=True)
    
    # Sort by station and time
    df_long.sort_values(by=['station_id', 'timestamp'], inplace=True)
    df_long.reset_index(drop=True, inplace=True)
    
    # Engineer temporal features
    df_long['hour'] = df_long['timestamp'].dt.hour
    df_long['dayofweek'] = df_long['timestamp'].dt.dayofweek
    df_long['is_weekend'] = df_long['dayofweek'].isin([5, 6]).astype(int)
    df_long['month'] = df_long['timestamp'].dt.month
    
    # Capacity is 1 for each ACN station
    df_long['capacity'] = 1.0
    # True Charger Utilization Rate: Charging Time / Total Available Time
    # Total available time in 1 hour is 1.0 hours per station
    df_long['utilization'] = df_long['charging_time'] / df_long['capacity']
    df_long['utilization'] = df_long['utilization'].clip(upper=1.0)
    
    # Site-wide Occupancy Density: Average occupied stations across all 54 stations at each hour
    site_occ = occ.set_index('timestamp')[stations].mean(axis=1).reset_index().rename(columns={0: 'occupancy_density'})
    df_long = df_long.merge(site_occ, on='timestamp', how='left')
    
    # Lag features
    df_long['vol_lag1'] = df_long.groupby('station_id')['volume'].shift(1)
    df_long['vol_lag2'] = df_long.groupby('station_id')['volume'].shift(2)
    df_long['vol_lag24'] = df_long.groupby('station_id')['volume'].shift(24)
    df_long['util_lag1'] = df_long.groupby('station_id')['utilization'].shift(1)
    
    # Electricity Procurement Cost: Time-of-Use tariff
    # Off-peak: 0-8h (₹6/kWh), Peak: 18-22h (₹12/kWh), Shoulder: rest (₹9/kWh)
    conditions = [
        (df_long['hour'] >= 0) & (df_long['hour'] < 8),
        (df_long['hour'] >= 18) & (df_long['hour'] < 22)
    ]
    choices = [6.0, 12.0]
    df_long['procurement_cost_per_kwh'] = np.select(conditions, choices, default=9.0)
    
    # Queue length proxy: For a single station, if utilization is 1 (occupied) and volume > 0, 
    # we proxy the queue probability or wait time
    df_long['queue_proxy'] = (df_long['utilization'] * df_long['volume'] * 0.2).clip(lower=0)
    
    # Drop rows with NaN due to lags
    df_long.dropna(subset=['vol_lag1', 'vol_lag2', 'vol_lag24', 'util_lag1'], inplace=True)
    
    print(f"ACN dataset long shape: {df_long.shape}")
    return df_long

def feature_engineering_urbanev():
    print("--- Feature Engineering for UrbanEV ---")
    vol_5m = pd.read_csv(os.path.join(urbanev_proc_dir, "urbanev_volume.csv"), index_col=0, parse_dates=True)
    occ_5m = pd.read_csv(os.path.join(urbanev_proc_dir, "urbanev_occupancy.csv"), index_col=0, parse_dates=True)
    prc_5m = pd.read_csv(os.path.join(urbanev_proc_dir, "urbanev_price.csv"), index_col=0, parse_dates=True)
    dur_5m = pd.read_csv(os.path.join(urbanev_proc_dir, "urbanev_duration.csv"), index_col=0, parse_dates=True)
    for df_temp in [vol_5m, occ_5m, prc_5m, dur_5m]:
        df_temp.index.name = 'timestamp'
    df_info = pd.read_csv(os.path.join(urbanev_proc_dir, "urbanev_info.csv"))
    
    # Aggregate 5-minute data to Hourly data to align and make models efficient
    print("Aggregating UrbanEV from 5-minute to hourly intervals...")
    vol_h = vol_5m.resample('h').sum()
    occ_h = occ_5m.resample('h').mean()
    prc_h = prc_5m.resample('h').mean()
    dur_h = dur_5m.resample('h').mean()
    
    grids = [c for c in vol_h.columns if c != 'timestamp']
    
    melted_list = []
    for grid in grids:
        df_grid = pd.DataFrame({
            'timestamp': vol_h.index,
            'grid_id': int(grid),
            'volume': vol_h[grid],
            'occupancy': occ_h[grid],
            'price': prc_h[grid],
            'duration': dur_h[grid]
        })
        melted_list.append(df_grid)
        
    df_long = pd.concat(melted_list, ignore_index=True)
    
    # Merge static grid information
    df_long = df_long.merge(df_info, left_on='grid_id', right_on='grid', how='left')
    
    # Sort and reset index
    df_long.sort_values(by=['grid_id', 'timestamp'], inplace=True)
    df_long.reset_index(drop=True, inplace=True)
    
    # Engineer temporal features
    df_long['hour'] = df_long['timestamp'].dt.hour
    df_long['dayofweek'] = df_long['timestamp'].dt.dayofweek
    df_long['is_weekend'] = df_long['dayofweek'].isin([5, 6]).astype(int)
    df_long['month'] = df_long['timestamp'].dt.month
    
    # Utilization Rate (occupancy / count)
    df_long['capacity'] = df_long['count']
    # Avoid division by zero
    df_long['capacity'] = df_long['capacity'].replace(0, 1)
    df_long['utilization'] = df_long['occupancy'] / df_long['capacity']
    df_long['utilization'] = df_long['utilization'].clip(upper=1.0)
    
    # Occupancy and Charger Density
    # Avoid division by zero for area
    df_long['area'] = df_long['area'].replace(0, 1)
    df_long['occupancy_density'] = df_long['occupancy'] / df_long['area']
    df_long['charger_density'] = df_long['capacity'] / df_long['area']
    
    # Lag features (hourly lags)
    df_long['vol_lag1'] = df_long.groupby('grid_id')['volume'].shift(1)
    df_long['vol_lag2'] = df_long.groupby('grid_id')['volume'].shift(2)
    df_long['vol_lag24'] = df_long.groupby('grid_id')['volume'].shift(24)
    df_long['util_lag1'] = df_long.groupby('grid_id')['utilization'].shift(1)
    
    # Electricity Procurement Cost: Time-of-Use tariff
    conditions = [
        (df_long['hour'] >= 0) & (df_long['hour'] < 8),
        (df_long['hour'] >= 18) & (df_long['hour'] < 22)
    ]
    choices = [6.0, 12.0]
    df_long['procurement_cost_per_kwh'] = np.select(conditions, choices, default=9.0)
    
    # Queue length proxy: when occupancy exceeds 80% capacity
    df_long['queue_proxy'] = np.maximum(0, df_long['occupancy'] - 0.8 * df_long['capacity']) * (df_long['volume'] / df_long['capacity'] + 0.1)
    
    # Drop rows with NaN due to lags
    df_long.dropna(subset=['vol_lag1', 'vol_lag2', 'vol_lag24', 'util_lag1'], inplace=True)
    
    print(f"UrbanEV dataset long shape: {df_long.shape}")
    return df_long

def train_and_evaluate(df_long, dataset_name, id_col):
    print(f"\n--- Training Demand Prediction Agent on {dataset_name} ---")
    
    # Sort chronologically to prevent leakage
    df_long = df_long.sort_values(by='timestamp').reset_index(drop=True)
    
    # Chronological split: 80% train, 20% test
    n_records = len(df_long)
    split_idx = int(n_records * 0.8)
    
    # Define features and targets
    features = ['hour', 'dayofweek', 'is_weekend', 'vol_lag1', 'vol_lag2', 'vol_lag24', 'util_lag1', 'occupancy_density']
    if dataset_name == 'UrbanEV':
        # Add spatial features
        features += ['fast_count', 'slow_count', 'lon', 'la', 'CBD', 'charger_density']
        
    target_vol = 'volume'
    target_util = 'utilization'
    
    # Target for congestion: utilization > 80%
    df_long['congestion'] = (df_long['utilization'] >= 0.8).astype(int)
    target_cong = 'congestion'
    
    X_train = df_long.loc[:split_idx, features]
    y_train_vol = df_long.loc[:split_idx, target_vol]
    y_train_util = df_long.loc[:split_idx, target_util]
    y_train_cong = df_long.loc[:split_idx, target_cong]
    
    X_test = df_long.loc[split_idx:, features]
    y_test_vol = df_long.loc[split_idx:, target_vol]
    y_test_util = df_long.loc[split_idx:, target_util]
    y_test_cong = df_long.loc[split_idx:, target_cong]
    
    print(f"Train samples: {len(X_train)} | Test samples: {len(X_test)}")
    
    # 1. Predict volume
    print("Training Volume Regressor (Random Forest)...")
    model_vol = RandomForestRegressor(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1)
    model_vol.fit(X_train, y_train_vol)
    preds_vol = model_vol.predict(X_test)
    
    rmse_vol = np.sqrt(mean_squared_error(y_test_vol, preds_vol))
    mae_vol = mean_absolute_error(y_test_vol, preds_vol)
    r2_vol = r2_score(y_test_vol, preds_vol)
    
    # 2. Predict utilization
    print("Training Utilization Regressor (Random Forest)...")
    model_util = RandomForestRegressor(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1)
    model_util.fit(X_train, y_train_util)
    preds_util = model_util.predict(X_test)
    
    rmse_util = np.sqrt(mean_squared_error(y_test_util, preds_util))
    mae_util = mean_absolute_error(y_test_util, preds_util)
    r2_util = r2_score(y_test_util, preds_util)
    
    # 3. Predict Congestion Probability (utilization > 80%)
    print("Training Congestion Classifier (Random Forest)...")
    model_cong = RandomForestClassifier(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1)
    model_cong.fit(X_train, y_train_cong)
    preds_cong_prob = model_cong.predict_proba(X_test)[:, 1]
    preds_cong = (preds_cong_prob >= 0.5).astype(int)
    
    acc_cong = accuracy_score(y_test_cong, preds_cong)
    try:
        auc_cong = roc_auc_score(y_test_cong, preds_cong_prob)
    except:
        auc_cong = 0.5
        
    print(f"Volume Regressor   | RMSE: {rmse_vol:.4f} | MAE: {mae_vol:.4f} | R2: {r2_vol:.4f}")
    print(f"Util Regressor     | RMSE: {rmse_util:.4f} | MAE: {mae_util:.4f} | R2: {r2_util:.4f}")
    print(f"Congestion Classif | Accuracy: {acc_cong:.4f} | AUC: {auc_cong:.4f}")
    
    # Save the testing dataset with predictions for pricing simulation
    df_test_out = df_long.loc[split_idx:].copy()
    df_test_out['pred_volume'] = preds_vol
    df_test_out['pred_utilization'] = preds_util
    df_test_out['pred_congestion_prob'] = preds_cong_prob
    
    # Get feature importances
    importances = pd.DataFrame({
        'Feature': features,
        'Importance_Volume': model_vol.feature_importances_,
        'Importance_Util': model_util.feature_importances_
    })
    print("Feature Importances:")
    print(importances.sort_values(by='Importance_Volume', ascending=False).head(5))
    
    metrics = {
        'Dataset': dataset_name,
        'Volume_RMSE': rmse_vol,
        'Volume_MAE': mae_vol,
        'Volume_R2': r2_vol,
        'Util_RMSE': rmse_util,
        'Util_MAE': mae_util,
        'Util_R2': r2_util,
        'Congestion_Accuracy': acc_cong,
        'Congestion_AUC': auc_cong
    }
    
    return metrics, df_test_out, importances

if __name__ == "__main__":
    # Process ACN
    df_acn_long = feature_engineering_acn()
    acn_metrics, df_acn_test_out, acn_importances = train_and_evaluate(df_acn_long, 'ACN-Caltech', 'station_id')
    
    # Process UrbanEV
    df_urbanev_long = feature_engineering_urbanev()
    urbanev_metrics, df_urbanev_test_out, urbanev_importances = train_and_evaluate(df_urbanev_long, 'UrbanEV', 'grid_id')
    
    # Save metrics
    df_metrics = pd.DataFrame([acn_metrics, urbanev_metrics])
    df_metrics.to_csv(output_metrics_path, index=False)
    print(f"\nAll metrics successfully saved to {output_metrics_path}!")
    
    # Save the test data with predictions for the pricing simulation step
    df_acn_test_out.to_csv(os.path.join(workspace_dir, "acn_test_predictions.csv"), index=False)
    df_urbanev_test_out.to_csv(os.path.join(workspace_dir, "urbanev_test_predictions.csv"), index=False)
    print("Predictions saved for pricing simulation.")
