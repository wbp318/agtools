# AgTools: Farm Optimization Tools

## Overview
The Farm Optimizer module helps small farms reduce costs by optimizing fertilizer and pesticide applications through data-driven decisions. By analyzing weather patterns, soil conditions, and field layouts, it helps farmers minimize input costs while maintaining crop health.

## Quick Start
```python
from agtools.farm_optimizer import FarmOptimizer

# Initialize optimizer
optimizer = FarmOptimizer()

# Load sample weather data
optimizer.load_weather_data("data/sample_weather.csv")

# Example: Check if you should spray today
recommendations = optimizer.analyze_spray_needs("field_1")
print(recommendations['spray_needed'])
print(recommendations['reason'])
```

## Key Features

### 🌧️ Weather-Based Spray Timing
- Analyzes weather patterns to find optimal spray windows
- Prevents wasted applications before rain
- Tracks humidity for disease pressure
- Uses historical weather data to improve timing

### 🌱 Fertilizer Optimization
- Calculates precise nutrient needs
- Supports multiple crops (corn, soybeans, wheat)
- Prevents over-application of expensive inputs
- Uses soil test data for accurate recommendations

### 🚜 Field Operation Planning
- Optimizes spray patterns to minimize overlap
- Reduces wasted inputs and fuel
- Generates efficient field paths
- Accounts for equipment specifications

## Installation

```bash
# Clone the repository
git clone https://github.com/wbp318/agtools.git
cd agtools

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Required Data Formats

### Weather Data (CSV)
```csv
Date,Rainfall,Temperature,Humidity
2024-01-01,0.2,12.5,65
2024-01-02,0.0,13.2,62
```

### Soil Test Data (Dictionary)
```python
soil_data = {
    'N': 45,  # Nitrogen (ppm)
    'P': 30,  # Phosphorus (ppm)
    'K': 80   # Potassium (ppm)
}
```

## Project Structure
```
agtools/
├── src/
│   └── agtools/
│       ├── __init__.py        # Package initialization
│       └── farm_optimizer.py  # Main optimization module
├── data/
│   └── sample_weather.csv     # Example weather data
├── tests/                     # Test files
├── abstract_pest_images/      # Image data for pest detection
├── notebooks/                 # Analysis notebooks
└── requirements.txt          # Project dependencies
```

## Development Plans
- [ ] Machine learning pest detection
- [ ] Soil moisture prediction
- [ ] Yield optimization
- [ ] Weather API integration
- [ ] Mobile app interface

## Contributing
Feel free to:
- Submit bug reports
- Suggest new features
- Submit pull requests

## Contact
Created by [@wbp318](https://github.com/wbp318)

## License
MIT License - feel free to use this for your farm!