"""
Weather Service
Integration with weather APIs for spray timing and disease forecasting
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List


def get_spray_windows(latitude: float, longitude: float, days_ahead: int = 5) -> Dict:
    """
    Get optimal spray windows based on weather forecast

    Args:
        latitude: Field latitude
        longitude: Field longitude
        days_ahead: Number of days to forecast

    Returns:
        Spray window recommendations
    """

    # In production, integrate with Weather.gov API, OpenWeather, or similar
    # For now, return example structure

    # Example API call structure:
    # api_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    # response = requests.get(api_url)
    # forecast_url = response.json()['properties']['forecast']

    # Simulated forecast for demonstration
    forecast = []
    base_date = datetime.now(timezone.utc)

    for i in range(days_ahead):
        day = base_date + timedelta(days=i)
        forecast.append({
            "date": day.strftime("%Y-%m-%d"),
            "day_name": day.strftime("%A"),
            "high_temp": 78 + (i % 3) * 2,
            "low_temp": 58 + (i % 3) * 2,
            "wind_speed_mph": 8 + (i % 4) * 2,
            "humidity_percent": 60 + (i % 3) * 5,
            "precipitation_chance": 20 if i != 2 else 70,
            "precipitation_amount": 0.0 if i != 2 else 0.8,
            "conditions": "Partly Cloudy" if i != 2 else "Rain"
        })

    # Analyze spray windows
    spray_windows = []
    for day_forecast in forecast:
        is_good_window = _analyze_spray_conditions(day_forecast)

        spray_windows.append({
            "date": day_forecast["date"],
            "day_name": day_forecast["day_name"],
            "suitable_for_spraying": is_good_window["suitable"],
            "rating": is_good_window["rating"],
            "concerns": is_good_window["concerns"],
            "best_time": is_good_window["best_time"],
            "forecast": day_forecast
        })

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "forecast_days": days_ahead,
        "spray_windows": spray_windows,
        "recommendations": _generate_spray_recommendations(spray_windows)
    }


def _analyze_spray_conditions(day_forecast: Dict) -> Dict:
    """Analyze if conditions are suitable for spraying"""

    concerns = []
    rating = 10  # Start at perfect

    # Temperature check
    temp = day_forecast["high_temp"]
    if temp < 55:
        concerns.append("Temperature below 55°F - reduced efficacy")
        rating -= 3
    elif temp > 85:
        concerns.append("Temperature above 85°F - volatility risk")
        rating -= 2

    # Wind check
    wind = day_forecast["wind_speed_mph"]
    if wind > 10:
        concerns.append(f"Wind speed {wind} mph - drift risk")
        rating -= 4
    elif wind > 5:
        rating -= 1

    # Rain check
    if day_forecast["precipitation_chance"] > 50:
        concerns.append(f"{day_forecast['precipitation_chance']}% chance of rain - washoff risk")
        rating -= 5
    elif day_forecast["precipitation_chance"] > 30:
        concerns.append(f"{day_forecast['precipitation_chance']}% chance of rain - monitor closely")
        rating -= 2

    if day_forecast["precipitation_amount"] > 0.3:
        concerns.append(f"{day_forecast['precipitation_amount']}\" rain forecast - application may wash off")
        rating -= 4

    # Humidity check (high humidity can reduce evaporation)
    humidity = day_forecast["humidity_percent"]
    if humidity > 85:
        rating -= 1

    suitable = rating >= 5 and day_forecast["precipitation_chance"] < 50

    # Best time of day
    if temp > 80:
        best_time = "Early morning or evening to avoid heat"
    else:
        best_time = "Morning after dew dries"

    return {
        "suitable": suitable,
        "rating": max(0, min(10, rating)),
        "concerns": concerns if concerns else ["Good spray conditions"],
        "best_time": best_time
    }


def _generate_spray_recommendations(spray_windows: List[Dict]) -> List[str]:
    """Generate overall recommendations"""

    recommendations = []

    # Find best days
    suitable_days = [w for w in spray_windows if w["suitable_for_spraying"]]

    if not suitable_days:
        recommendations.append("⚠️ No ideal spray windows in next 5 days. Monitor forecast closely.")
    else:
        best_day = max(suitable_days, key=lambda x: x["rating"])
        recommendations.append(f"✓ Best window: {best_day['day_name']} ({best_day['date']}) - Rating: {best_day['rating']}/10")

    # Check for rain
    rainy_days = [w for w in spray_windows if w["forecast"]["precipitation_chance"] > 50]
    if rainy_days:
        rain_dates = ", ".join([w["day_name"] for w in rainy_days])
        recommendations.append(f"⚠️ Rain expected: {rain_dates}. Avoid spraying.")

    # Wind warnings
    windy_days = [w for w in spray_windows if w["forecast"]["wind_speed_mph"] > 10]
    if windy_days:
        recommendations.append("⚠️ High winds forecast - ensure proper nozzles and boom height")

    return recommendations


def get_growing_degree_days(latitude: float, longitude: float, start_date: datetime) -> float:
    """
    Calculate accumulated growing degree days (GDD) since start date

    Args:
        latitude: Location latitude
        longitude: Location longitude
        start_date: Starting date (e.g., planting date)

    Returns:
        Accumulated GDD (base 50°F for corn, base 50°F for soybeans)
    """

    # In production, would query historical weather data
    # For now, return estimated value

    days_elapsed = (datetime.now(timezone.utc) - start_date).days
    estimated_gdd = days_elapsed * 15  # Rough estimate: 15 GDD per day average

    return estimated_gdd


# Example usage
if __name__ == "__main__":
    # Example location (Central Iowa)
    result = get_spray_windows(
        latitude=41.8780,
        longitude=-93.0977,
        days_ahead=5
    )

    print("=== SPRAY WINDOW FORECAST ===")
    print(f"Location: {result['location']['latitude']}, {result['location']['longitude']}\n")

    for window in result["spray_windows"]:
        print(f"{window['day_name']} ({window['date']})")
        print(f"  Suitable: {'✓ Yes' if window['suitable_for_spraying'] else '✗ No'}")
        print(f"  Rating: {window['rating']}/10")
        print(f"  Temp: {window['forecast']['low_temp']}-{window['forecast']['high_temp']}°F")
        print(f"  Wind: {window['forecast']['wind_speed_mph']} mph")
        print(f"  Rain: {window['forecast']['precipitation_chance']}% ({window['forecast']['precipitation_amount']}\")")
        print(f"  Best Time: {window['best_time']}")
        if window['concerns']:
            print(f"  Concerns: {'; '.join(window['concerns'])}")
        print()

    print("RECOMMENDATIONS:")
    for rec in result["recommendations"]:
        print(f"  {rec}")
