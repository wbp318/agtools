import pandas as pd
import numpy as np

def generate_sample_data(n_samples=1000):
    np.random.seed(42)  # for reproducibility
    
    data = pd.DataFrame({
        'temperature': np.random.uniform(60, 100, n_samples),  # Fahrenheit
        'rainfall': np.random.uniform(20, 60, n_samples),  # Inches
        'soil_type': np.random.choice(['clay', 'loam', 'sandy'], n_samples),
        'current_crop': np.random.choice(['corn', 'wheat', 'rice', 'soybean'], n_samples)
    })
    
    # Simple rule-based adaptation recommendation
    conditions = [
        (data['temperature'] > 86) & (data['rainfall'] < 31),  # Hot and dry
        (data['temperature'] < 68) & (data['rainfall'] > 47)   # Cool and wet
    ]
    choices = ['drought_resistant_crop', 'flood_resistant_crop']
    data['recommended_adaptation'] = np.select(conditions, choices, default='normal_crop')
    
    return data

if __name__ == "__main__":
    # Generate the data
    sample_data = generate_sample_data()
    
    # Save to CSV
    filename = 'climate_adaptation_sample_data.csv'
    sample_data.to_csv(filename, index=False)
    
    print(f"Sample data has been generated and saved to {filename}")
    print(f"Number of rows: {len(sample_data)}")
    print("\nFirst few rows of the data:")
    print(sample_data.head())

    # Print value counts for categorical variables
    print("\nDistribution of soil types:")
    print(sample_data['soil_type'].value_counts())
    print("\nDistribution of current crops:")
    print(sample_data['current_crop'].value_counts())
    print("\nDistribution of recommended adaptations:")
    print(sample_data['recommended_adaptation'].value_counts())