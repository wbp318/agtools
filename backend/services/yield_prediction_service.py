"""
Yield Prediction Service
Phase 3 of AgTools AI/ML Intelligence Suite (v3.0)

Features:
- Train on historical field data (inputs, weather, yields)
- Predict expected yield based on current season inputs
- Factor in weather patterns, soil conditions, input rates
- Confidence intervals and risk assessment
- Marketing/pricing decision support
"""

import logging
import json
import sqlite3
import pickle
from datetime import date
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Try to import sklearn for ML
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.info("scikit-learn not available - using simplified prediction model")


class CropType(str, Enum):
    CORN = "corn"
    SOYBEAN = "soybean"
    WHEAT = "wheat"
    RICE = "rice"
    COTTON = "cotton"
    GRAIN_SORGHUM = "grain_sorghum"


class ModelType(str, Enum):
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    LINEAR = "linear"
    RIDGE = "ridge"
    ENSEMBLE = "ensemble"


@dataclass
class YieldPrediction:
    """Yield prediction result"""
    crop: CropType
    field_id: Optional[int]
    field_name: Optional[str]
    predicted_yield: float
    yield_unit: str
    confidence_low: float
    confidence_high: float
    confidence_level: float  # 0-1
    factors: Dict[str, float]  # Factor importance
    comparison: Dict[str, Any]  # Comparison to benchmarks
    recommendations: List[str]
    model_info: Dict[str, Any]


@dataclass
class TrainingData:
    """Training data for yield prediction"""
    crop: CropType
    crop_year: int
    field_id: Optional[int]
    # Planting info
    planting_date: Optional[str]
    seed_variety: Optional[str]
    seeding_rate: float  # seeds/acre or lbs/acre
    # Fertilizer inputs
    nitrogen_rate: float  # lbs N/acre
    phosphorus_rate: float  # lbs P2O5/acre
    potassium_rate: float  # lbs K2O/acre
    # Soil
    soil_type: Optional[str]
    soil_ph: Optional[float]
    organic_matter: Optional[float]
    # Weather (growing season)
    total_rainfall: Optional[float]  # inches
    gdd_accumulated: Optional[float]  # Growing Degree Days
    avg_temp: Optional[float]
    # Management
    irrigation: bool
    previous_crop: Optional[str]
    tillage_type: Optional[str]
    # Actual yield
    actual_yield: float
    moisture_at_harvest: Optional[float]


# Default crop parameters for baseline predictions
CROP_DEFAULTS = {
    CropType.CORN: {
        "yield_unit": "bu/acre",
        "typical_yield": 180,
        "yield_range": (120, 250),
        "optimal_n": 180,  # lbs N/acre
        "optimal_p": 60,
        "optimal_k": 80,
        "optimal_seeding": 34000,  # seeds/acre
        "gdd_requirement": 2700,
        "n_response": 0.8,  # bu/lb N up to optimum
        "base_temp": 50,
    },
    CropType.SOYBEAN: {
        "yield_unit": "bu/acre",
        "typical_yield": 55,
        "yield_range": (35, 75),
        "optimal_n": 0,  # N-fixing
        "optimal_p": 40,
        "optimal_k": 60,
        "optimal_seeding": 140000,
        "gdd_requirement": 2500,
        "n_response": 0,
        "base_temp": 50,
    },
    CropType.WHEAT: {
        "yield_unit": "bu/acre",
        "typical_yield": 65,
        "yield_range": (40, 90),
        "optimal_n": 100,
        "optimal_p": 40,
        "optimal_k": 40,
        "optimal_seeding": 1200000,  # seeds/acre
        "gdd_requirement": 2000,
        "n_response": 0.6,
        "base_temp": 32,
    },
    CropType.RICE: {
        "yield_unit": "cwt/acre",
        "typical_yield": 75,
        "yield_range": (50, 95),
        "optimal_n": 150,
        "optimal_p": 50,
        "optimal_k": 60,
        "optimal_seeding": 80,  # lbs/acre
        "gdd_requirement": 2800,
        "n_response": 0.5,
        "base_temp": 50,
    },
    CropType.COTTON: {
        "yield_unit": "lbs lint/acre",
        "typical_yield": 1000,
        "yield_range": (600, 1400),
        "optimal_n": 100,
        "optimal_p": 40,
        "optimal_k": 60,
        "optimal_seeding": 40000,
        "gdd_requirement": 2200,
        "n_response": 5,
        "base_temp": 60,
    },
    CropType.GRAIN_SORGHUM: {
        "yield_unit": "bu/acre",
        "typical_yield": 110,
        "yield_range": (70, 150),
        "optimal_n": 120,
        "optimal_p": 40,
        "optimal_k": 40,
        "optimal_seeding": 60000,
        "gdd_requirement": 2500,
        "n_response": 0.7,
        "base_temp": 50,
    },
}


