import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import math

class FarmOptimizer:
    def __init__(self):
        self.weather_data = pd.DataFrame()
        self.soil_data = pd.DataFrame()
        self.spray_history = pd.DataFrame()
        
    def load_weather_data(self, filepath: str) -> None:
        """
        Load weather data (rainfall, temperature, humidity)
        Expected format: Date, Rainfall(mm), Temperature(C), Humidity(%)
        """
        self.weather_data = pd.read_csv(filepath)
        self.weather_data['Date'] = pd.to_datetime(self.weather_data['Date'])
        
    def analyze_spray_needs(self, field_id: str) -> Dict:
        """
        Analyze optimal spraying schedule based on weather conditions
        Returns recommendations for next spray date
        """
        # Get recent weather patterns
        recent_weather = self.weather_data.tail(7)
        
        # Basic rules for spray recommendations
        rain_expected = recent_weather['Rainfall'].mean() > 5  # mm
        humid_conditions = recent_weather['Humidity'].mean() > 75  # %
        
        recommendations = {
            'spray_needed': False,
            'optimal_time': None,
            'reason': []
        }
        
        if rain_expected:
            recommendations['reason'].append("Delay spraying due to rain forecast")
        if humid_conditions:
            recommendations['spray_needed'] = True
            recommendations['reason'].append("Higher disease pressure due to humidity")
            
        return recommendations
    
    def optimize_fertilizer_usage(self, 
                                soil_nutrients: Dict[str, float],
                                crop_type: str) -> Dict[str, float]:
        """
        Calculate optimal fertilizer amounts based on soil tests and crop needs
        """
        # Example nutrient requirements for different crops
        crop_requirements = {
            'corn': {'N': 180, 'P': 70, 'K': 150},
            'soybeans': {'N': 50, 'P': 40, 'K': 130},
            'wheat': {'N': 120, 'P': 60, 'K': 100}
        }
        
        if crop_type not in crop_requirements:
            raise ValueError(f"Crop type {crop_type} not supported")
            
        required = crop_requirements[crop_type]
        
        # Calculate deficits
        fertilizer_needs = {
            nutrient: max(0, required[nutrient] - soil_nutrients.get(nutrient, 0))
            for nutrient in required
        }
        
        return fertilizer_needs
    
    def calculate_spray_zones(self, 
                            field_dimensions: Tuple[float, float],
                            spray_width: float) -> List[Dict]:
        """
        Optimize spraying pattern to minimize overlap and missed areas
        """
        width, length = field_dimensions
        
        # Calculate number of passes needed
        passes = math.ceil(width / spray_width)
        
        # Generate optimized spray zones
        zones = []
        for i in range(passes):
            zone = {
                'pass_number': i + 1,
                'start_x': i * spray_width,
                'end_x': min((i + 1) * spray_width, width),
                'length': length
            }
            zones.append(zone)
            
        return zones
    
    def generate_report(self) -> str:
        """
        Generate summary report of optimization recommendations
        """
        report = []
        report.append("Farm Optimization Report")
        report.append("-" * 20)
        
        if not self.weather_data.empty:
            avg_temp = self.weather_data['Temperature'].mean()
            avg_rain = self.weather_data['Rainfall'].mean()
            report.append(f"Average Temperature: {avg_temp:.1f}°C")
            report.append(f"Average Rainfall: {avg_rain:.1f}mm")
            
        # Add more report sections as needed
        return "\n".join(report)

def main():
    optimizer = FarmOptimizer()
    
    # Example soil test results
    soil_data = {'N': 45, 'P': 30, 'K': 80}
    
    # Calculate fertilizer needs for corn
    fert_needs = optimizer.optimize_fertilizer_usage(soil_data, 'corn')
    
    # Calculate optimal spray zones for a 100x200m field
    spray_zones = optimizer.calculate_spray_zones((100, 200), 12)  # 12m spray width
    
    # Generate and print report
    print(optimizer.generate_report())

if __name__ == "__main__":
    main()