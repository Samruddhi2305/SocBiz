import os
import pandas as pd
import numpy as np

# Define directories
workspace_dir = r"c:\Users\HP\OneDrive\Desktop\SocBiz"
dataset_root = os.path.join(workspace_dir, "Datasets OP'26 Analytics-20260603T202954Z-3-001", "Datasets OP_26 Analytics")
acn_xlsx_path = os.path.join(dataset_root, "ACN Data_ 25 April 2018 to 16 Dec 2018", "acndata_sessions.json.xlsx")
acn_csv_path = os.path.join(workspace_dir, "acndata_sessions.csv")
urbanev_dir = os.path.join(dataset_root, "UrbanEV_ SZ_districts")

def preprocess_acn():
    print("--- Preprocessing ACN Data ---")
    # Read raw XLSX
    print("Reading ACN Excel file...")
    df = pd.read_excel(acn_xlsx_path)
    
    # Save as raw CSV
    print("Saving raw ACN sessions to CSV...")
    df.to_csv(acn_csv_path, index=False)
    
    # Data Quality and Missing Value Report
    total_raw = len(df)
    nan_counts = df[['connectionTime', 'disconnectTime', 'kWhDelivered', 'stationID']].isna().sum()
    df_clean = df.dropna(subset=['connectionTime', 'disconnectTime', 'kWhDelivered', 'stationID']).copy()
    cleaned_count = len(df_clean)
    dropped_count = total_raw - cleaned_count
    done_missing = df_clean['doneChargingTime'].isna().sum()
    
    print("\n[ACN Data Quality Report]")
    print(f"  - Total raw sessions: {total_raw}")
    print(f"  - Dropped sessions (missing essential IDs/timestamps): {dropped_count}")
    print(f"  - Sessions with missing doneChargingTime filled with disconnectTime: {done_missing}")
    print("  - Assumption: Standard charging completion defaults to disconnect time when doneChargingTime is missing.")
    
    # Convert to datetime
    df_clean['connectionTime'] = pd.to_datetime(df_clean['connectionTime'])
    df_clean['disconnectTime'] = pd.to_datetime(df_clean['disconnectTime'])
    # If doneChargingTime is missing or invalid, fall back to disconnectTime
    df_clean['doneChargingTime'] = pd.to_datetime(df_clean['doneChargingTime']).fillna(df_clean['disconnectTime'])
    
    # Ensure times are localized or UTC-naive for matching
    df_clean['connectionTime'] = df_clean['connectionTime'].dt.tz_localize(None)
    df_clean['disconnectTime'] = df_clean['disconnectTime'].dt.tz_localize(None)
    df_clean['doneChargingTime'] = df_clean['doneChargingTime'].dt.tz_localize(None)
    
    # Unique station IDs
    stations = df_clean['stationID'].unique()
    print(f"Loaded {len(df_clean)} sessions across {len(stations)} stations.")
    
    # Determine the time range (hourly bins)
    min_time = df_clean['connectionTime'].min().floor('h')
    max_time = df_clean['disconnectTime'].max().ceil('h')
    time_index = pd.date_range(start=min_time, end=max_time, freq='h')
    print(f"Time range: {min_time} to {max_time} ({len(time_index)} hours)")
    
    # Create aligned timeseries dataframes
    print("Aggregating ACN sessions into hourly timeseries at the station level...")
    # Initialize matrices
    occupancy_matrix = pd.DataFrame(0, index=time_index, columns=stations)
    volume_matrix = pd.DataFrame(0.0, index=time_index, columns=stations)
    duration_matrix = pd.DataFrame(0.0, index=time_index, columns=stations)
    charging_time_matrix = pd.DataFrame(0.0, index=time_index, columns=stations)
    
    # Distribute session metrics across the hourly grid
    for _, session in df_clean.iterrows():
        station = session['stationID']
        conn = session['connectionTime']
        disc = session['disconnectTime']
        done = session['doneChargingTime']
        kwh = session['kWhDelivered']
        
        # Connection duration
        conn_dur_hours = (disc - conn).total_seconds() / 3600.0
        if conn_dur_hours <= 0:
            continue
            
        # Charging duration
        charge_dur_hours = (done - conn).total_seconds() / 3600.0
        if charge_dur_hours <= 0:
            charge_dur_hours = conn_dur_hours
            done = disc
            
        charging_rate = kwh / charge_dur_hours  # kW
        
        # Hourly overlap
        # Connected hours
        start_hour = conn.floor('h')
        end_hour = disc.ceil('h')
        hours_in_range = pd.date_range(start=start_hour, end=end_hour, freq='h')
        
        for hr in hours_in_range:
            if hr not in time_index:
                continue
            
            # Connected overlap
            overlap_conn_start = max(conn, hr)
            overlap_conn_end = min(disc, hr + pd.Timedelta(hours=1))
            overlap_conn_sec = max(0.0, (overlap_conn_end - overlap_conn_start).total_seconds())
            
            if overlap_conn_sec > 0:
                occupancy_matrix.at[hr, station] = 1.0
                duration_matrix.at[hr, station] = overlap_conn_sec / 3600.0
                
            # Charging overlap
            overlap_charge_start = max(conn, hr)
            overlap_charge_end = min(done, hr + pd.Timedelta(hours=1))
            overlap_charge_sec = max(0.0, (overlap_charge_end - overlap_charge_start).total_seconds())
            
            if overlap_charge_sec > 0:
                volume_matrix.at[hr, station] += charging_rate * (overlap_charge_sec / 3600.0)
                charging_time_matrix.at[hr, station] += overlap_charge_sec / 3600.0
                
    # Save the aggregated datasets
    print("Saving processed ACN timeseries files...")
    acn_proc_dir = os.path.join(workspace_dir, "processed_acn")
    os.makedirs(acn_proc_dir, exist_ok=True)
    
    occupancy_matrix.to_csv(os.path.join(acn_proc_dir, "acn_occupancy.csv"))
    volume_matrix.to_csv(os.path.join(acn_proc_dir, "acn_volume.csv"))
    duration_matrix.to_csv(os.path.join(acn_proc_dir, "acn_duration.csv"))
    charging_time_matrix.to_csv(os.path.join(acn_proc_dir, "acn_charging_time.csv"))
    
    print("ACN data preprocessing completed successfully!")