class YieldPredictionService:
    """
    Yield Prediction Service

    Uses machine learning to predict crop yields based on
    historical data, inputs, and growing conditions.
    """

    def __init__(self, db_path: str = "agtools.db", models_dir: str = "models/yield"):
        """
        Initialize Yield Prediction Service

        Args:
            db_path: Path to SQLite database
            models_dir: Directory for trained models
        """
        self.db_path = db_path
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.models: Dict[CropType, Any] = {}
        self.scalers: Dict[CropType, Any] = {}
        self.feature_names: Dict[CropType, List[str]] = {}

        self._init_db()
        self._load_models()

    def _init_db(self):
        """Initialize database tables for yield prediction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Historical yield data for training
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS yield_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER,
                crop TEXT NOT NULL,
                crop_year INTEGER NOT NULL,
                planting_date DATE,
                seed_variety TEXT,
                seeding_rate REAL,
                nitrogen_rate REAL,
                phosphorus_rate REAL,
                potassium_rate REAL,
                soil_type TEXT,
                soil_ph REAL,
                organic_matter REAL,
                total_rainfall REAL,
                gdd_accumulated REAL,
                avg_temp REAL,
                irrigation BOOLEAN,
                previous_crop TEXT,
                tillage_type TEXT,
                actual_yield REAL NOT NULL,
                moisture_at_harvest REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Yield predictions log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS yield_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER,
                crop TEXT NOT NULL,
                crop_year INTEGER NOT NULL,
                predicted_yield REAL NOT NULL,
                confidence_low REAL,
                confidence_high REAL,
                model_type TEXT,
                input_data TEXT,
                actual_yield REAL,
                prediction_error REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Model training history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS yield_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crop TEXT NOT NULL,
                model_type TEXT NOT NULL,
                model_path TEXT,
                training_records INTEGER,
                r2_score REAL,
                mae REAL,
                rmse REAL,
                feature_importance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)

        conn.commit()
        conn.close()

    def _load_models(self):
        """Load trained models from disk"""
        for crop in CropType:
            model_path = self.models_dir / f"{crop.value}_model.pkl"
            scaler_path = self.models_dir / f"{crop.value}_scaler.pkl"
            features_path = self.models_dir / f"{crop.value}_features.json"

            if model_path.exists() and HAS_SKLEARN:
                try:
                    with open(model_path, 'rb') as f:
                        self.models[crop] = pickle.load(f)
                    if scaler_path.exists():
                        with open(scaler_path, 'rb') as f:
                            self.scalers[crop] = pickle.load(f)
                    if features_path.exists():
                        with open(features_path, 'r') as f:
                            self.feature_names[crop] = json.load(f)
                    logger.info(f"Loaded yield model for {crop.value}")
                except Exception as e:
                    logger.warning(f"Failed to load model for {crop.value}: {e}")

    def add_historical_data(self, data: TrainingData) -> int:
        """
        Add historical yield data for training

        Args:
            data: TrainingData object with field/yield information

        Returns:
            ID of inserted record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO yield_history
            (field_id, crop, crop_year, planting_date, seed_variety, seeding_rate,
             nitrogen_rate, phosphorus_rate, potassium_rate, soil_type, soil_ph,
             organic_matter, total_rainfall, gdd_accumulated, avg_temp, irrigation,
             previous_crop, tillage_type, actual_yield, moisture_at_harvest)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.field_id, data.crop.value, data.crop_year, data.planting_date,
            data.seed_variety, data.seeding_rate, data.nitrogen_rate,
            data.phosphorus_rate, data.potassium_rate, data.soil_type,
            data.soil_ph, data.organic_matter, data.total_rainfall,
            data.gdd_accumulated, data.avg_temp, data.irrigation,
            data.previous_crop, data.tillage_type, data.actual_yield,
            data.moisture_at_harvest
        ))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return record_id

    def train_model(
        self,
        crop: CropType,
        model_type: ModelType = ModelType.RANDOM_FOREST,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train yield prediction model for a crop

        Args:
            crop: Crop type to train for
            model_type: Type of ML model to use
            test_size: Fraction of data for testing

        Returns:
            Training results with metrics
        """
        if not HAS_SKLEARN:
            return {
                "status": "error",
                "message": "scikit-learn not installed. Run: pip install scikit-learn"
            }

        # Get training data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT seeding_rate, nitrogen_rate, phosphorus_rate, potassium_rate,
                   soil_ph, organic_matter, total_rainfall, gdd_accumulated,
                   avg_temp, irrigation, actual_yield
            FROM yield_history
            WHERE crop = ? AND actual_yield IS NOT NULL
        """, (crop.value,))

        rows = cursor.fetchall()
        conn.close()

        if len(rows) < 10:
            return {
                "status": "error",
                "message": f"Need at least 10 records for training, have {len(rows)}"
            }

        # Prepare features and target
        feature_names = [
            'seeding_rate', 'nitrogen_rate', 'phosphorus_rate', 'potassium_rate',
            'soil_ph', 'organic_matter', 'total_rainfall', 'gdd_accumulated',
            'avg_temp', 'irrigation'
        ]

        X = []
        y = []

        for row in rows:
            features = list(row[:-1])
            # Handle None values with defaults
            defaults = CROP_DEFAULTS.get(crop, CROP_DEFAULTS[CropType.CORN])
            features = [
                features[0] or defaults['optimal_seeding'],
                features[1] or 0,
                features[2] or 0,
                features[3] or 0,
                features[4] or 6.5,
                features[5] or 3.0,
                features[6] or 20,
                features[7] or defaults['gdd_requirement'],
                features[8] or 70,
                1 if features[9] else 0
            ]
            X.append(features)
            y.append(row[-1])

        X = np.array(X)
        y = np.array(y)

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42
        )

        # Train model
        if model_type == ModelType.RANDOM_FOREST:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == ModelType.GRADIENT_BOOSTING:
            model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        elif model_type == ModelType.LINEAR:
            model = LinearRegression()
        elif model_type == ModelType.RIDGE:
            model = Ridge(alpha=1.0)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        # Cross-validation
        cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='r2')

        # Feature importance
        if hasattr(model, 'feature_importances_'):
            importance = dict(zip(feature_names, model.feature_importances_))
        else:
            importance = {}

        # Save model
        model_path = self.models_dir / f"{crop.value}_model.pkl"
        scaler_path = self.models_dir / f"{crop.value}_scaler.pkl"
        features_path = self.models_dir / f"{crop.value}_features.json"

        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        with open(features_path, 'w') as f:
            json.dump(feature_names, f)

        # Update loaded models
        self.models[crop] = model
        self.scalers[crop] = scaler
        self.feature_names[crop] = feature_names

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE yield_models SET is_active = FALSE WHERE crop = ?
        """, (crop.value,))

        cursor.execute("""
            INSERT INTO yield_models
            (crop, model_type, model_path, training_records, r2_score, mae, rmse,
             feature_importance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            crop.value, model_type.value, str(model_path), len(rows),
            r2, mae, rmse, json.dumps(importance)
        ))

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "crop": crop.value,
            "model_type": model_type.value,
            "training_records": len(rows),
            "metrics": {
                "r2_score": round(r2, 4),
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
                "cv_r2_mean": round(np.mean(cv_scores), 4),
                "cv_r2_std": round(np.std(cv_scores), 4)
            },
            "feature_importance": {k: round(v, 4) for k, v in sorted(
                importance.items(), key=lambda x: x[1], reverse=True
            )}
        }

    def predict_yield(
        self,
        crop: CropType,
        field_id: Optional[int] = None,
        field_name: Optional[str] = None,
        seeding_rate: Optional[float] = None,
        nitrogen_rate: float = 0,
        phosphorus_rate: float = 0,
        potassium_rate: float = 0,
        soil_ph: float = 6.5,
        organic_matter: float = 3.0,
        total_rainfall: Optional[float] = None,
        gdd_accumulated: Optional[float] = None,
        avg_temp: float = 70,
        irrigation: bool = False,
        save_prediction: bool = True
    ) -> YieldPrediction:
        """
        Predict yield for given inputs

        Args:
            crop: Crop type
            field_id: Optional field ID
            field_name: Optional field name
            seeding_rate: Seeding rate
            nitrogen_rate: N applied (lbs/acre)
            phosphorus_rate: P2O5 applied (lbs/acre)
            potassium_rate: K2O applied (lbs/acre)
            soil_ph: Soil pH
            organic_matter: Organic matter %
            total_rainfall: Growing season rainfall (inches)
            gdd_accumulated: Growing degree days
            avg_temp: Average temperature
            irrigation: Whether field is irrigated
            save_prediction: Save prediction to database

        Returns:
            YieldPrediction with predicted yield and confidence
        """
        defaults = CROP_DEFAULTS.get(crop, CROP_DEFAULTS[CropType.CORN])

        # Use defaults for missing values
        seeding_rate = seeding_rate or defaults['optimal_seeding']
        total_rainfall = total_rainfall or 20  # Default 20 inches
        gdd_accumulated = gdd_accumulated or defaults['gdd_requirement']

        # Check if we have a trained model
        if crop in self.models and HAS_SKLEARN:
            prediction = self._predict_with_model(
                crop, seeding_rate, nitrogen_rate, phosphorus_rate, potassium_rate,
                soil_ph, organic_matter, total_rainfall, gdd_accumulated, avg_temp,
                irrigation
            )
        else:
            # Use agronomic formula
            prediction = self._predict_agronomic(
                crop, seeding_rate, nitrogen_rate, phosphorus_rate, potassium_rate,
                soil_ph, organic_matter, total_rainfall, gdd_accumulated, avg_temp,
                irrigation
            )

        # Build factors importance
        factors = self._calculate_factor_impact(
            crop, nitrogen_rate, total_rainfall, gdd_accumulated, irrigation
        )

        # Compare to benchmarks
        comparison = {
            "typical_yield": defaults['typical_yield'],
            "vs_typical": round((prediction['yield'] - defaults['typical_yield']) /
                               defaults['typical_yield'] * 100, 1),
            "yield_range": defaults['yield_range'],
            "percentile": self._estimate_percentile(crop, prediction['yield'])
        }

        # Generate recommendations
        recommendations = self._generate_recommendations(
            crop, prediction['yield'], nitrogen_rate, total_rainfall, irrigation, defaults
        )

        result = YieldPrediction(
            crop=crop,
            field_id=field_id,
            field_name=field_name,
            predicted_yield=prediction['yield'],
            yield_unit=defaults['yield_unit'],
            confidence_low=prediction['low'],
            confidence_high=prediction['high'],
            confidence_level=prediction['confidence'],
            factors=factors,
            comparison=comparison,
            recommendations=recommendations,
            model_info={
                "model_type": prediction.get('model_type', 'agronomic'),
                "has_trained_model": crop in self.models
            }
        )

        # Save prediction
        if save_prediction:
            self._save_prediction(result, {
                'seeding_rate': seeding_rate,
                'nitrogen_rate': nitrogen_rate,
                'phosphorus_rate': phosphorus_rate,
                'potassium_rate': potassium_rate,
                'soil_ph': soil_ph,
                'organic_matter': organic_matter,
                'total_rainfall': total_rainfall,
                'gdd_accumulated': gdd_accumulated,
                'avg_temp': avg_temp,
                'irrigation': irrigation
            })

        return result

    def _predict_with_model(
        self, crop: CropType, seeding_rate: float, nitrogen_rate: float,
        phosphorus_rate: float, potassium_rate: float, soil_ph: float,
        organic_matter: float, total_rainfall: float, gdd_accumulated: float,
        avg_temp: float, irrigation: bool
    ) -> Dict[str, float]:
        """Predict using trained ML model"""
        model = self.models[crop]
        scaler = self.scalers.get(crop)

        features = np.array([[
            seeding_rate, nitrogen_rate, phosphorus_rate, potassium_rate,
            soil_ph, organic_matter, total_rainfall, gdd_accumulated,
            avg_temp, 1 if irrigation else 0
        ]])

        if scaler:
            features = scaler.transform(features)

        predicted = model.predict(features)[0]

        # Estimate confidence interval
        if hasattr(model, 'estimators_'):
            # For ensemble models, use tree predictions
            predictions = [tree.predict(features)[0] for tree in model.estimators_]
            std = np.std(predictions)
            confidence = max(0.5, 1 - std / predicted) if predicted > 0 else 0.5
        else:
            std = predicted * 0.1  # 10% uncertainty for simple models
            confidence = 0.7

        return {
            'yield': round(predicted, 1),
            'low': round(predicted - 2 * std, 1),
            'high': round(predicted + 2 * std, 1),
            'confidence': round(confidence, 2),
            'model_type': 'ml_trained'
        }

    def _predict_agronomic(
        self, crop: CropType, seeding_rate: float, nitrogen_rate: float,
        phosphorus_rate: float, potassium_rate: float, soil_ph: float,
        organic_matter: float, total_rainfall: float, gdd_accumulated: float,
        avg_temp: float, irrigation: bool
    ) -> Dict[str, float]:
        """Predict using agronomic formulas when no trained model available"""
        defaults = CROP_DEFAULTS.get(crop, CROP_DEFAULTS[CropType.CORN])

        base_yield = defaults['typical_yield']

        # Nitrogen response (diminishing returns)
        optimal_n = defaults['optimal_n']
        if optimal_n > 0:
            n_ratio = min(nitrogen_rate / optimal_n, 1.2)
            n_factor = 0.7 + 0.3 * (1 - (1 - n_ratio) ** 2) if n_ratio <= 1 else 1.0 - 0.1 * (n_ratio - 1)
        else:
            n_factor = 1.0

        # Rainfall factor
        optimal_rain = 25 if not irrigation else 15  # inches
        rain_ratio = total_rainfall / optimal_rain
        rain_factor = min(1.0, 0.5 + 0.5 * rain_ratio) if rain_ratio < 1 else max(0.8, 1.1 - 0.1 * (rain_ratio - 1))

        # GDD factor
        gdd_req = defaults['gdd_requirement']
        gdd_ratio = gdd_accumulated / gdd_req
        gdd_factor = min(1.0, 0.6 + 0.4 * gdd_ratio) if gdd_ratio < 1 else 1.0

        # Irrigation bonus
        irrigation_factor = 1.15 if irrigation else 1.0

        # Seeding rate factor
        optimal_seeding = defaults['optimal_seeding']
        seeding_ratio = seeding_rate / optimal_seeding
        seeding_factor = min(1.0, 0.7 + 0.3 * seeding_ratio) if seeding_ratio < 1 else max(0.95, 1.0 - 0.05 * (seeding_ratio - 1))

        # Soil pH factor (optimal ~6.5)
        ph_optimal = 6.5
        ph_diff = abs(soil_ph - ph_optimal)
        ph_factor = max(0.8, 1.0 - 0.05 * ph_diff)

        # Calculate predicted yield
        predicted = base_yield * n_factor * rain_factor * gdd_factor * irrigation_factor * seeding_factor * ph_factor

        # Clamp to reasonable range
        predicted = max(defaults['yield_range'][0] * 0.8,
                       min(defaults['yield_range'][1] * 1.1, predicted))

        # Confidence based on how far from typical
        deviation = abs(predicted - base_yield) / base_yield
        confidence = max(0.5, 0.9 - deviation)

        # Uncertainty range
        uncertainty = base_yield * 0.15  # 15% base uncertainty

        return {
            'yield': round(predicted, 1),
            'low': round(predicted - uncertainty, 1),
            'high': round(predicted + uncertainty, 1),
            'confidence': round(confidence, 2),
            'model_type': 'agronomic_formula'
        }

    def _calculate_factor_impact(
        self, crop: CropType, nitrogen_rate: float, total_rainfall: float,
        gdd_accumulated: float, irrigation: bool
    ) -> Dict[str, float]:
        """Calculate relative impact of each factor"""
        defaults = CROP_DEFAULTS.get(crop, CROP_DEFAULTS[CropType.CORN])

        factors = {}

        # Nitrogen impact
        if defaults['optimal_n'] > 0:
            n_optimal = min(nitrogen_rate / defaults['optimal_n'], 1.0)
            factors['nitrogen'] = round(n_optimal * 0.3, 2)  # Up to 30% impact
        else:
            factors['nitrogen'] = 0

        # Water impact
        water_score = min((total_rainfall + (10 if irrigation else 0)) / 25, 1.0)
        factors['water'] = round(water_score * 0.35, 2)  # Up to 35% impact

        # Heat units impact
        gdd_score = min(gdd_accumulated / defaults['gdd_requirement'], 1.0)
        factors['heat_units'] = round(gdd_score * 0.25, 2)  # Up to 25% impact

        # Other factors
        factors['genetics_management'] = 0.10  # Fixed 10%

        return factors

    def _estimate_percentile(self, crop: CropType, predicted_yield: float) -> int:
        """Estimate percentile ranking of predicted yield"""
        defaults = CROP_DEFAULTS.get(crop, CROP_DEFAULTS[CropType.CORN])

        low, high = defaults['yield_range']
        typical = defaults['typical_yield']

        if predicted_yield >= high:
            return 95
        elif predicted_yield <= low:
            return 10
        else:
            # Linear interpolation
            if predicted_yield >= typical:
                percentile = 50 + 45 * (predicted_yield - typical) / (high - typical)
            else:
                percentile = 10 + 40 * (predicted_yield - low) / (typical - low)
            return int(percentile)

    def _generate_recommendations(
        self, crop: CropType, predicted_yield: float, nitrogen_rate: float,
        total_rainfall: float, irrigation: bool, defaults: Dict
    ) -> List[str]:
        """Generate recommendations based on prediction"""
        recommendations = []

        # Check nitrogen
        if defaults['optimal_n'] > 0:
            if nitrogen_rate < defaults['optimal_n'] * 0.8:
                gap = defaults['optimal_n'] - nitrogen_rate
                recommendations.append(
                    f"Consider increasing N rate by {gap:.0f} lbs/acre to optimize yield"
                )
            elif nitrogen_rate > defaults['optimal_n'] * 1.2:
                excess = nitrogen_rate - defaults['optimal_n']
                recommendations.append(
                    f"N rate exceeds optimum by {excess:.0f} lbs/acre - potential for savings"
                )

        # Check water
        if total_rainfall < 15 and not irrigation:
            recommendations.append(
                "Low rainfall predicted - consider irrigation if available"
            )

        # Yield expectations
        if predicted_yield < defaults['typical_yield'] * 0.8:
            recommendations.append(
                "Yield below typical - review inputs and field conditions"
            )
        elif predicted_yield > defaults['typical_yield'] * 1.1:
            recommendations.append(
                "Above-average yield expected - ensure adequate harvest capacity"
            )

        # Marketing
        recommendations.append(
            f"Consider forward contracting at predicted yield of {predicted_yield:.0f} {defaults['yield_unit']}"
        )

        return recommendations

    def _save_prediction(self, prediction: YieldPrediction, input_data: Dict):
        """Save prediction to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO yield_predictions
            (field_id, crop, crop_year, predicted_yield, confidence_low,
             confidence_high, model_type, input_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction.field_id,
            prediction.crop.value,
            date.today().year,
            prediction.predicted_yield,
            prediction.confidence_low,
            prediction.confidence_high,
            prediction.model_info.get('model_type', 'unknown'),
            json.dumps(input_data)
        ))

        conn.commit()
        conn.close()

    def get_model_info(self, crop: Optional[CropType] = None) -> Dict[str, Any]:
        """Get information about available models"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if crop:
            cursor.execute("""
                SELECT crop, model_type, training_records, r2_score, mae, rmse,
                       feature_importance, created_at
                FROM yield_models
                WHERE crop = ? AND is_active = TRUE
            """, (crop.value,))
        else:
            cursor.execute("""
                SELECT crop, model_type, training_records, r2_score, mae, rmse,
                       feature_importance, created_at
                FROM yield_models
                WHERE is_active = TRUE
            """)

        rows = cursor.fetchall()
        conn.close()

        models = {}
        for row in rows:
            models[row[0]] = {
                "model_type": row[1],
                "training_records": row[2],
                "r2_score": row[3],
                "mae": row[4],
                "rmse": row[5],
                "feature_importance": json.loads(row[6]) if row[6] else {},
                "trained_at": row[7]
            }

        return {
            "available_models": models,
            "sklearn_available": HAS_SKLEARN,
            "crops_supported": [c.value for c in CropType],
            "default_parameters": {
                c.value: {
                    "typical_yield": d['typical_yield'],
                    "yield_unit": d['yield_unit'],
                    "optimal_n": d['optimal_n']
                }
                for c, d in CROP_DEFAULTS.items()
            }
        }

    def get_training_data_stats(self) -> Dict[str, Any]:
        """Get statistics about available training data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT crop, COUNT(*) as count, AVG(actual_yield) as avg_yield,
                   MIN(crop_year) as min_year, MAX(crop_year) as max_year
            FROM yield_history
            GROUP BY crop
        """)

        rows = cursor.fetchall()
        conn.close()

        stats = {}
        for row in rows:
            stats[row[0]] = {
                "record_count": row[1],
                "average_yield": round(row[2], 1) if row[2] else None,
                "year_range": f"{row[3]}-{row[4]}" if row[3] else None,
                "ready_for_training": row[1] >= 10
            }

        return {
            "by_crop": stats,
            "total_records": sum(s['record_count'] for s in stats.values()),
            "min_records_for_training": 10
        }


# Singleton instance
_yield_prediction_service: Optional[YieldPredictionService] = None


def get_yield_prediction_service() -> YieldPredictionService:
    """Get or create yield prediction service singleton"""
    global _yield_prediction_service
    if _yield_prediction_service is None:
        _yield_prediction_service = YieldPredictionService()
    return _yield_prediction_service
