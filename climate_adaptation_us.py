import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

def create_and_fit_encoders(data):
    encoders = {}
    for column in ['soil_type', 'current_crop']:
        le = LabelEncoder()
        le.fit(data[column].unique())
        encoders[column] = le
    return encoders

def climate_adaptation_model(data, encoders):
    X = data[['temperature', 'rainfall', 'soil_type', 'current_crop']].copy()
    y = data['recommended_adaptation']
    
    for column, encoder in encoders.items():
        X[column] = encoder.transform(X[column])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    print("Model Evaluation:")
    print(classification_report(y_test, y_pred))
    
    return model

def generate_sample_data(n_samples=1000):
    np.random.seed(42)
    data = pd.DataFrame({
        'temperature': np.random.uniform(60, 100, n_samples),  # Fahrenheit
        'rainfall': np.random.uniform(20, 60, n_samples),  # Inches
        'soil_type': np.random.choice(['clay', 'loam', 'sandy'], n_samples),
        'current_crop': np.random.choice(['corn', 'wheat', 'rice', 'soybean'], n_samples)
    })
    
    conditions = [
        (data['temperature'] > 86) & (data['rainfall'] < 31),  # Hot and dry
        (data['temperature'] < 68) & (data['rainfall'] > 47)   # Cool and wet
    ]
    choices = ['drought_resistant_crop', 'flood_resistant_crop']
    data['recommended_adaptation'] = np.select(conditions, choices, default='normal_crop')
    
    return data

if __name__ == "__main__":
    climate_data = generate_sample_data()
    print("Sample of generated data:")
    print(climate_data.head())
    
    encoders = create_and_fit_encoders(climate_data)
    
    print("\nTraining the model...")
    adaptation_model = climate_adaptation_model(climate_data, encoders)
    
    new_data = pd.DataFrame({
        'temperature': [77, 90],  # Fahrenheit
        'rainfall': [39, 28],     # Inches
        'soil_type': ['clay', 'sandy'],
        'current_crop': ['corn', 'wheat']
    })
    
    for column, encoder in encoders.items():
        new_data[column] = encoder.transform(new_data[column])
    
    recommendations = adaptation_model.predict(new_data)
    print("\nRecommendations for new data:")
    for i, rec in enumerate(recommendations):
        print(f"Scenario {i+1}: Recommended adaptation strategy: {rec}")

    # Feature importance
    feature_importance = adaptation_model.feature_importances_
    features = ['temperature', 'rainfall', 'soil_type', 'current_crop']
    for feature, importance in zip(features, feature_importance):
        print(f"{feature}: {importance}")