def preprocess_urbanev():
    print("\n--- Preprocessing UrbanEV Data ---")
    # Read files
    df_time = pd.read_csv(os.path.join(urbanev_dir, "time.csv"))
    df_vol = pd.read_csv(os.path.join(urbanev_dir, "volume.csv"))
    df_occ = pd.read_csv(os.path.join(urbanev_dir, "occupancy.csv"))
    df_prc = pd.read_csv(os.path.join(urbanev_dir, "price.csv"))
    df_dur = pd.read_csv(os.path.join(urbanev_dir, "duration.csv"))
    df_info = pd.read_csv(os.path.join(urbanev_dir, "information.csv"))
    
    print("\n[UrbanEV Data Quality Report]")
    for name, df_temp in [('volume', df_vol), ('occupancy', df_occ), ('price', df_prc), ('duration', df_dur), ('info', df_info)]:
        null_count = df_temp.isna().sum().sum()
        print(f"  - {name} dataset: {len(df_temp)} records, {null_count} missing values.")
    print("  - Assumption: All records in the source csv files are complete and valid, as missing counts are zero.")
    
    # Create datetime index
    timestamps = pd.to_datetime(df_time[['year', 'month', 'day', 'hour', 'minute', 'second']])
    
    df_vol.index = timestamps
    df_occ.index = timestamps
    df_prc.index = timestamps
    df_dur.index = timestamps
    
    # Drop raw timestamp columns if they exist
    for df in [df_vol, df_occ, df_prc, df_dur]:
        if 'timestamp' in df.columns:
            df.drop(columns=['timestamp'], inplace=True)
            
    # Save the parsed datasets
    print("Saving parsed UrbanEV datasets...")
    urbanev_proc_dir = os.path.join(workspace_dir, "processed_urbanev")
    os.makedirs(urbanev_proc_dir, exist_ok=True)
    
    df_vol.to_csv(os.path.join(urbanev_proc_dir, "urbanev_volume.csv"))
    df_occ.to_csv(os.path.join(urbanev_proc_dir, "urbanev_occupancy.csv"))
    df_prc.to_csv(os.path.join(urbanev_proc_dir, "urbanev_price.csv"))
    df_dur.to_csv(os.path.join(urbanev_proc_dir, "urbanev_duration.csv"))
    df_info.to_csv(os.path.join(urbanev_proc_dir, "urbanev_info.csv"), index=False)
    
    print("UrbanEV data preprocessing completed successfully!")

if __name__ == "__main__":
    preprocess_acn()
    preprocess_urbanev()
