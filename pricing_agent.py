import os
import pandas as pd
import numpy as np

workspace_dir = r"c:\Users\HP\OneDrive\Desktop\SocBiz"
acn_test_path = os.path.join(workspace_dir, "acn_test_predictions.csv")
urbanev_test_path = os.path.join(workspace_dir, "urbanev_test_predictions.csv")
pricing_outcomes_path = os.path.join(workspace_dir, "pricing_outcomes.csv")

def run_pricing_simulation(df_test, dataset_name, true_elasticity=None):
    if true_elasticity is not None:
        print(f"\n--- Running Pricing Simulation for {dataset_name} (Elasticity: {true_elasticity}) ---")
    else:
        print(f"\n--- Running Pricing Simulation for {dataset_name} (Default Elasticity) ---")
    
    # Sort chronologically
    df_test['timestamp'] = pd.to_datetime(df_test['timestamp'])
    df_test.sort_values(by='timestamp', inplace=True)
    df_test.reset_index(drop=True, inplace=True)
    
    # We will simulate day-by-day learning
    df_test['date'] = df_test['timestamp'].dt.date
    unique_dates = sorted(df_test['date'].unique())
    
    # Baseline elasticity
    if true_elasticity is None:
        true_elasticity = 0.5 if dataset_name == 'ACN-Caltech' else 0.4
    
    # Initial pricing policy parameters
    p_baseline = 15.0  # ₹15/kWh fixed baseline
    p_surge = 22.0     # Initial surge price
    p_discount = 10.0  # Initial discount price
    
    # We'll collect daily metrics
    daily_results = []
    
    # Arrays to store adjusted metrics back into the main DataFrame
    df_test['applied_price'] = p_baseline
    df_test['adj_volume'] = df_test['volume']
    df_test['adj_utilization'] = df_test['utilization']
    df_test['adj_queue_proxy'] = df_test['queue_proxy']
    
    for i, dt in enumerate(unique_dates):
        # Slice data for the day
        day_mask = df_test['date'] == dt
        df_day = df_test[day_mask].copy()
        
        # Calculate prices based on predicted utilization
        # Surge when pred_util > 80%, Discount when pred_util < 30%, otherwise Baseline
        prices = np.where(df_day['pred_utilization'] >= 0.8, p_surge, 
                 np.where(df_day['pred_utilization'] <= 0.3, p_discount, p_baseline))
        
        # Calculate price change percent
        price_change_pct = (prices - p_baseline) / p_baseline
        
        # Simulate demand response based on true elasticity
        # Q_adj = Q_actual * (1 - epsilon * price_change_pct)
        # Note: if price decreases, demand increases; if price increases, demand decreases
        adj_volumes = df_day['volume'] * (1.0 - true_elasticity * price_change_pct)
        adj_volumes = np.maximum(0.0, adj_volumes)  # clip negative
        
        # Calculate adjusted utilization (proportional to volume change)
        adj_utils = df_day['utilization'] * (adj_volumes / (df_day['volume'] + 1e-9))
        adj_utils = np.minimum(1.0, adj_utils)
        
        # Calculate adjusted queue proxy
        adj_queues = np.maximum(0.0, df_day['occupancy'] * (adj_volumes / (df_day['volume'] + 1e-9)) - 0.8 * df_day['capacity']) * (adj_volumes / df_day['capacity'] + 0.1)
        
        # Write back to main dataframe
        df_test.loc[day_mask, 'applied_price'] = prices
        df_test.loc[day_mask, 'adj_volume'] = adj_volumes
        df_test.loc[day_mask, 'adj_utilization'] = adj_utils
        df_test.loc[day_mask, 'adj_queue_proxy'] = adj_queues
        
        # Calculate metrics for the day
        base_revenue = (df_day['volume'] * p_baseline).sum()
        new_revenue = (adj_volumes * prices).sum()
        revenue_gain = ((new_revenue - base_revenue) / (base_revenue + 1e-9)) * 100.0
        
        avg_base_util = df_day['utilization'].mean()
        avg_adj_util = adj_utils.mean()
        
        # Peak queue reduction (when baseline occupancy >= 80% capacity)
        peak_mask = df_day['utilization'] >= 0.8
        base_peak_queue = df_day.loc[peak_mask, 'queue_proxy'].sum()
        adj_peak_queue = adj_queues[peak_mask].sum()
        peak_queue_reduction = ((base_peak_queue - adj_peak_queue) / (base_peak_queue + 1e-9)) * 100.0
        
        # Off-peak uplift (when baseline util < 30%)
        low_demand_mask = df_day['utilization'] < 0.3
        base_low_vol = df_day.loc[low_demand_mask, 'volume'].sum()
        adj_low_vol = adj_volumes[low_demand_mask].sum()
        off_peak_uplift = ((adj_low_vol - base_low_vol) / (base_low_vol + 1e-9)) * 100.0
        
        # Empirical customer response rate (demand elasticity proxy)
        price_changed_mask = price_change_pct != 0
        if price_changed_mask.any():
            vol_pct = (adj_volumes[price_changed_mask] - df_day.loc[price_changed_mask, 'volume']) / (df_day.loc[price_changed_mask, 'volume'] + 1e-9)
            prc_pct = price_change_pct[price_changed_mask]
            emp_elast = - vol_pct / (prc_pct + 1e-9)
            customer_response_rate = emp_elast.mean()
        else:
            customer_response_rate = 0.0
            
        # Pricing efficiency: revenue per kWh delivered
        total_kwh = adj_volumes.sum()
        pricing_efficiency = new_revenue / (total_kwh + 1e-9)
        
        # Learning Agent Feedback Loop: 
        # Evaluate day's outcome and adjust pricing thresholds for the NEXT day
        old_p_surge = p_surge
        old_p_discount = p_discount
        
        # Feedback loop logic using peak queue reduction
        if revenue_gain > 0:
            if peak_queue_reduction > 10.0:  # Successfully reduced peak queue, can charge slightly more for surge
                p_surge = min(p_surge + 0.5, 25.0)
            else:  # Queue didn't reduce much, keep price high or increase slightly
                p_surge = max(p_surge - 0.2, 18.0)
        else:  # Revenue drop, pricing was too aggressive
            p_surge = max(p_surge - 0.5, 17.0)
            
        if off_peak_uplift < 5.0:  # Not enough off-peak attraction, lower the discount price (increase discount)
            p_discount = max(p_discount - 0.5, 7.0)
        else:  # Success, can raise discount price slightly to capture more margin
            p_discount = min(p_discount + 0.3, 13.0)
            
        daily_results.append({
            'Day': i + 1,
            'Date': str(dt),
            'Surge_Price': old_p_surge,
            'Discount_Price': old_p_discount,
            'Base_Revenue': base_revenue,
            'New_Revenue': new_revenue,
            'Revenue_Gain_Pct': revenue_gain,
            'Base_Util': avg_base_util,
            'Adj_Util': avg_adj_util,
            'Peak_Queue_Reduction_Pct': peak_queue_reduction,
            'Off_Peak_Uplift_Pct': off_peak_uplift,
            'Customer_Response_Rate': customer_response_rate,
            'Pricing_Efficiency': pricing_efficiency
        })
        
    df_daily = pd.DataFrame(daily_results)
    print(df_daily[['Day', 'Revenue_Gain_Pct', 'Peak_Queue_Reduction_Pct', 'Off_Peak_Uplift_Pct', 'Customer_Response_Rate', 'Pricing_Efficiency']])
    
    # Save the detailed outputs (only for standard/default run)
    if true_elasticity in [0.5, 0.4] or true_elasticity is None:
        df_test.to_csv(os.path.join(workspace_dir, f"{dataset_name.lower()}_sim_results.csv"), index=False)
    
    return df_daily

