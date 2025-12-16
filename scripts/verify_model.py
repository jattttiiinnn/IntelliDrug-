import pandas as pd
import pickle
import os
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

def verify():
    # Load data
    df = pd.read_csv('data/repurposing_training_data.csv')
    
    # Preprocess (same as training)
    phase_map = {'Discovery': 0, 'Phase1': 1, 'Phase2': 2, 'Phase3': 3}
    df['phase_started_encoded'] = df['phase_started'].map(phase_map)
    df['disease_category_match'] = df['disease_category_match'].astype(int)
    
    feature_cols = [
        'molecular_similarity', 
        'phase_started_encoded', 
        'disease_category_match', 
        'market_size_ratio', 
        'mechanism_strength', 
        'prior_safety_data'
    ]
    X = df[feature_cols]
    y = df['outcome']
    
    # Split (same seed)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # LoadScaler
    with open('models/repurposing_scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    X_test_scaled = scaler.transform(X_test)
    
    # Load Model
    with open('models/repurposing_predictor.pkl', 'rb') as f:
        model = pickle.load(f)
        
    # Predict
    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"Validation Accuracy: {acc}")
    
    with open('validation_metrics.txt', 'w') as f:
        f.write(f"Accuracy: {acc}\n")
        f.write(f"Model: {type(model).__name__}\n")

if __name__ == "__main__":
    verify()
