import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import os

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import xgboost as xgb

def load_and_preprocess_data(filepath):
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    
    # Preprocessing
    
    # 1. Encode Phase Started (Ordinal)
    phase_map = {
        'Discovery': 0,
        'Phase1': 1,
        'Phase2': 2,
        'Phase3': 3
    }
    # Handle potentially unknown phases by filling with median or mode if needed, 
    # but our dataset is clean.
    df['phase_started_encoded'] = df['phase_started'].map(phase_map)
    
    # 2. Encode Boolean
    df['disease_category_match'] = df['disease_category_match'].astype(int)
    
    # 3. Select Features and Target
    feature_cols = [
        'molecular_similarity', 
        'phase_started_encoded', 
        'disease_category_match', 
        'market_size_ratio', 
        'mechanism_strength', 
        'prior_safety_data'
    ]
    target_col = 'outcome'
    
    X = df[feature_cols]
    y = df[target_col]
    
    print(f"Features: {feature_cols}")
    print(f"Target distribution:\n{y.value_counts()}")
    
    return X, y, feature_cols

def train_and_evaluate(X, y, feature_names):
    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Models to train
    models = {
        'Logistic Regression': LogisticRegression(random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'XGBoost': xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    }
    
    best_model = None
    best_acc = 0.0
    best_model_name = ""
    
    results = {}

    print("\n--- Model Evaluation ---")
    
    for name, model in models.items():
        # Train
        model.fit(X_train_scaled, y_train)
        
        # Predict
        y_pred = model.predict(X_test_scaled)
        
        # Metrics
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        results[name] = {'Accuracy': acc, 'Precision': prec, 'Recall': rec, 'F1': f1}
        
        print(f"\n{name}:")
        print(f"  Accuracy: {acc:.4f}")
        print(f"  Precision: {prec:.4f}")
        print(f"  Recall: {rec:.4f}")
        print(f"  F1 Score: {f1:.4f}")
        
        if acc > best_acc:
            best_acc = acc
            best_model = model
            best_model_name = name
            
    print(f"\nBest Model: {best_model_name} with Accuracy: {best_acc:.4f}")
    
    # Feature Importance (for Tree methods)
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        plt.figure(figsize=(10, 6))
        plt.title(f"Feature Importances ({best_model_name})")
        plt.bar(range(X.shape[1]), importances[indices], align="center")
        plt.xticks(range(X.shape[1]), [feature_names[i] for i in indices], rotation=45)
        plt.tight_layout()
        os.makedirs('data', exist_ok=True)
        plt.savefig('data/feature_importance.png')
        print("Feature importance plot saved to data/feature_importance.png")
    
    return best_model, scaler

def save_artifacts(model, scaler):
    os.makedirs('models', exist_ok=True)
    
    with open('models/repurposing_predictor.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    with open('models/repurposing_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
        
    print("Model and scaler saved to models/")

if __name__ == "__main__":
    data_path = "data/repurposing_training_data.csv"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
    else:
        X, y, feature_names = load_and_preprocess_data(data_path)
        best_model, scaler = train_and_evaluate(X, y, feature_names)
        save_artifacts(best_model, scaler)