def run_sensitivity_analysis(df_acn_test, df_urbanev_test):
    print("\n=========================================================")
    print("RUNNING SENSITIVITY ANALYSIS (ROBUSTNESS CHECKS)")
    print("=========================================================")
    elasticities = [0.2, 0.5, 0.8]
    sensitivity_results = []
    
    for elasticity in elasticities:
        # ACN
        if df_acn_test is not None and not df_acn_test.empty:
            df_temp = df_acn_test.copy()
            df_daily = run_pricing_simulation(df_temp, 'ACN-Caltech', true_elasticity=elasticity)
            sensitivity_results.append({
                'Dataset': 'ACN-Caltech',
                'Elasticity': elasticity,
                'Avg_Revenue_Gain_Pct': df_daily['Revenue_Gain_Pct'].mean(),
                'Avg_Peak_Queue_Reduction_Pct': df_daily['Peak_Queue_Reduction_Pct'].mean(),
                'Avg_Off_Peak_Uplift_Pct': df_daily['Off_Peak_Uplift_Pct'].mean(),
                'Avg_Pricing_Efficiency': df_daily['Pricing_Efficiency'].mean()
            })
            
        # UrbanEV
        if df_urbanev_test is not None and not df_urbanev_test.empty:
            df_temp = df_urbanev_test.copy()
            df_daily = run_pricing_simulation(df_temp, 'UrbanEV', true_elasticity=elasticity)
            sensitivity_results.append({
                'Dataset': 'UrbanEV',
                'Elasticity': elasticity,
                'Avg_Revenue_Gain_Pct': df_daily['Revenue_Gain_Pct'].mean(),
                'Avg_Peak_Queue_Reduction_Pct': df_daily['Peak_Queue_Reduction_Pct'].mean(),
                'Avg_Off_Peak_Uplift_Pct': df_daily['Off_Peak_Uplift_Pct'].mean(),
                'Avg_Pricing_Efficiency': df_daily['Pricing_Efficiency'].mean()
            })
            
    df_sens = pd.DataFrame(sensitivity_results)
    df_sens.to_csv(os.path.join(workspace_dir, "pricing_robustness_checks.csv"), index=False)
    print(f"Sensitivity analysis results successfully saved to {os.path.join(workspace_dir, 'pricing_robustness_checks.csv')}!")

