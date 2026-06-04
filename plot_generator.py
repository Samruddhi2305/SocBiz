import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

workspace_dir = r"c:\Users\HP\OneDrive\Desktop\SocBiz"
acn_proc_dir = os.path.join(workspace_dir, "processed_acn")
urbanev_proc_dir = os.path.join(workspace_dir, "processed_urbanev")
plots_dir = os.path.join(workspace_dir, "plots")
os.makedirs(plots_dir, exist_ok=True)

# Set visual style to match premium dark presentation deck
plt.style.use('dark_background')
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16,
    'figure.facecolor': '#121919',
    'axes.facecolor': '#1E2828',
    'axes.grid': True,
    'grid.color': '#2C3A3A',
    'grid.linestyle': '--',
    'grid.linewidth': 0.5,
    'text.color': '#FFFFFF',
    'axes.labelcolor': '#FFFFFF',
    'xtick.color': '#B4BEBE',
    'ytick.color': '#B4BEBE'
})

def generate_eda_plots():
    print("--- Generating EDA Plots ---")
    
    # 1. ACN EDA
    print("Plotting ACN EDA...")
    occ_acn = pd.read_csv(os.path.join(acn_proc_dir, "acn_occupancy.csv"), parse_dates=['Unnamed: 0']).rename(columns={'Unnamed: 0': 'timestamp'})
    vol_acn = pd.read_csv(os.path.join(acn_proc_dir, "acn_volume.csv"), parse_dates=['Unnamed: 0']).rename(columns={'Unnamed: 0': 'timestamp'})
    
    # Calculate average hourly volume across all stations
    vol_acn['hour'] = vol_acn['timestamp'].dt.hour
    vol_acn['dayofweek'] = vol_acn['timestamp'].dt.day_name()
    vol_acn['is_weekend'] = vol_acn['timestamp'].dt.dayofweek.isin([5, 6])
    
    stations = [c for c in vol_acn.columns if c not in ['timestamp', 'hour', 'dayofweek', 'is_weekend']]
    vol_acn['total_volume'] = vol_acn[stations].sum(axis=1)
    
    hourly_acn = vol_acn.groupby(['hour', 'is_weekend'])['total_volume'].mean().reset_index()
    
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=hourly_acn, x='hour', y='total_volume', hue='is_weekend', style='is_weekend', palette='Set1', linewidth=2.5)
    plt.title("ACN Caltech Network: Average Hourly Charging Load (kW)", pad=15)
    plt.xlabel("Hour of Day")
    plt.ylabel("Total Charging Volume (kWh / hour)")
    plt.xticks(range(0, 24))
    plt.legend(title="Is Weekend?", labels=["Weekday", "Weekend"])
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "eda_acn_demand.png"), dpi=150)
    plt.close()
    
    # 2. UrbanEV EDA (CBD vs Non-CBD)
    print("Plotting UrbanEV EDA...")
    vol_uev = pd.read_csv(os.path.join(urbanev_proc_dir, "urbanev_volume.csv"), index_col=0, parse_dates=True)
    df_info = pd.read_csv(os.path.join(urbanev_proc_dir, "urbanev_info.csv"))
    
    vol_uev.index.name = 'timestamp'
    vol_uev_h = vol_uev.resample('h').sum()
    vol_uev_h['hour'] = vol_uev_h.index.hour
    
    cbd_grids = df_info[df_info['CBD'] == 1]['grid'].astype(str).tolist()
    non_cbd_grids = df_info[df_info['CBD'] == 0]['grid'].astype(str).tolist()
    
    # Clean lists to only include columns that exist in the dataframe
    cbd_grids = [g for g in cbd_grids if g in vol_uev_h.columns]
    non_cbd_grids = [g for g in non_cbd_grids if g in vol_uev_h.columns]
    
    vol_uev_h['cbd_avg'] = vol_uev_h[cbd_grids].mean(axis=1)
    vol_uev_h['non_cbd_avg'] = vol_uev_h[non_cbd_grids].mean(axis=1)
    
    hourly_uev = vol_uev_h.groupby('hour')[['cbd_avg', 'non_cbd_avg']].mean().reset_index()
    
    plt.figure(figsize=(10, 5))
    plt.plot(hourly_uev['hour'], hourly_uev['cbd_avg'], label='CBD Grids', color='darkorange', linewidth=2.5, marker='o')
    plt.plot(hourly_uev['hour'], hourly_uev['non_cbd_avg'], label='Non-CBD Grids', color='teal', linewidth=2.5, marker='s')
    plt.title("UrbanEV Shenzhen: Average Charging Demand Profile by Grid Type", pad=15)
    plt.xlabel("Hour of Day")
    plt.ylabel("Average Volume per Grid (kWh / hour)")
    plt.xticks(range(0, 24))
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "eda_urbanev_demand.png"), dpi=150)
    plt.close()

