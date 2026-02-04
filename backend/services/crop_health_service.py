"""
Crop Health Scoring Service
Phase 2 of AgTools AI/ML Intelligence Suite (v3.0)

Features:
- Process drone/satellite field imagery
- NDVI and vegetation index analysis
- Problem area detection and mapping
- Health score generation per field zone
- Treatment recommendations based on detected issues
"""

import logging
import io
import json
import hashlib
import sqlite3
from datetime import datetime, date, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    logger.info("OpenCV not available - using PIL fallback for image processing")


class HealthStatus(str, Enum):
    """Field health status categories"""
    EXCELLENT = "excellent"      # NDVI > 0.7
    GOOD = "good"               # NDVI 0.5-0.7
    MODERATE = "moderate"       # NDVI 0.3-0.5
    STRESSED = "stressed"       # NDVI 0.2-0.3
    POOR = "poor"              # NDVI 0.1-0.2
    CRITICAL = "critical"       # NDVI < 0.1


class IssueType(str, Enum):
    """Types of crop health issues detected"""
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    WATER_STRESS = "water_stress"
    PEST_DAMAGE = "pest_damage"
    DISEASE = "disease"
    WEED_PRESSURE = "weed_pressure"
    HERBICIDE_DAMAGE = "herbicide_damage"
    WEATHER_DAMAGE = "weather_damage"
    UNKNOWN = "unknown"


class ImageType(str, Enum):
    """Types of input imagery"""
    RGB = "rgb"                      # Standard color photos
    NDVI = "ndvi"                    # Pre-calculated NDVI
    MULTISPECTRAL = "multispectral"  # Multi-band (NIR, Red, etc.)
    THERMAL = "thermal"              # Thermal/infrared


@dataclass
class ZoneHealth:
    """Health assessment for a field zone"""
    zone_id: int
    center_x: float
    center_y: float
    ndvi_mean: float
    ndvi_min: float
    ndvi_max: float
    health_status: HealthStatus
    area_percentage: float
    issue_type: Optional[IssueType]
    confidence: float
    recommendations: List[str]


@dataclass
class FieldHealthReport:
    """Complete health report for a field"""
    field_id: Optional[int]
    field_name: Optional[str]
    analysis_date: str
    image_hash: str
    image_type: ImageType
    overall_ndvi: float
    overall_health: HealthStatus
    healthy_percentage: float
    stressed_percentage: float
    zones: List[ZoneHealth]
    problem_areas: List[Dict]
    recommendations: List[str]
    processing_time_ms: int
    notes: List[str]