if __name__ == "__main__":
    df_acn_test = pd.DataFrame()
    df_urbanev_test = pd.DataFrame()
    
    # Simulate for ACN
    if os.path.exists(acn_test_path):
        df_acn_test = pd.read_csv(acn_test_path)
        acn_daily = run_pricing_simulation(df_acn_test, 'ACN-Caltech')
        acn_daily['Dataset'] = 'ACN-Caltech'
    else:
        acn_daily = pd.DataFrame()
        print("ACN test predictions file missing!")
        
    # Simulate for UrbanEV
    if os.path.exists(urbanev_test_path):
        df_urbanev_test = pd.read_csv(urbanev_test_path)
        urbanev_daily = run_pricing_simulation(df_urbanev_test, 'UrbanEV')
        urbanev_daily['Dataset'] = 'UrbanEV'
    else:
        urbanev_daily = pd.DataFrame()
        print("UrbanEV test predictions file missing!")
        
    # Combine results and save
    if not acn_daily.empty or not urbanev_daily.empty:
        df_all = pd.concat([acn_daily, urbanev_daily], ignore_index=True)
        # Reorder columns to place Dataset first
        cols = ['Dataset'] + [c for c in df_all.columns if c != 'Dataset']
        df_all = df_all[cols]
        df_all.to_csv(pricing_outcomes_path, index=False)
        print(f"\nAll simulation results saved to {pricing_outcomes_path}!")
        
        # Run sensitivity analysis (Robustness Checks)
        run_sensitivity_analysis(df_acn_test, df_urbanev_test)