def generate_prediction_plots():
    print("--- Generating Model Prediction Plots ---")
    
    # 1. ACN Predictions
    acn_pred = pd.read_csv(os.path.join(workspace_dir, "acn_test_predictions.csv"), parse_dates=['timestamp'])
    acn_pred_station = acn_pred[acn_pred['station_id'] == acn_pred['station_id'].iloc[0]].head(72)  # 3 days
    
    plt.figure(figsize=(12, 5))
    plt.plot(acn_pred_station['timestamp'], acn_pred_station['volume'], label='Actual Volume', color='blue', alpha=0.7, linewidth=2)
    plt.plot(acn_pred_station['timestamp'], acn_pred_station['pred_volume'], label='Predicted Volume (Random Forest)', color='red', linestyle='--', linewidth=2)
    plt.title(f"ACN Station {acn_pred_station['station_id'].iloc[0]}: 3-Day Actual vs. Predicted Demand (kWh)", pad=15)
    plt.xlabel("Timeline")
    plt.ylabel("Volume (kWh)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "model_predictions_acn.png"), dpi=150)
    plt.close()
    
    # 2. UrbanEV Predictions
    uev_pred = pd.read_csv(os.path.join(workspace_dir, "urbanev_test_predictions.csv"), parse_dates=['timestamp'])
    uev_pred_grid = uev_pred[uev_pred['grid_id'] == uev_pred['grid_id'].iloc[0]].head(72)  # 3 days
    
    plt.figure(figsize=(12, 5))
    plt.plot(uev_pred_grid['timestamp'], uev_pred_grid['volume'], label='Actual Volume', color='teal', alpha=0.7, linewidth=2)
    plt.plot(uev_pred_grid['timestamp'], uev_pred_grid['pred_volume'], label='Predicted Volume (Random Forest)', color='magenta', linestyle='--', linewidth=2)
    plt.title(f"UrbanEV Grid {uev_pred_grid['grid_id'].iloc[0]}: 3-Day Actual vs. Predicted Demand (kWh)", pad=15)
    plt.xlabel("Timeline")
    plt.ylabel("Volume (kWh)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "model_predictions_urbanev.png"), dpi=150)
    plt.close()

def generate_pricing_plots():
    print("--- Generating Pricing & Feedback Loop Plots ---")
    df_outcomes = pd.read_csv(os.path.join(workspace_dir, "pricing_outcomes.csv"))
    
    # 1. Revenue Gain plot
    plt.figure(figsize=(10, 5))
    sns.barplot(data=df_outcomes, x='Day', y='Revenue_Gain_Pct', hue='Dataset', palette='Dark2')
    plt.title("Daily Revenue Gain (%) with Agentic Dynamic Pricing vs. Fixed Baseline", pad=15)
    plt.xlabel("Simulation Day")
    plt.ylabel("Revenue Gain (%)")
    plt.axhline(0, color='black', linewidth=1)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "pricing_outcomes_revenue.png"), dpi=150)
    plt.close()
    
    # 2. Queue Reduction and Off-Peak Uplift
    plt.figure(figsize=(10, 5))
    acn_df = df_outcomes[df_outcomes['Dataset'] == 'ACN-Caltech']
    uev_df = df_outcomes[df_outcomes['Dataset'] == 'UrbanEV']
    
    plt.plot(acn_df['Day'], acn_df['Peak_Queue_Reduction_Pct'], label='ACN Peak Queue Reduction (%)', color='#00CC88', marker='o', linewidth=2)
    plt.plot(uev_df['Day'], uev_df['Peak_Queue_Reduction_Pct'], label='UrbanEV Peak Queue Reduction (%)', color='#FF6E00', marker='^', linewidth=2)
    plt.plot(uev_df['Day'], uev_df['Off_Peak_Uplift_Pct'], label='UrbanEV Off-Peak Uplift (%)', color='#00AAFF', marker='s', linewidth=2)
    plt.title("Grid Congestion & Shift in Demand Patterns", pad=15)
    plt.xlabel("Simulation Day")
    plt.ylabel("Percentage Change (%)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "pricing_outcomes_grid_metrics.png"), dpi=150)
    plt.close()
    
    # 3. Surge Price Adjustment over time (Feedback loop)
    plt.figure(figsize=(10, 5))
    plt.step(acn_df['Day'], acn_df['Surge_Price'], label='ACN Surge Price (₹/kWh)', color='red', where='post', linewidth=2)
    plt.step(uev_df['Day'], uev_df['Surge_Price'], label='UrbanEV Surge Price (₹/kWh)', color='magenta', where='post', linewidth=2)
    plt.title("Monitoring & Learning Agent: Surge Price Adaptive Adjustments", pad=15)
    plt.xlabel("Simulation Day")
    plt.ylabel("Price (₹/kWh)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "pricing_feedback_loop.png"), dpi=150)
    plt.close()

def generate_sensitivity_plots():
    print("--- Generating Sensitivity & Robustness Plots ---")
    df_sens = pd.read_csv(os.path.join(workspace_dir, "pricing_robustness_checks.csv"))
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor('#121919')
    
    # 1. Revenue Gain
    sns.lineplot(ax=axes[0], data=df_sens, x='Elasticity', y='Avg_Revenue_Gain_Pct', hue='Dataset', marker='o', linewidth=2.5, palette=['#00CC88', '#FF6E00'])
    axes[0].set_facecolor('#1E2828')
    axes[0].set_title("Revenue Gain vs. Customer Elasticity", pad=10)
    axes[0].set_xlabel("Price Elasticity")
    axes[0].set_ylabel("Average Daily Revenue Gain (%)")
    axes[0].set_xticks([0.2, 0.5, 0.8])
    
    # 2. Peak Queue Reduction
    sns.lineplot(ax=axes[1], data=df_sens, x='Elasticity', y='Avg_Peak_Queue_Reduction_Pct', hue='Dataset', marker='s', linewidth=2.5, palette=['#00CC88', '#FF6E00'])
    axes[1].set_facecolor('#1E2828')
    axes[1].set_title("Peak Queue Reduction vs. Elasticity", pad=10)
    axes[1].set_xlabel("Price Elasticity")
    axes[1].set_ylabel("Average Peak Queue Reduction (%)")
    axes[1].set_xticks([0.2, 0.5, 0.8])
    
    plt.suptitle("Sensitivity Analysis & Robustness Checks", y=0.98)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "pricing_sensitivity_analysis.png"), dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("Sensitivity analysis plot successfully generated!")

if __name__ == "__main__":
    generate_eda_plots()
    generate_prediction_plots()
    generate_pricing_plots()
    if os.path.exists(os.path.join(workspace_dir, "pricing_robustness_checks.csv")):
        generate_sensitivity_plots()
    print("All analytical plots successfully generated and saved!")
