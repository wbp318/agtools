"""
Weather-Based Spray AI Enhancement Service
Phase 5 of AgTools AI/ML Intelligence Suite (v3.0)

Features:
- ML-enhanced spray timing predictions
- Learn from historical spray success/failure data
- Factor in micro-climate patterns
- Optimize application windows based on outcomes
- Integrates with existing SprayTimingOptimizer
"""

import logging
import os
import json
import sqlite3
import pickle
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)

# Try to import sklearn
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class SprayOutcome(str, Enum):
    """Outcome of spray application"""
    EXCELLENT = "excellent"  # Perfect conditions, great efficacy
    GOOD = "good"           # Good conditions, expected efficacy
    FAIR = "fair"           # Some issues, reduced efficacy
    POOR = "poor"           # Problems occurred, low efficacy
    FAILED = "failed"       # Washed off, drifted, or no effect
    UNKNOWN = "unknown"


class SprayType(str, Enum):
    HERBICIDE = "herbicide"
    INSECTICIDE = "insecticide"
    FUNGICIDE = "fungicide"
    GROWTH_REGULATOR = "growth_regulator"
    DESICCANT = "desiccant"


@dataclass
class SprayApplication:
    """Historical spray application record"""
    field_id: Optional[int]
    spray_type: SprayType
    product_name: str
    application_date: str
    application_time: str  # Time of day
    # Weather at application
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: Optional[str]
    rain_last_24h: float
    rain_next_24h: float  # Known after the fact
    dew_point: Optional[float]
    cloud_cover: Optional[float]
    # Application details
    rate_per_acre: float
    acres_treated: float
    applicator: Optional[str]  # ground, aerial
    # Outcome
    outcome: SprayOutcome
    efficacy_rating: Optional[float]  # 0-100
    notes: Optional[str]


@dataclass
class SprayPrediction:
    """AI-enhanced spray timing prediction"""
    spray_type: SprayType
    conditions: Dict[str, float]
    predicted_outcome: SprayOutcome
    confidence: float
    success_probability: float
    risk_factors: List[str]
    recommendations: List[str]
    historical_similar: int  # Number of similar historical conditions
    model_used: str


# Weather condition scoring weights (learned from data)
DEFAULT_CONDITION_WEIGHTS = {
    SprayType.HERBICIDE: {
        'temperature': 0.15,
        'humidity': 0.10,
        'wind_speed': 0.25,
        'rain_risk': 0.30,
        'time_of_day': 0.10,
        'inversion_risk': 0.10
    },
    SprayType.FUNGICIDE: {
        'temperature': 0.15,
        'humidity': 0.20,
        'wind_speed': 0.15,
        'rain_risk': 0.20,
        'time_of_day': 0.15,
        'disease_pressure': 0.15
    },
    SprayType.INSECTICIDE: {
        'temperature': 0.20,
        'humidity': 0.10,
        'wind_speed': 0.20,
        'rain_risk': 0.20,
        'time_of_day': 0.15,
        'pest_activity': 0.15
    }
}


