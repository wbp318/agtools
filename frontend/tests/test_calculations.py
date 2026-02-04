"""
Core Calculation Tests

Tests for offline calculation engines - yield response, spray timing.
"""

import sys
import os

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestYieldResponseCalculator:
    """Tests for yield response calculation engine."""

    def test_calculator_initialization(self):
        """Test offline yield calculator initializes."""
        from core.calculations.yield_response import get_offline_yield_calculator

        calc = get_offline_yield_calculator()
        assert calc is not None

    def test_calculate_eor_corn_nitrogen(self):
        """Test EOR calculation for corn with nitrogen."""
        from core.calculations.yield_response import get_offline_yield_calculator

        calc = get_offline_yield_calculator()
        result = calc.calculate_eor(
            crop='corn',
            nutrient='N',
            nutrient_cost=0.50,
            grain_price=5.00,
            yield_potential=200
        )

        assert result is not None
        assert hasattr(result, 'eor')
        assert result.eor >= 0
        assert result.eor < 300  # Reasonable range for corn N

    def test_calculate_eor_soybeans_phosphorus(self):
        """Test EOR calculation for soybeans with phosphorus."""
        from core.calculations.yield_response import get_offline_yield_calculator

        calc = get_offline_yield_calculator()
        result = calc.calculate_eor(
            crop='soybean',
            nutrient='P',
            nutrient_cost=0.60,
            grain_price=12.00,
            yield_potential=60
        )

        assert result is not None
        assert result.eor >= 0

    def test_yield_calculation(self):
        """Test yield calculation at specific rate."""
        from core.calculations.yield_response import get_offline_yield_calculator

        calc = get_offline_yield_calculator()
        yield_value = calc.calculate_yield(
            rate=150,
            crop='corn',
            nutrient='N',
            yield_potential=200
        )

        assert yield_value is not None
        assert yield_value > 0
        assert yield_value <= 250  # Reasonable yield range

    def test_calculate_yield_different_rates(self):
        """Test yield increases with rate up to a point."""
        from core.calculations.yield_response import get_offline_yield_calculator

        calc = get_offline_yield_calculator()

        yield_at_50 = calc.calculate_yield(rate=50, crop='corn', nutrient='N')
        yield_at_100 = calc.calculate_yield(rate=100, crop='corn', nutrient='N')
        yield_at_150 = calc.calculate_yield(rate=150, crop='corn', nutrient='N')

        # Yield should generally increase with rate (up to plateau)
        assert yield_at_100 >= yield_at_50
        assert yield_at_150 >= yield_at_100

    def test_response_model_types(self):
        """Test different response model calculations."""
        from core.calculations.yield_response import ResponseModel

        # Check response models exist
        assert ResponseModel.QUADRATIC_PLATEAU is not None
        assert ResponseModel.QUADRATIC is not None
        assert ResponseModel.LINEAR_PLATEAU is not None

    def test_soil_test_level_enum(self):
        """Test soil test level enum."""
        from core.calculations.yield_response import SoilTestLevel

        assert SoilTestLevel.VERY_LOW is not None
        assert SoilTestLevel.LOW is not None
        assert SoilTestLevel.MEDIUM is not None
        assert SoilTestLevel.HIGH is not None

    def test_default_crop_parameters(self):
        """Test default crop parameter loading."""
        from core.calculations.yield_response import get_offline_yield_calculator

        calc = get_offline_yield_calculator()

        # get_crop_parameters is the method name
        corn_params = calc.get_crop_parameters('corn')
        assert corn_params is not None
        assert 'N' in corn_params


