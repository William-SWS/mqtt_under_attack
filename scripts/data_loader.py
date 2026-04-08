import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42

def calculate_gaps(df_full):
    """
    Calculates gaps between CONNECT (type 1) and PUBLISH (type 3) messages.
    Needs 'frame.time_epoch' and 'mqtt.msgtype'.
    """
    if 'frame.time_epoch' in df_full.columns:
        df_full = df_full.sort_values('frame.time_epoch').reset_index(drop=True)
        
        df_full['publish_gap'] = 0.0
        df_full['connect_gap'] = 0.0
        
        for traffic_type in df_full['type'].unique():
            mask = df_full['type'] == traffic_type
            subset = df_full[mask].copy()
            
            if len(subset) > 1:
                timestamps = subset['frame.time_epoch'].values
                msgtypes = subset['mqtt.msgtype'].fillna(0).values
                
                # Calculate publish gaps (msgtype == 3)
                publish_indices = np.where(msgtypes == 3)[0]
                if len(publish_indices) > 1:
                    publish_times = timestamps[publish_indices]
                    publish_gaps = np.diff(publish_times)
                    for i, idx in enumerate(publish_indices[1:], 1):
                        actual_idx = subset.index[idx]
                        df_full.loc[actual_idx, 'publish_gap'] = publish_gaps[i-1]
                
                # Calculate connect gaps (msgtype == 1)
                connect_indices = np.where(msgtypes == 1)[0]
                if len(connect_indices) > 1:
                    connect_times = timestamps[connect_indices]
                    connect_gaps = np.diff(connect_times)
                    for i, idx in enumerate(connect_indices[1:], 1):
                        actual_idx = subset.index[idx]
                        df_full.loc[actual_idx, 'connect_gap'] = connect_gaps[i-1]
    return df_full

def clean_data(df):
    """
    Removes irrelevant Wireshark features.
    """
    columns_to_remove = [
        'frame.time_delta_displayed', 'frame.time_epoch', 'frame.time_invalid',
        'frame.time_relative', 'frame.coloring_rule.name', 'frame.coloring_rule.string',
        'frame.comment', 'frame.comment.expert', 'frame.encap_type', 'frame.file_off',
        'frame.ignored', 'frame.incomplete', 'frame.interface_id', 'frame.interface_name',
        'frame.link_nr', 'frame.marked', 'frame.md5_hash', 'frame.number', 'frame.offset_shift',
        'ip.src', 'ip.dst', 'eth.src', 'eth.dst', 'tcp.srcport', 'tcp.dstport',
        'mqtt.clientid', 'mqtt.conack.flags', 'mqtt.conflags', 'mqtt.dupflag', 'mqtt.hdrflags',
        'mqtt.msg', 'mqtt.msgid', 'mqtt.passwd', 'mqtt.passwd_len', 'mqtt.proto_len',
        'mqtt.protoname', 'mqtt.sub.qos', 'mqtt.suback.qos', 'mqtt.topic', 'mqtt.username',
        'mqtt.username_len', 'mqtt.ver', 'mqtt.willmsg', 'mqtt.willmsg_len', 'mqtt.willtopic',
        'mqtt.willtopic_len'
    ]
    
    existing_cols_to_remove = [col for col in columns_to_remove if col in df.columns]
    df_clean = df.drop(columns=existing_cols_to_remove)
    return df_clean

def split_and_scale(df_clean):
    """
    Fills NaNs, splits the dataset, and applies standard scaling.
    """
    X = df_clean.drop('type', axis=1)
    y = df_clean['type']
    
    # Fill NAs with 0 (assuming absence of MQTT message field)
    X = X.fillna(0)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=X.columns, index=X_train.index)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=X.columns, index=X_test.index)
    
    return X_train, X_test, X_train_scaled, X_test_scaled, y_train, y_test

def load_and_preprocess(raw_data_path):
    """
    Orchestrates the data loading and preprocessing.
    """
    print("Loading data...")
    df = pd.read_csv(raw_data_path)
    
    print("Calculating gaps...")
    df = calculate_gaps(df)
    
    print("Cleaning data...")
    df_clean = clean_data(df)
    
    print("Splitting and scaling...")
    X_train, X_test, X_train_scaled, X_test_scaled, y_train, y_test = split_and_scale(df_clean)
    
    return X_train, X_test, X_train_scaled, X_test_scaled, y_train, y_test

if __name__ == "__main__":
    # Test block
    path = '../data/raw/MQTT Under Attack Dataset/DoS.csv'
    X_train, X_test, X_train_scaled, X_test_scaled, y_train, y_test = load_and_preprocess(path)
    print("Data loading completed. Train shapes:", X_train.shape, y_train.shape)