class SprayAIService:
    """
    AI-Enhanced Spray Timing Service

    Learns from historical spray outcomes to improve
    timing recommendations and predict application success.
    """

    def __init__(self, db_path: str = "agtools.db", model_dir: str = "models/spray"):
        """
        Initialize Spray AI Service

        Args:
            db_path: Path to SQLite database
            model_dir: Directory for trained models
        """
        self.db_path = db_path
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        self.models: Dict[SprayType, Any] = {}
        self.scalers: Dict[SprayType, Any] = {}
        self.condition_weights = DEFAULT_CONDITION_WEIGHTS.copy()

        self._init_db()
        self._load_models()
        self._calculate_condition_weights()

    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Historical spray applications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spray_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER,
                spray_type TEXT NOT NULL,
                product_name TEXT,
                application_date DATE NOT NULL,
                application_time TEXT,
                temperature REAL,
                humidity REAL,
                wind_speed REAL,
                wind_direction TEXT,
                rain_last_24h REAL,
                rain_next_24h REAL,
                dew_point REAL,
                cloud_cover REAL,
                rate_per_acre REAL,
                acres_treated REAL,
                applicator TEXT,
                outcome TEXT,
                efficacy_rating REAL,
                notes TEXT,
                created_by_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Spray predictions log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spray_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spray_type TEXT NOT NULL,
                conditions TEXT NOT NULL,
                predicted_outcome TEXT,
                confidence REAL,
                success_probability REAL,
                actual_outcome TEXT,
                prediction_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Model training history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spray_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spray_type TEXT NOT NULL,
                model_type TEXT NOT NULL,
                training_records INTEGER,
                accuracy REAL,
                feature_importance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)

        # Micro-climate patterns learned
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS microclimate_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER,
                hour_of_day INTEGER,
                month INTEGER,
                avg_temp_adjustment REAL,
                avg_wind_adjustment REAL,
                avg_humidity_adjustment REAL,
                inversion_probability REAL,
                sample_count INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        conn.commit()
        conn.close()

    def _load_models(self):
        """Load trained models"""
        for spray_type in SprayType:
            model_path = os.path.join(self.model_dir, f"{spray_type.value}_model.pkl")
            if os.path.exists(model_path) and HAS_SKLEARN:
                try:
                    with open(model_path, 'rb') as f:
                        data = pickle.load(f)
                        self.models[spray_type] = data.get('model')
                        self.scalers[spray_type] = data.get('scaler')
                except Exception as e:
                    logger.warning(f"Failed to load {spray_type.value} model: {e}")

    def _calculate_condition_weights(self):
        """Calculate condition weights from historical data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for spray_type in SprayType:
            cursor.execute("""
                SELECT outcome, temperature, humidity, wind_speed,
                       rain_last_24h, rain_next_24h
                FROM spray_applications
                WHERE spray_type = ? AND outcome IS NOT NULL
            """, (spray_type.value,))

            rows = cursor.fetchall()
            if len(rows) < 20:
                continue

            # Calculate correlations between conditions and outcomes
            # (Simplified - full implementation would use proper statistical analysis)
            success_temps = []
            fail_temps = []

            for row in rows:
                outcome, temp, humidity, wind, rain_before, rain_after = row
                if outcome in ['excellent', 'good']:
                    success_temps.append(temp or 70)
                elif outcome in ['poor', 'failed']:
                    fail_temps.append(temp or 70)

            # Update weights based on data patterns
            # (This is a simplified version)
            if success_temps and fail_temps:
                temp_importance = abs(np.mean(success_temps) - np.mean(fail_temps)) / 30
                self.condition_weights[spray_type]['temperature'] = min(0.25, temp_importance)

        conn.close()

    def add_spray_record(self, application: SprayApplication) -> int:
        """
        Add a historical spray application record

        Args:
            application: SprayApplication data

        Returns:
            Record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO spray_applications
            (field_id, spray_type, product_name, application_date, application_time,
             temperature, humidity, wind_speed, wind_direction, rain_last_24h,
             rain_next_24h, dew_point, cloud_cover, rate_per_acre, acres_treated,
             applicator, outcome, efficacy_rating, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            application.field_id, application.spray_type.value, application.product_name,
            application.application_date, application.application_time, application.temperature,
            application.humidity, application.wind_speed, application.wind_direction,
            application.rain_last_24h, application.rain_next_24h, application.dew_point,
            application.cloud_cover, application.rate_per_acre, application.acres_treated,
            application.applicator, application.outcome.value, application.efficacy_rating,
            application.notes
        ))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return record_id

    def predict_outcome(
        self,
        spray_type: SprayType,
        temperature: float,
        humidity: float,
        wind_speed: float,
        rain_chance: float = 0,
        time_of_day: str = "morning",
        field_id: Optional[int] = None
    ) -> SprayPrediction:
        """
        Predict spray application outcome

        Args:
            spray_type: Type of spray
            temperature: Temperature in Fahrenheit
            humidity: Relative humidity %
            wind_speed: Wind speed in mph
            rain_chance: Probability of rain (0-100)
            time_of_day: morning, midday, evening, night
            field_id: Optional field for micro-climate adjustment

        Returns:
            SprayPrediction with outcome prediction and recommendations
        """
        conditions = {
            'temperature': temperature,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'rain_chance': rain_chance,
            'time_of_day': time_of_day
        }

        # Apply micro-climate adjustments if field known
        if field_id:
            conditions = self._apply_microclimate(conditions, field_id, time_of_day)

        # Check if we have a trained ML model
        if spray_type in self.models and self.models[spray_type] and HAS_SKLEARN:
            prediction = self._predict_with_ml(spray_type, conditions)
        else:
            prediction = self._predict_rule_based(spray_type, conditions)

        # Find similar historical applications
        similar_count = self._count_similar_conditions(spray_type, conditions)
        prediction.historical_similar = similar_count

        # Generate recommendations
        prediction.recommendations = self._generate_recommendations(
            spray_type, conditions, prediction
        )

        return prediction

    def _predict_with_ml(self, spray_type: SprayType, conditions: Dict) -> SprayPrediction:
        """Predict using trained ML model"""
        model = self.models[spray_type]
        scaler = self.scalers.get(spray_type)

        # Prepare features
        time_encoding = {'morning': 0, 'midday': 1, 'evening': 2, 'night': 3}
        features = np.array([[
            conditions['temperature'],
            conditions['humidity'],
            conditions['wind_speed'],
            conditions['rain_chance'],
            time_encoding.get(conditions.get('time_of_day', 'morning'), 0)
        ]])

        if scaler:
            features = scaler.transform(features)

        # Get prediction and probabilities
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]

        # Map to outcome
        try:
            outcome = SprayOutcome(prediction)
        except ValueError:
            outcome = SprayOutcome.UNKNOWN

        # Calculate success probability (excellent + good outcomes)
        classes = model.classes_
        success_prob = 0
        for i, cls in enumerate(classes):
            if cls in ['excellent', 'good']:
                success_prob += probabilities[i]

        # Identify risk factors
        risk_factors = self._identify_risk_factors(spray_type, conditions)

        return SprayPrediction(
            spray_type=spray_type,
            conditions=conditions,
            predicted_outcome=outcome,
            confidence=float(max(probabilities)),
            success_probability=float(success_prob),
            risk_factors=risk_factors,
            recommendations=[],
            historical_similar=0,
            model_used="ml_trained"
        )

    def _predict_rule_based(self, spray_type: SprayType, conditions: Dict) -> SprayPrediction:
        """Predict using rule-based scoring"""
        score = 100  # Start at perfect

        risk_factors = []

        # Temperature scoring
        temp = conditions['temperature']
        if temp < 45 or temp > 90:
            score -= 30
            risk_factors.append(f"Temperature {temp}°F outside optimal range")
        elif temp < 55 or temp > 85:
            score -= 15
            risk_factors.append(f"Temperature {temp}°F marginal")

        # Wind scoring
        wind = conditions['wind_speed']
        if wind > 15:
            score -= 40
            risk_factors.append(f"Wind {wind} mph too high - drift risk")
        elif wind > 10:
            score -= 20
            risk_factors.append(f"Wind {wind} mph elevated")
        elif wind < 3:
            score -= 10
            risk_factors.append(f"Wind {wind} mph low - inversion risk")

        # Humidity scoring
        humidity = conditions['humidity']
        if humidity < 30:
            score -= 15
            risk_factors.append(f"Humidity {humidity}% too low - evaporation risk")
        elif humidity > 95:
            score -= 10
            risk_factors.append(f"Humidity {humidity}% very high")

        # Rain chance scoring
        rain = conditions.get('rain_chance', 0)
        if rain > 50:
            score -= 35
            risk_factors.append(f"Rain chance {rain}% - washoff risk")
        elif rain > 30:
            score -= 20
            risk_factors.append(f"Rain chance {rain}% elevated")

        # Time of day scoring
        time = conditions.get('time_of_day', 'morning')
        if time == 'night':
            score -= 25
            risk_factors.append("Night application - limited visibility")
        elif time == 'midday' and temp > 80:
            score -= 15
            risk_factors.append("Midday application in heat - evaporation risk")

        # Determine outcome based on score
        if score >= 85:
            outcome = SprayOutcome.EXCELLENT
        elif score >= 70:
            outcome = SprayOutcome.GOOD
        elif score >= 55:
            outcome = SprayOutcome.FAIR
        elif score >= 40:
            outcome = SprayOutcome.POOR
        else:
            outcome = SprayOutcome.FAILED

        confidence = score / 100
        success_prob = max(0, min(1, (score - 30) / 70))

        return SprayPrediction(
            spray_type=spray_type,
            conditions=conditions,
            predicted_outcome=outcome,
            confidence=round(confidence, 2),
            success_probability=round(success_prob, 2),
            risk_factors=risk_factors,
            recommendations=[],
            historical_similar=0,
            model_used="rule_based"
        )

    def _apply_microclimate(self, conditions: Dict, field_id: int, time_of_day: str) -> Dict:
        """Apply micro-climate adjustments for specific field"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        hour_map = {'morning': 8, 'midday': 12, 'evening': 18, 'night': 22}
        hour = hour_map.get(time_of_day, 12)
        month = datetime.now(timezone.utc).month

        cursor.execute("""
            SELECT avg_temp_adjustment, avg_wind_adjustment, avg_humidity_adjustment
            FROM microclimate_patterns
            WHERE field_id = ? AND hour_of_day = ? AND month = ?
        """, (field_id, hour, month))

        row = cursor.fetchone()
        conn.close()

        if row:
            conditions = conditions.copy()
            conditions['temperature'] += row[0] or 0
            conditions['wind_speed'] += row[1] or 0
            conditions['humidity'] += row[2] or 0

        return conditions

    def _identify_risk_factors(self, spray_type: SprayType, conditions: Dict) -> List[str]:
        """Identify risk factors in conditions"""
        risks = []

        if conditions['wind_speed'] > 10:
            risks.append("High wind increases drift risk")
        if conditions.get('rain_chance', 0) > 30:
            risks.append("Rain may reduce efficacy")
        if conditions['temperature'] > 85:
            risks.append("High temperature may cause volatilization")
        if conditions['humidity'] < 40:
            risks.append("Low humidity increases evaporation")

        return risks

    def _count_similar_conditions(self, spray_type: SprayType, conditions: Dict) -> int:
        """Count historical applications with similar conditions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM spray_applications
            WHERE spray_type = ?
            AND temperature BETWEEN ? AND ?
            AND wind_speed BETWEEN ? AND ?
            AND humidity BETWEEN ? AND ?
        """, (
            spray_type.value,
            conditions['temperature'] - 10, conditions['temperature'] + 10,
            max(0, conditions['wind_speed'] - 3), conditions['wind_speed'] + 3,
            max(0, conditions['humidity'] - 15), min(100, conditions['humidity'] + 15)
        ))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def _generate_recommendations(
        self,
        spray_type: SprayType,
        conditions: Dict,
        prediction: SprayPrediction
    ) -> List[str]:
        """Generate recommendations based on prediction"""
        recommendations = []

        if prediction.success_probability >= 0.8:
            recommendations.append("Conditions are favorable - proceed with application")
        elif prediction.success_probability >= 0.6:
            recommendations.append("Conditions acceptable but monitor closely")
        else:
            recommendations.append("Consider waiting for better conditions")

        # Specific recommendations based on risk factors
        if conditions['wind_speed'] > 10:
            recommendations.append("Use larger droplet size to reduce drift")
            recommendations.append("Consider reducing boom height")

        if conditions.get('rain_chance', 0) > 30:
            recommendations.append("Check radar for rain timing")
            recommendations.append("Consider using rain-fast adjuvant")

        if conditions['temperature'] > 80:
            recommendations.append("Apply in early morning or evening")
            recommendations.append("Add humectant adjuvant to reduce evaporation")

        if conditions['humidity'] < 40:
            recommendations.append("Increase water volume")
            recommendations.append("Consider oil-based adjuvant")

        return recommendations

    def train_model(self, spray_type: SprayType) -> Dict[str, Any]:
        """Train prediction model for spray type"""
        if not HAS_SKLEARN:
            return {"status": "error", "message": "scikit-learn not available"}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT temperature, humidity, wind_speed, rain_last_24h,
                   application_time, outcome
            FROM spray_applications
            WHERE spray_type = ? AND outcome IS NOT NULL
            AND temperature IS NOT NULL AND humidity IS NOT NULL
            AND wind_speed IS NOT NULL
        """, (spray_type.value,))

        rows = cursor.fetchall()
        conn.close()

        if len(rows) < 20:
            return {
                "status": "error",
                "message": f"Need at least 20 records, have {len(rows)}"
            }

        # Prepare features
        X = []
        y = []
        time_map = {'morning': 0, 'midday': 1, 'evening': 2, 'night': 3}

        for row in rows:
            temp, humidity, wind, rain, time_str, outcome = row
            time_val = time_map.get(time_str or 'morning', 0)
            X.append([temp, humidity, wind, rain or 0, time_val])
            y.append(outcome)

        X = np.array(X)
        y = np.array(y)

        # Split and train
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)

        # Save model
        model_path = os.path.join(self.model_dir, f"{spray_type.value}_model.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump({'model': model, 'scaler': scaler}, f)

        self.models[spray_type] = model
        self.scalers[spray_type] = scaler

        # Feature importance
        feature_names = ['temperature', 'humidity', 'wind_speed', 'rain', 'time_of_day']
        importance = dict(zip(feature_names, model.feature_importances_))

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO spray_models (spray_type, model_type, training_records, accuracy, feature_importance)
            VALUES (?, 'random_forest', ?, ?, ?)
        """, (spray_type.value, len(rows), accuracy, json.dumps(importance)))
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "spray_type": spray_type.value,
            "training_records": len(rows),
            "accuracy": round(accuracy, 4),
            "feature_importance": {k: round(v, 4) for k, v in sorted(importance.items(), key=lambda x: x[1], reverse=True)}
        }

    def get_historical_analysis(self, spray_type: Optional[SprayType] = None) -> Dict[str, Any]:
        """Get analysis of historical spray outcomes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if spray_type:
            cursor.execute("""
                SELECT outcome, COUNT(*) as count
                FROM spray_applications
                WHERE spray_type = ?
                GROUP BY outcome
            """, (spray_type.value,))
        else:
            cursor.execute("""
                SELECT outcome, COUNT(*) as count
                FROM spray_applications
                GROUP BY outcome
            """)

        outcomes = dict(cursor.fetchall())

        # Get average conditions by outcome
        cursor.execute("""
            SELECT outcome,
                   AVG(temperature) as avg_temp,
                   AVG(humidity) as avg_humidity,
                   AVG(wind_speed) as avg_wind
            FROM spray_applications
            WHERE outcome IS NOT NULL
            GROUP BY outcome
        """)

        by_outcome = {}
        for row in cursor.fetchall():
            by_outcome[row[0]] = {
                'avg_temperature': round(row[1], 1) if row[1] else None,
                'avg_humidity': round(row[2], 1) if row[2] else None,
                'avg_wind_speed': round(row[3], 1) if row[3] else None
            }

        conn.close()

        total = sum(outcomes.values())
        success_rate = (outcomes.get('excellent', 0) + outcomes.get('good', 0)) / total if total > 0 else 0

        return {
            "total_applications": total,
            "outcome_distribution": outcomes,
            "success_rate": round(success_rate, 3),
            "conditions_by_outcome": by_outcome,
            "models_available": list(self.models.keys())
        }

    def get_optimal_windows(
        self,
        spray_type: SprayType,
        forecast: List[Dict[str, Any]],
        min_success_prob: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find optimal spray windows in forecast

        Args:
            spray_type: Type of spray
            forecast: List of hourly forecast dicts
            min_success_prob: Minimum success probability threshold

        Returns:
            List of recommended windows
        """
        windows = []

        for i, hour in enumerate(forecast):
            prediction = self.predict_outcome(
                spray_type=spray_type,
                temperature=hour.get('temperature', 70),
                humidity=hour.get('humidity', 50),
                wind_speed=hour.get('wind_speed', 5),
                rain_chance=hour.get('rain_chance', 0),
                time_of_day=self._get_time_of_day(hour.get('hour', 12))
            )

            if prediction.success_probability >= min_success_prob:
                windows.append({
                    'datetime': hour.get('datetime', f'Hour {i}'),
                    'success_probability': prediction.success_probability,
                    'predicted_outcome': prediction.predicted_outcome.value,
                    'risk_factors': prediction.risk_factors,
                    'conditions': {
                        'temperature': hour.get('temperature'),
                        'humidity': hour.get('humidity'),
                        'wind_speed': hour.get('wind_speed'),
                        'rain_chance': hour.get('rain_chance')
                    }
                })

        # Sort by success probability
        windows.sort(key=lambda x: x['success_probability'], reverse=True)

        return windows[:10]  # Top 10 windows

    def _get_time_of_day(self, hour: int) -> str:
        """Convert hour to time of day category"""
        if 5 <= hour < 11:
            return 'morning'
        elif 11 <= hour < 17:
            return 'midday'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'


# Singleton
_spray_ai_service: Optional[SprayAIService] = None


def get_spray_ai_service() -> SprayAIService:
    """Get or create spray AI service singleton"""
    global _spray_ai_service
    if _spray_ai_service is None:
        _spray_ai_service = SprayAIService()
    return _spray_ai_service
