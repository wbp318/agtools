import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def load_and_preprocess_data(file_path):
    # Load the data
    data = pd.read_csv(file_path)
    
    # Prepare features (X) and target variable (y)
    X = data[['soil_type', 'rainfall', 'temperature', 'fertilizer_used']]
    y = data['yield']
    
    return X, y

def create_model_pipeline():
    # Create preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), ['rainfall', 'temperature', 'fertilizer_used']),
            ('cat', OneHotEncoder(drop='first'), ['soil_type'])
        ])

    # Create pipeline
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])

    return model

def train_model(X, y):
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create and train the model
    model = create_model_pipeline()
    model.fit(X_train, y_train)
    
    return model, X_test, y_test

def evaluate_model(model, X_test, y_test):
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Root Mean Squared Error: {rmse:.2f}")
    print(f"R-squared Score: {r2:.2f}")

def print_feature_importance(model, feature_names):
    # Get feature importances
    importances = model.named_steps['regressor'].feature_importances_
    
    # Get feature names after preprocessing
    feature_names = (model.named_steps['preprocessor']
                     .named_transformers_['num'].get_feature_names_out().tolist() +
                     model.named_steps['preprocessor']
                     .named_transformers_['cat'].get_feature_names_out(['soil_type']).tolist())
    
    # Sort feature importances in descending order
    indices = np.argsort(importances)[::-1]

    # Print the feature ranking
    print("Feature importance ranking:")
    for f in range(len(feature_names)):
        print("%d. %s (%f)" % (f + 1, feature_names[indices[f]], importances[indices[f]]))

def predict_yield(model, soil_type, rainfall, temperature, fertilizer_used):
    # Prepare the input data
    input_data = pd.DataFrame({
        'soil_type': [soil_type],
        'rainfall': [rainfall],
        'temperature': [temperature],
        'fertilizer_used': [fertilizer_used]
    })
    
    # Make prediction
    prediction = model.predict(input_data)
    
    return prediction[0]

def main():
    # Load and preprocess the data
    X, y = load_and_preprocess_data('crop_data.csv')
    
    # Train the model
    model, X_test, y_test = train_model(X, y)
    
    # Evaluate the model
    evaluate_model(model, X_test, y_test)
    
    # Print feature importance
    print_feature_importance(model, X.columns)
    
    # Example prediction
    soil_type = 'loam'
    rainfall = 1000
    temperature = 25
    fertilizer_used = 200
    
    predicted_yield = predict_yield(model, soil_type, rainfall, temperature, fertilizer_used)
    print(f"\nPredicted yield for {soil_type} soil with {rainfall}mm rainfall, {temperature}°C temperature, and {fertilizer_used}kg/ha fertilizer: {predicted_yield:.2f} kg/ha")

if __name__ == "__main__":
    main()