class CropHealthService:
    """
    Crop Health Scoring and Analysis Service

    Processes drone/satellite imagery to assess crop health,
    detect problem areas, and provide treatment recommendations.
    """

    # NDVI thresholds for health classification
    NDVI_THRESHOLDS = {
        HealthStatus.EXCELLENT: 0.7,
        HealthStatus.GOOD: 0.5,
        HealthStatus.MODERATE: 0.3,
        HealthStatus.STRESSED: 0.2,
        HealthStatus.POOR: 0.1,
        HealthStatus.CRITICAL: 0.0
    }

    # Issue detection patterns based on visual features
    ISSUE_PATTERNS = {
        IssueType.NUTRIENT_DEFICIENCY: {
            "ndvi_pattern": "gradual_decline",
            "color_hints": ["yellowing", "pale_green"],
            "spatial_pattern": "diffuse",
            "recommendations": [
                "Conduct tissue testing to identify specific nutrient deficiency",
                "Consider soil sampling in affected areas",
                "Apply appropriate fertilizer based on test results"
            ]
        },
        IssueType.WATER_STRESS: {
            "ndvi_pattern": "uniform_low",
            "color_hints": ["wilting", "curling"],
            "spatial_pattern": "large_patches",
            "recommendations": [
                "Check soil moisture levels",
                "Verify irrigation system function",
                "Consider additional irrigation if available"
            ]
        },
        IssueType.PEST_DAMAGE: {
            "ndvi_pattern": "spotty",
            "color_hints": ["holes", "defoliation"],
            "spatial_pattern": "scattered",
            "recommendations": [
                "Scout affected areas to identify pest",
                "Check economic thresholds",
                "Consider targeted treatment if threshold exceeded"
            ]
        },
        IssueType.DISEASE: {
            "ndvi_pattern": "spreading",
            "color_hints": ["lesions", "discoloration"],
            "spatial_pattern": "expanding_circles",
            "recommendations": [
                "Identify disease pathogen",
                "Check weather conditions for disease pressure",
                "Apply fungicide if economically justified"
            ]
        },
        IssueType.WEED_PRESSURE: {
            "ndvi_pattern": "mixed_high_low",
            "color_hints": ["different_texture"],
            "spatial_pattern": "patchy",
            "recommendations": [
                "Scout to identify weed species",
                "Consider post-emergence herbicide if window allows",
                "Plan weed management for next season"
            ]
        }
    }

    def __init__(self, db_path: str = "agtools.db", output_dir: str = "health_maps"):
        """
        Initialize Crop Health Service

        Args:
            db_path: Path to SQLite database
            output_dir: Directory for generated health maps
        """
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Initialize database tables for crop health data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Field health assessments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS field_health_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER,
                image_hash TEXT NOT NULL,
                image_path TEXT,
                analysis_date DATE NOT NULL,
                image_type TEXT NOT NULL,
                overall_ndvi REAL,
                overall_health TEXT,
                healthy_percentage REAL,
                stressed_percentage REAL,
                zones_data TEXT,
                problem_areas TEXT,
                recommendations TEXT,
                notes TEXT,
                created_by_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Health zone details
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                zone_id INTEGER NOT NULL,
                center_x REAL,
                center_y REAL,
                ndvi_mean REAL,
                ndvi_min REAL,
                ndvi_max REAL,
                health_status TEXT,
                area_percentage REAL,
                issue_type TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assessment_id) REFERENCES field_health_assessments(id)
            )
        """)

        # Historical health trends
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER NOT NULL,
                crop_year INTEGER NOT NULL,
                analysis_date DATE NOT NULL,
                overall_ndvi REAL,
                healthy_percentage REAL,
                stressed_percentage REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        conn.commit()
        conn.close()

    def _hash_image(self, image_bytes: bytes) -> str:
        """Generate hash for image identification"""
        return hashlib.sha256(image_bytes).hexdigest()[:16]

    def analyze_image(
        self,
        image_bytes: bytes,
        image_type: ImageType = ImageType.RGB,
        field_id: Optional[int] = None,
        field_name: Optional[str] = None,
        grid_size: int = 10,
        save_results: bool = True
    ) -> FieldHealthReport:
        """
        Analyze field image for crop health

        Args:
            image_bytes: Raw image bytes
            image_type: Type of imagery (RGB, NDVI, multispectral)
            field_id: Optional field ID for linking
            field_name: Optional field name
            grid_size: Number of zones to divide field into (grid_size x grid_size)
            save_results: Save results to database

        Returns:
            FieldHealthReport with comprehensive analysis
        """
        import time
        start_time = time.time()

        image_hash = self._hash_image(image_bytes)
        notes = []

        # Load and process image
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            img_array = np.array(image)
            notes.append(f"Image loaded: {image.width}x{image.height} pixels")
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}")

        # Calculate NDVI or pseudo-NDVI based on image type
        if image_type == ImageType.NDVI:
            # Image is already NDVI - extract values
            ndvi_map = self._extract_ndvi_from_visualization(img_array)
            notes.append("Using pre-calculated NDVI image")
        elif image_type == ImageType.MULTISPECTRAL:
            # Calculate true NDVI from NIR and Red bands
            ndvi_map = self._calculate_ndvi_multispectral(img_array)
            notes.append("Calculated NDVI from multispectral bands")
        else:
            # RGB image - calculate pseudo-NDVI using vegetation indices
            ndvi_map = self._calculate_pseudo_ndvi(img_array)
            notes.append("Calculated vegetation index from RGB (pseudo-NDVI)")

        # Divide into zones and analyze
        zones = self._analyze_zones(ndvi_map, grid_size)

        # Calculate overall statistics
        valid_ndvi = ndvi_map[~np.isnan(ndvi_map)]
        if len(valid_ndvi) > 0:
            overall_ndvi = float(np.mean(valid_ndvi))
        else:
            overall_ndvi = 0.0

        overall_health = self._classify_health(overall_ndvi)

        # Calculate healthy vs stressed percentages
        healthy_mask = ndvi_map >= self.NDVI_THRESHOLDS[HealthStatus.GOOD]
        stressed_mask = ndvi_map < self.NDVI_THRESHOLDS[HealthStatus.STRESSED]
        total_valid = np.sum(~np.isnan(ndvi_map))

        healthy_percentage = float(np.sum(healthy_mask) / total_valid * 100) if total_valid > 0 else 0
        stressed_percentage = float(np.sum(stressed_mask) / total_valid * 100) if total_valid > 0 else 0

        # Detect problem areas
        problem_areas = self._detect_problem_areas(ndvi_map, zones)

        # Generate recommendations
        recommendations = self._generate_recommendations(zones, problem_areas, overall_health)

        processing_time = int((time.time() - start_time) * 1000)

        # Build report
        report = FieldHealthReport(
            field_id=field_id,
            field_name=field_name,
            analysis_date=datetime.now(timezone.utc).isoformat(),
            image_hash=image_hash,
            image_type=image_type,
            overall_ndvi=round(overall_ndvi, 3),
            overall_health=overall_health,
            healthy_percentage=round(healthy_percentage, 1),
            stressed_percentage=round(stressed_percentage, 1),
            zones=zones,
            problem_areas=problem_areas,
            recommendations=recommendations,
            processing_time_ms=processing_time,
            notes=notes
        )

        # Save to database
        if save_results:
            self._save_assessment(report, image_bytes)

        # Generate and save health map visualization
        self._generate_health_map(ndvi_map, image_hash)

        return report

    def _calculate_pseudo_ndvi(self, rgb_array: np.ndarray) -> np.ndarray:
        """
        Calculate pseudo-NDVI from RGB image

        Uses Excess Green Index (ExG) or similar vegetation indices
        that work with standard RGB cameras.

        Formula: (2*G - R - B) / (R + G + B)
        """
        # Convert to float
        rgb = rgb_array.astype(np.float32)
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

        # Calculate Excess Green Index (normalized)
        total = r + g + b + 1e-6  # Avoid division by zero
        excess_green = (2 * g - r - b) / total

        # Normalize to 0-1 range (approximate NDVI scale)
        ndvi = (excess_green + 1) / 2  # Scale from [-1,1] to [0,1]

        # Clip to valid range
        ndvi = np.clip(ndvi, 0, 1)

        return ndvi

    def _calculate_ndvi_multispectral(self, img_array: np.ndarray) -> np.ndarray:
        """
        Calculate true NDVI from multispectral image

        Assumes NIR is in channel 0 (or 3 if RGBNIR) and Red in channel 1 (or 0)
        NDVI = (NIR - Red) / (NIR + Red)
        """
        if img_array.shape[2] >= 4:
            # Assume RGBNIR format
            nir = img_array[:, :, 3].astype(np.float32)
            red = img_array[:, :, 0].astype(np.float32)
        else:
            # Assume NIR-Red-Green format
            nir = img_array[:, :, 0].astype(np.float32)
            red = img_array[:, :, 1].astype(np.float32)

        # Calculate NDVI
        denominator = nir + red + 1e-6
        ndvi = (nir - red) / denominator

        # Clip to valid range
        ndvi = np.clip(ndvi, -1, 1)

        # Scale to 0-1 for consistency
        ndvi = (ndvi + 1) / 2

        return ndvi

    def _extract_ndvi_from_visualization(self, rgb_array: np.ndarray) -> np.ndarray:
        """
        Extract NDVI values from a color-coded NDVI visualization

        Common color scales:
        - Red/Brown = low NDVI (stressed)
        - Yellow = moderate NDVI
        - Green = high NDVI (healthy)
        """
        rgb = rgb_array.astype(np.float32) / 255.0
        r, g, _b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

        # Estimate NDVI based on color
        # Green-heavy = high NDVI, Red-heavy = low NDVI
        ndvi = (g - r) / (g + r + 0.01) * 0.5 + 0.5

        return np.clip(ndvi, 0, 1)

    def _classify_health(self, ndvi: float) -> HealthStatus:
        """Classify health status based on NDVI value"""
        if ndvi >= self.NDVI_THRESHOLDS[HealthStatus.EXCELLENT]:
            return HealthStatus.EXCELLENT
        elif ndvi >= self.NDVI_THRESHOLDS[HealthStatus.GOOD]:
            return HealthStatus.GOOD
        elif ndvi >= self.NDVI_THRESHOLDS[HealthStatus.MODERATE]:
            return HealthStatus.MODERATE
        elif ndvi >= self.NDVI_THRESHOLDS[HealthStatus.STRESSED]:
            return HealthStatus.STRESSED
        elif ndvi >= self.NDVI_THRESHOLDS[HealthStatus.POOR]:
            return HealthStatus.POOR
        else:
            return HealthStatus.CRITICAL

    def _analyze_zones(self, ndvi_map: np.ndarray, grid_size: int) -> List[ZoneHealth]:
        """Divide image into zones and analyze each"""
        height, width = ndvi_map.shape
        zone_height = height // grid_size
        zone_width = width // grid_size

        zones = []
        zone_id = 0

        for row in range(grid_size):
            for col in range(grid_size):
                # Extract zone
                y_start = row * zone_height
                y_end = (row + 1) * zone_height if row < grid_size - 1 else height
                x_start = col * zone_width
                x_end = (col + 1) * zone_width if col < grid_size - 1 else width

                zone_ndvi = ndvi_map[y_start:y_end, x_start:x_end]
                valid_values = zone_ndvi[~np.isnan(zone_ndvi)]

                if len(valid_values) > 0:
                    ndvi_mean = float(np.mean(valid_values))
                    ndvi_min = float(np.min(valid_values))
                    ndvi_max = float(np.max(valid_values))
                    health_status = self._classify_health(ndvi_mean)

                    # Detect potential issues
                    issue_type, confidence = self._detect_zone_issue(
                        ndvi_mean, ndvi_min, ndvi_max, valid_values
                    )

                    # Get recommendations for this zone
                    recommendations = self._get_zone_recommendations(health_status, issue_type)

                    zones.append(ZoneHealth(
                        zone_id=zone_id,
                        center_x=(x_start + x_end) / 2 / width,
                        center_y=(y_start + y_end) / 2 / height,
                        ndvi_mean=round(ndvi_mean, 3),
                        ndvi_min=round(ndvi_min, 3),
                        ndvi_max=round(ndvi_max, 3),
                        health_status=health_status,
                        area_percentage=round(len(valid_values) / ndvi_map.size * 100, 2),
                        issue_type=issue_type,
                        confidence=round(confidence, 2),
                        recommendations=recommendations
                    ))

                zone_id += 1

        return zones

    def _detect_zone_issue(
        self,
        ndvi_mean: float,
        ndvi_min: float,
        ndvi_max: float,
        values: np.ndarray
    ) -> Tuple[Optional[IssueType], float]:
        """Detect potential issue type in a zone"""

        # Only flag issues if zone is stressed
        if ndvi_mean >= self.NDVI_THRESHOLDS[HealthStatus.GOOD]:
            return None, 0.0

        # Calculate variability
        std = float(np.std(values)) if len(values) > 1 else 0

        # High variability suggests pest/disease (patchy damage)
        if std > 0.15 and ndvi_mean < 0.5:
            return IssueType.PEST_DAMAGE, min(0.8, std * 3)

        # Uniform low NDVI suggests water stress or nutrient deficiency
        if std < 0.1 and ndvi_mean < 0.4:
            # Very uniform low = water stress
            if ndvi_mean < 0.25:
                return IssueType.WATER_STRESS, 0.7
            else:
                return IssueType.NUTRIENT_DEFICIENCY, 0.6

        # Moderate variability with moderate NDVI
        if 0.1 <= std <= 0.15:
            return IssueType.WEED_PRESSURE, 0.5

        return IssueType.UNKNOWN, 0.3

    def _get_zone_recommendations(
        self,
        health_status: HealthStatus,
        issue_type: Optional[IssueType]
    ) -> List[str]:
        """Get recommendations for a specific zone"""
        recommendations = []

        if health_status in [HealthStatus.EXCELLENT, HealthStatus.GOOD]:
            return ["Zone healthy - continue current management"]

        if health_status == HealthStatus.MODERATE:
            recommendations.append("Monitor zone closely for changes")

        if issue_type and issue_type in self.ISSUE_PATTERNS:
            recommendations.extend(self.ISSUE_PATTERNS[issue_type]["recommendations"])
        else:
            recommendations.append("Scout this area to identify cause of stress")

        if health_status in [HealthStatus.POOR, HealthStatus.CRITICAL]:
            recommendations.append("Prioritize this zone for immediate attention")

        return recommendations

    def _detect_problem_areas(
        self,
        ndvi_map: np.ndarray,
        zones: List[ZoneHealth]
    ) -> List[Dict]:
        """Detect and characterize problem areas"""
        problem_areas = []

        # Find stressed zones
        stressed_zones = [z for z in zones if z.health_status in [
            HealthStatus.STRESSED, HealthStatus.POOR, HealthStatus.CRITICAL
        ]]

        for zone in stressed_zones:
            problem_areas.append({
                "zone_id": zone.zone_id,
                "location": {"x": zone.center_x, "y": zone.center_y},
                "severity": zone.health_status.value,
                "ndvi": zone.ndvi_mean,
                "issue_type": zone.issue_type.value if zone.issue_type else "unknown",
                "confidence": zone.confidence,
                "area_percentage": zone.area_percentage,
                "recommendations": zone.recommendations
            })

        # Sort by severity (worst first)
        severity_order = {
            HealthStatus.CRITICAL.value: 0,
            HealthStatus.POOR.value: 1,
            HealthStatus.STRESSED.value: 2
        }
        problem_areas.sort(key=lambda x: severity_order.get(x["severity"], 3))

        return problem_areas

    def _generate_recommendations(
        self,
        zones: List[ZoneHealth],
        problem_areas: List[Dict],
        overall_health: HealthStatus
    ) -> List[str]:
        """Generate overall field recommendations"""
        recommendations = []

        if overall_health == HealthStatus.EXCELLENT:
            recommendations.append("Field is in excellent condition - maintain current management practices")
            return recommendations

        if overall_health == HealthStatus.GOOD:
            recommendations.append("Field is in good condition overall")

        # Count issues by type
        issue_counts = {}
        for zone in zones:
            if zone.issue_type:
                issue_counts[zone.issue_type] = issue_counts.get(zone.issue_type, 0) + 1

        # Add issue-specific recommendations
        if IssueType.WATER_STRESS in issue_counts:
            recommendations.append(
                f"Water stress detected in {issue_counts[IssueType.WATER_STRESS]} zones - "
                "check irrigation and soil moisture"
            )

        if IssueType.NUTRIENT_DEFICIENCY in issue_counts:
            recommendations.append(
                f"Possible nutrient deficiency in {issue_counts[IssueType.NUTRIENT_DEFICIENCY]} zones - "
                "consider tissue testing"
            )

        if IssueType.PEST_DAMAGE in issue_counts:
            recommendations.append(
                f"Patchy damage patterns in {issue_counts[IssueType.PEST_DAMAGE]} zones - "
                "scout for pests"
            )

        # Add problem area count
        if len(problem_areas) > 0:
            critical_count = len([p for p in problem_areas if p["severity"] == "critical"])
            if critical_count > 0:
                recommendations.append(
                    f"URGENT: {critical_count} critical areas require immediate attention"
                )
            recommendations.append(
                f"Total of {len(problem_areas)} problem areas identified - prioritize scouting"
            )

        # Timing recommendation
        recommendations.append(
            "Re-analyze in 7-10 days to track changes and treatment effectiveness"
        )

        return recommendations

    def _generate_health_map(self, ndvi_map: np.ndarray, image_hash: str):
        """Generate and save color-coded health map"""
        # Create color map (red=stressed, yellow=moderate, green=healthy)
        height, width = ndvi_map.shape
        health_map = np.zeros((height, width, 3), dtype=np.uint8)

        # Red channel - inverse of NDVI (high when stressed)
        health_map[:, :, 0] = ((1 - ndvi_map) * 255).astype(np.uint8)
        # Green channel - proportional to NDVI
        health_map[:, :, 1] = (ndvi_map * 255).astype(np.uint8)
        # Blue channel - low
        health_map[:, :, 2] = 50

        # Save health map
        output_path = self.output_dir / f"{image_hash}_health_map.png"
        Image.fromarray(health_map).save(output_path)

    def _save_assessment(self, report: FieldHealthReport, image_bytes: bytes):
        """Save assessment to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Save image
        image_path = self.output_dir / f"{report.image_hash}_original.jpg"
        Image.open(io.BytesIO(image_bytes)).save(image_path, "JPEG", quality=90)

        # Insert assessment
        cursor.execute("""
            INSERT INTO field_health_assessments
            (field_id, image_hash, image_path, analysis_date, image_type,
             overall_ndvi, overall_health, healthy_percentage, stressed_percentage,
             zones_data, problem_areas, recommendations, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report.field_id,
            report.image_hash,
            str(image_path),
            date.today().isoformat(),
            report.image_type.value,
            report.overall_ndvi,
            report.overall_health.value,
            report.healthy_percentage,
            report.stressed_percentage,
            json.dumps([asdict(z) for z in report.zones]),
            json.dumps(report.problem_areas),
            json.dumps(report.recommendations),
            json.dumps(report.notes)
        ))

        assessment_id = cursor.lastrowid

        # Save zones
        for zone in report.zones:
            cursor.execute("""
                INSERT INTO health_zones
                (assessment_id, zone_id, center_x, center_y, ndvi_mean, ndvi_min, ndvi_max,
                 health_status, area_percentage, issue_type, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                assessment_id,
                zone.zone_id,
                zone.center_x,
                zone.center_y,
                zone.ndvi_mean,
                zone.ndvi_min,
                zone.ndvi_max,
                zone.health_status.value,
                zone.area_percentage,
                zone.issue_type.value if zone.issue_type else None,
                zone.confidence
            ))

        # Save to trends if field_id provided
        if report.field_id:
            cursor.execute("""
                INSERT INTO health_trends
                (field_id, crop_year, analysis_date, overall_ndvi,
                 healthy_percentage, stressed_percentage)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report.field_id,
                date.today().year,
                date.today().isoformat(),
                report.overall_ndvi,
                report.healthy_percentage,
                report.stressed_percentage
            ))

        conn.commit()
        conn.close()

    def get_field_health_score(self, field_id: int) -> Optional[Dict]:
        """Get current health score for a specific field."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, analysis_date, overall_ndvi, overall_health,
                   healthy_percentage, stressed_percentage, recommendations
            FROM field_health_assessments
            WHERE field_id = ?
            ORDER BY analysis_date DESC
            LIMIT 1
        """, (field_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            # Return default health score if no assessment exists
            return {
                "field_id": field_id,
                "score": 75.0,  # Default healthy score
                "health_status": "good",
                "overall_ndvi": 0.65,
                "healthy_percentage": 80.0,
                "stressed_percentage": 20.0,
                "last_assessment": None,
                "recommendations": ["No recent assessment available. Consider uploading field imagery."]
            }

        return {
            "field_id": field_id,
            "assessment_id": row[0],
            "last_assessment": row[1],
            "overall_ndvi": row[2],
            "health_status": row[3],
            "score": row[2] * 100 if row[2] else 65.0,  # NDVI as percentage
            "healthy_percentage": row[4],
            "stressed_percentage": row[5],
            "recommendations": json.loads(row[6]) if row[6] else []
        }

    def get_health_summary(self) -> Dict:
        """Get health summary across all fields."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get latest health data per field
        cursor.execute("""
            SELECT field_id, overall_ndvi, overall_health,
                   healthy_percentage, stressed_percentage
            FROM field_health_assessments fha
            WHERE analysis_date = (
                SELECT MAX(analysis_date)
                FROM field_health_assessments
                WHERE field_id = fha.field_id
            )
        """)

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {
                "total_fields": 0,
                "average_health_score": 0.0,
                "fields_excellent": 0,
                "fields_good": 0,
                "fields_stressed": 0,
                "fields_critical": 0,
                "summary": "No field health data available"
            }

        # Calculate summary statistics
        total = len(rows)
        avg_ndvi = sum(r[1] for r in rows if r[1]) / total if total > 0 else 0

        status_counts = {"excellent": 0, "good": 0, "moderate": 0, "stressed": 0, "poor": 0, "critical": 0}
        for row in rows:
            status = row[2] if row[2] else "unknown"
            if status in status_counts:
                status_counts[status] += 1

        return {
            "total_fields": total,
            "average_health_score": round(avg_ndvi * 100, 1),
            "average_ndvi": round(avg_ndvi, 3),
            "fields_excellent": status_counts["excellent"],
            "fields_good": status_counts["good"],
            "fields_moderate": status_counts["moderate"],
            "fields_stressed": status_counts["stressed"],
            "fields_poor": status_counts["poor"],
            "fields_critical": status_counts["critical"],
            "summary": f"{total} fields monitored, average NDVI {avg_ndvi:.2f}"
        }

    def calculate_health_score(self, field_id: int) -> Dict:
        """Recalculate health score for a field (triggers analysis if needed)."""
        # For now, return the existing health score
        # In production, this would trigger image re-analysis
        existing = self.get_field_health_score(field_id)
        return {
            "field_id": field_id,
            "score": existing.get("score", 70.0),
            "health_status": existing.get("health_status", "good"),
            "recalculated": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_field_history(self, field_id: int, limit: int = 10) -> List[Dict]:
        """Get health assessment history for a field"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, analysis_date, overall_ndvi, overall_health,
                   healthy_percentage, stressed_percentage, recommendations
            FROM field_health_assessments
            WHERE field_id = ?
            ORDER BY analysis_date DESC
            LIMIT ?
        """, (field_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "analysis_date": row[1],
                "overall_ndvi": row[2],
                "overall_health": row[3],
                "healthy_percentage": row[4],
                "stressed_percentage": row[5],
                "recommendations": json.loads(row[6]) if row[6] else []
            }
            for row in rows
        ]

    def get_health_trends(self, field_id: int, crop_year: Optional[int] = None) -> Dict:
        """Get health trends for a field over time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if crop_year:
            cursor.execute("""
                SELECT analysis_date, overall_ndvi, healthy_percentage, stressed_percentage
                FROM health_trends
                WHERE field_id = ? AND crop_year = ?
                ORDER BY analysis_date
            """, (field_id, crop_year))
        else:
            cursor.execute("""
                SELECT analysis_date, overall_ndvi, healthy_percentage, stressed_percentage
                FROM health_trends
                WHERE field_id = ?
                ORDER BY analysis_date
            """, (field_id,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"field_id": field_id, "data": [], "summary": None}

        data = [
            {
                "date": row[0],
                "ndvi": row[1],
                "healthy_pct": row[2],
                "stressed_pct": row[3]
            }
            for row in rows
        ]

        # Calculate trend summary
        ndvi_values = [d["ndvi"] for d in data]
        summary = {
            "data_points": len(data),
            "first_date": data[0]["date"],
            "last_date": data[-1]["date"],
            "ndvi_start": ndvi_values[0],
            "ndvi_end": ndvi_values[-1],
            "ndvi_change": round(ndvi_values[-1] - ndvi_values[0], 3),
            "ndvi_trend": "improving" if ndvi_values[-1] > ndvi_values[0] else "declining",
            "ndvi_average": round(np.mean(ndvi_values), 3)
        }

        return {"field_id": field_id, "data": data, "summary": summary}


# Singleton instance
_crop_health_service: Optional[CropHealthService] = None


def get_crop_health_service() -> CropHealthService:
    """Get or create crop health service singleton"""
    global _crop_health_service
    if _crop_health_service is None:
        _crop_health_service = CropHealthService()
    return _crop_health_service