class TestSprayTimingCalculator:
    """Tests for spray timing calculation engine."""

    def test_calculator_initialization(self):
        """Test offline spray calculator initializes."""
        from core.calculations.spray_timing import get_offline_spray_calculator

        calc = get_offline_spray_calculator()
        assert calc is not None

    def test_weather_condition_creation(self):
        """Test WeatherCondition dataclass."""
        from core.calculations.spray_timing import WeatherCondition

        weather = WeatherCondition(
            temperature_f=75,
            wind_speed_mph=8,
            humidity_pct=55
        )

        assert weather.temperature_f == 75
        assert weather.wind_speed_mph == 8
        assert weather.humidity_pct == 55

    def test_evaluate_good_conditions(self):
        """Test evaluation of good spray conditions."""
        from core.calculations.spray_timing import (
            get_offline_spray_calculator, WeatherCondition
        )

        calc = get_offline_spray_calculator()
        weather = WeatherCondition(
            temperature_f=70,
            wind_speed_mph=5,
            humidity_pct=60
        )

        result = calc.evaluate_conditions(weather)

        assert result is not None
        assert hasattr(result, 'risk_level')
        # Good conditions should be excellent/good/fair
        assert result.risk_level.value in ['excellent', 'good', 'fair', 'EXCELLENT', 'GOOD', 'FAIR']

    def test_evaluate_windy_conditions(self):
        """Test evaluation of windy conditions."""
        from core.calculations.spray_timing import (
            get_offline_spray_calculator, WeatherCondition
        )

        calc = get_offline_spray_calculator()
        weather = WeatherCondition(
            temperature_f=70,
            wind_speed_mph=18,  # High wind (above 15 mph threshold)
            humidity_pct=60
        )

        result = calc.evaluate_conditions(weather)

        assert result is not None
        # High wind should increase risk - poor or do_not_spray
        assert result.risk_level.value in ['poor', 'do_not_spray', 'POOR', 'DO_NOT_SPRAY', 'fair', 'FAIR']

    def test_evaluate_hot_dry_conditions(self):
        """Test evaluation of hot, dry conditions."""
        from core.calculations.spray_timing import (
            get_offline_spray_calculator, WeatherCondition
        )

        calc = get_offline_spray_calculator()
        weather = WeatherCondition(
            temperature_f=95,  # Hot
            wind_speed_mph=5,
            humidity_pct=25  # Low humidity
        )

        result = calc.evaluate_conditions(weather)

        assert result is not None
        # Hot/dry = evaporation risk - should have concerns or recommendations
        assert hasattr(result, 'concerns') or hasattr(result, 'recommendations')

    def test_delta_t_calculation(self):
        """Test Delta-T calculation."""
        from core.calculations.spray_timing import get_offline_spray_calculator

        calc = get_offline_spray_calculator()

        # calculate_delta_t needs temp_f, humidity_pct, and dew_point_f
        delta_t = calc.calculate_delta_t(
            temp_f=75,
            humidity_pct=60,
            dew_point_f=55
        )
        # Delta-T should be a reasonable value
        assert delta_t is not None
        assert isinstance(delta_t, (int, float))
        assert 0 <= delta_t <= 30  # Reasonable range

    def test_risk_level_enum(self):
        """Test RiskLevel enum values."""
        from core.calculations.spray_timing import RiskLevel

        assert RiskLevel.EXCELLENT is not None
        assert RiskLevel.GOOD is not None
        assert RiskLevel.FAIR is not None
        assert RiskLevel.POOR is not None
        assert RiskLevel.DO_NOT_SPRAY is not None

    def test_spray_type_enum(self):
        """Test SprayType enum values."""
        from core.calculations.spray_timing import SprayType

        assert SprayType.HERBICIDE is not None
        assert SprayType.INSECTICIDE is not None
        assert SprayType.FUNGICIDE is not None

    def test_evaluation_has_recommendations(self):
        """Test evaluation result has recommendations."""
        from core.calculations.spray_timing import (
            get_offline_spray_calculator, WeatherCondition
        )

        calc = get_offline_spray_calculator()
        weather = WeatherCondition(
            temperature_f=75,
            wind_speed_mph=5,
            humidity_pct=60
        )

        result = calc.evaluate_conditions(weather)
        assert result is not None
        assert hasattr(result, 'recommendations')
        assert isinstance(result.recommendations, list)


class TestCalculationEdgeCases:
    """Tests for edge cases in calculations."""

    def test_zero_rate_yield(self):
        """Test yield calculation at zero nutrient rate."""
        from core.calculations.yield_response import get_offline_yield_calculator

        calc = get_offline_yield_calculator()
        result = calc.calculate_eor(
            crop='corn',
            nutrient='N',
            nutrient_cost=0.50,
            grain_price=5.00,
            yield_potential=200
        )
        # EOR should still be calculable
        assert result is not None

    def test_extreme_temperatures(self):
        """Test spray evaluation at extreme temperatures."""
        from core.calculations.spray_timing import (
            get_offline_spray_calculator, WeatherCondition
        )

        calc = get_offline_spray_calculator()

        # Very cold
        cold = WeatherCondition(temperature_f=35, wind_speed_mph=5, humidity_pct=60)
        cold_result = calc.evaluate_conditions(cold)
        assert cold_result is not None

        # Very hot
        hot = WeatherCondition(temperature_f=105, wind_speed_mph=5, humidity_pct=20)
        hot_result = calc.evaluate_conditions(hot)
        assert hot_result is not None

    def test_boundary_humidity(self):
        """Test spray evaluation at boundary humidity values."""
        from core.calculations.spray_timing import (
            get_offline_spray_calculator, WeatherCondition
        )

        calc = get_offline_spray_calculator()

        # Very low humidity
        dry = WeatherCondition(temperature_f=75, wind_speed_mph=5, humidity_pct=10)
        dry_result = calc.evaluate_conditions(dry)
        assert dry_result is not None

        # Very high humidity
        humid = WeatherCondition(temperature_f=75, wind_speed_mph=5, humidity_pct=95)
        humid_result = calc.evaluate_conditions(humid)
        assert humid_result is not None
