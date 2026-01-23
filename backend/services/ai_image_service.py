"""
AI Image Service - Hybrid Cloud + Local Model Architecture
Phase 1 of AgTools AI/ML Intelligence Suite (v3.0)

Features:
- Cloud API integration (Hugging Face Inference API - free tier)
- Local TensorFlow model inference (when trained model available)
- Training data collection pipeline
- Integration with existing pest/disease knowledge base
- Confidence scoring with top-N predictions
"""

import os
import io
import json
import base64
import hashlib
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import httpx
from PIL import Image
import numpy as np

# Import existing knowledge base
import sys
# Add both backend and project root to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

try:
    from database.seed_data import CORN_PESTS, SOYBEAN_PESTS, CORN_DISEASES, SOYBEAN_DISEASES
except ImportError:
    # Fallback if running from different context
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "seed_data",
            os.path.join(project_root, "database", "seed_data.py")
        )
        seed_data = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(seed_data)
        CORN_PESTS = seed_data.CORN_PESTS
        SOYBEAN_PESTS = seed_data.SOYBEAN_PESTS
        CORN_DISEASES = seed_data.CORN_DISEASES
        SOYBEAN_DISEASES = seed_data.SOYBEAN_DISEASES
    except Exception as e:
        # Use empty lists if all else fails
        print(f"Warning: Could not load seed data: {e}")
        CORN_PESTS = []
        SOYBEAN_PESTS = []
        CORN_DISEASES = []
        SOYBEAN_DISEASES = []


class IdentificationType(str, Enum):
    PEST = "pest"
    DISEASE = "disease"
    WEED = "weed"
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    UNKNOWN = "unknown"


class AIProvider(str, Enum):
    HUGGINGFACE = "huggingface"
    GOOGLE_VISION = "google_vision"
    AWS_REKOGNITION = "aws_rekognition"
    LOCAL_MODEL = "local_model"
    OFFLINE = "offline"


@dataclass
class ImageAnalysisResult:
    """Result from AI image analysis"""
    provider: AIProvider
    raw_labels: List[Dict]  # Raw labels from AI provider
    mapped_identifications: List[Dict]  # Mapped to our knowledge base
    confidence: float
    processing_time_ms: int
    image_hash: str
    notes: List[str]


class AIImageService:
    """
    Hybrid AI Image Analysis Service

    Uses cloud APIs for immediate results, with ability to switch to
    local model when trained. Collects training data for model improvement.
    """

    # Hugging Face models for plant/agriculture analysis
    HF_MODELS = {
        "plant_disease": "ozair23/mobilenet_v2_1.0_224-finetuned-plantdisease",
        "general_image": "google/vit-base-patch16-224",
        "plant_species": "microsoft/resnet-50",
    }

    # Mapping of common AI labels to our knowledge base
    LABEL_MAPPINGS = {
        # Pest-related labels
        "aphid": ["aphid", "corn leaf aphid", "soybean aphid"],
        "beetle": ["japanese beetle", "bean leaf beetle", "flea beetle"],
        "caterpillar": ["armyworm", "corn borer", "cutworm", "webworm"],
        "worm": ["rootworm", "wireworm", "armyworm"],
        "mite": ["spider mite", "spider mites"],
        "bug": ["stink bug", "plant bug"],

        # Disease-related labels
        "rust": ["rust", "common rust", "southern rust"],
        "blight": ["northern corn leaf blight", "southern corn leaf blight", "bacterial blight"],
        "spot": ["gray leaf spot", "tar spot", "brown spot", "frogeye leaf spot"],
        "mold": ["white mold", "gray mold"],
        "rot": ["stalk rot", "root rot", "ear rot"],
        "wilt": ["bacterial wilt", "goss's wilt", "sudden death syndrome"],

        # Nutrient deficiency labels
        "yellow": ["nitrogen deficiency", "sulfur deficiency", "iron deficiency"],
        "purple": ["phosphorus deficiency"],
        "brown_edges": ["potassium deficiency"],
    }

    def __init__(self,
                 hf_api_key: Optional[str] = None,
                 google_api_key: Optional[str] = None,
                 db_path: str = "agtools.db",
                 models_dir: str = "models",
                 training_data_dir: str = "training_data"):
        """
        Initialize AI Image Service

        Args:
            hf_api_key: Hugging Face API key (optional, uses free tier if None)
            google_api_key: Google Cloud Vision API key (optional)
            db_path: Path to SQLite database
            models_dir: Directory for local models
            training_data_dir: Directory for training data collection
        """
        self.hf_api_key = hf_api_key or os.environ.get("HUGGINGFACE_API_KEY", "")
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_VISION_API_KEY", "")
        self.db_path = db_path
        self.models_dir = Path(models_dir)
        self.training_data_dir = Path(training_data_dir)

        # Create directories if needed
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.training_data_dir.mkdir(parents=True, exist_ok=True)

        # Build knowledge base lookup
        self._build_knowledge_base()

        # Initialize database tables for training data
        self._init_db()

        # Check for local trained model
        self.local_model = None
        self._load_local_model()

    def _build_knowledge_base(self):
        """Build searchable knowledge base from seed data"""
        self.knowledge_base = {
            "corn": {
                "pests": {p["common_name"].lower(): p for p in CORN_PESTS},
                "diseases": {d["common_name"].lower(): d for d in CORN_DISEASES}
            },
            "soybean": {
                "pests": {p["common_name"].lower(): p for p in SOYBEAN_PESTS},
                "diseases": {d["common_name"].lower(): d for d in SOYBEAN_DISEASES}
            }
        }

        # Build reverse lookup for keywords
        self.keyword_lookup = {}
        for crop in ["corn", "soybean"]:
            for category in ["pests", "diseases"]:
                for name, data in self.knowledge_base[crop][category].items():
                    # Index by common name words
                    for word in name.split():
                        word = word.lower().strip("()")
                        if word not in self.keyword_lookup:
                            self.keyword_lookup[word] = []
                        self.keyword_lookup[word].append({
                            "crop": crop,
                            "type": category[:-1],  # pest or disease
                            "name": name,
                            "data": data
                        })

    def _init_db(self):
        """Initialize database tables for AI training data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Training images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_training_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_hash TEXT UNIQUE NOT NULL,
                file_path TEXT NOT NULL,
                crop TEXT NOT NULL,
                growth_stage TEXT,
                identification_type TEXT NOT NULL,
                label TEXT NOT NULL,
                confidence REAL,
                verified BOOLEAN DEFAULT FALSE,
                verified_by_user_id INTEGER,
                verified_at TIMESTAMP,
                ai_provider TEXT,
                ai_raw_response TEXT,
                notes TEXT,
                latitude REAL,
                longitude REAL,
                captured_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # AI predictions log (for model improvement)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_hash TEXT NOT NULL,
                provider TEXT NOT NULL,
                model_name TEXT,
                prediction_label TEXT NOT NULL,
                confidence REAL,
                mapped_to TEXT,
                user_feedback TEXT,
                is_correct BOOLEAN,
                processing_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_hash) REFERENCES ai_training_images(image_hash)
            )
        """)

        # Model versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                version TEXT NOT NULL,
                crop TEXT,
                model_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                training_images_count INTEGER,
                accuracy REAL,
                classes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)

        conn.commit()
        conn.close()

    def _load_local_model(self):
        """Load local TensorFlow model if available"""
        # Check for crop-specific models
        model_files = list(self.models_dir.glob("*.h5")) + list(self.models_dir.glob("*.keras"))

        if model_files:
            try:
                import tensorflow as tf
                # Load most recent model
                model_path = sorted(model_files, key=lambda x: x.stat().st_mtime)[-1]
                self.local_model = tf.keras.models.load_model(str(model_path))
                self.local_model_path = model_path
                print(f"Loaded local model: {model_path.name}")
            except Exception as e:
                print(f"Could not load local model: {e}")
                self.local_model = None

    def _hash_image(self, image_bytes: bytes) -> str:
        """Generate hash for image deduplication"""
        return hashlib.sha256(image_bytes).hexdigest()[:16]

    def _preprocess_image(self, image_bytes: bytes, target_size: Tuple[int, int] = (224, 224)) -> Image.Image:
        """Preprocess image for model input"""
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize maintaining aspect ratio
        image.thumbnail(target_size, Image.Resampling.LANCZOS)

        # Create square canvas and paste
        canvas = Image.new("RGB", target_size, (255, 255, 255))
        offset = ((target_size[0] - image.width) // 2, (target_size[1] - image.height) // 2)
        canvas.paste(image, offset)

        return canvas

    async def analyze_image(
        self,
        image_bytes: bytes,
        crop: str,
        growth_stage: Optional[str] = None,
        use_local_model: bool = True,
        save_for_training: bool = True
    ) -> ImageAnalysisResult:
        """
        Analyze image using hybrid AI approach

        Args:
            image_bytes: Raw image bytes
            crop: Crop type (corn, soybean, wheat, etc.)
            growth_stage: Current growth stage (optional)
            use_local_model: Use local model if available
            save_for_training: Save image for training data collection

        Returns:
            ImageAnalysisResult with identifications and confidence scores
        """
        import time
        start_time = time.time()

        image_hash = self._hash_image(image_bytes)
        notes = []

        # Try local model first if available and requested
        if use_local_model and self.local_model is not None:
            try:
                result = await self._analyze_with_local_model(image_bytes, crop)
                result.image_hash = image_hash
                notes.append("Analyzed with local trained model")

                if save_for_training:
                    self._save_prediction(image_hash, result)

                return result
            except Exception as e:
                notes.append(f"Local model failed: {str(e)}, falling back to cloud API")

        # Try Hugging Face API
        try:
            result = await self._analyze_with_huggingface(image_bytes, crop)
            result.image_hash = image_hash
            notes.extend(result.notes)
            notes.append("Analyzed with Hugging Face API")

            if save_for_training:
                self._save_prediction(image_hash, result)
                self._save_training_image(image_bytes, image_hash, crop, growth_stage, result)

            processing_time = int((time.time() - start_time) * 1000)
            result.processing_time_ms = processing_time
            result.notes = notes

            return result

        except Exception as e:
            notes.append(f"Cloud API failed: {str(e)}")

        # Fallback to offline symptom-based matching
        notes.append("Using offline mode - symptom-based matching only")
        return ImageAnalysisResult(
            provider=AIProvider.OFFLINE,
            raw_labels=[],
            mapped_identifications=self._get_common_issues(crop),
            confidence=0.0,
            processing_time_ms=int((time.time() - start_time) * 1000),
            image_hash=image_hash,
            notes=notes
        )

    async def _analyze_with_huggingface(self, image_bytes: bytes, crop: str) -> ImageAnalysisResult:
        """Analyze image using Hugging Face Inference API"""

        # Encode image as base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        headers = {}
        if self.hf_api_key:
            headers["Authorization"] = f"Bearer {self.hf_api_key}"

        raw_labels = []

        # Try plant disease model first
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                model_id = self.HF_MODELS["plant_disease"]
                response = await client.post(
                    f"https://api-inference.huggingface.co/models/{model_id}",
                    headers=headers,
                    json={"inputs": image_base64},
                )

                if response.status_code == 200:
                    results = response.json()
                    if isinstance(results, list):
                        raw_labels = [{"label": r.get("label", ""), "score": r.get("score", 0)} for r in results[:10]]
            except Exception:
                # Try general image model as fallback
                try:
                    model_id = self.HF_MODELS["general_image"]
                    response = await client.post(
                        f"https://api-inference.huggingface.co/models/{model_id}",
                        headers=headers,
                        json={"inputs": image_base64},
                    )

                    if response.status_code == 200:
                        results = response.json()
                        if isinstance(results, list):
                            raw_labels = [{"label": r.get("label", ""), "score": r.get("score", 0)} for r in results[:10]]
                except (ValueError, KeyError, TypeError, Exception):
                    # Log error but continue with fallback
                    pass

        # Map raw labels to our knowledge base
        mapped = self._map_labels_to_knowledge_base(raw_labels, crop)

        # Calculate overall confidence
        confidence = max([m["confidence"] for m in mapped]) if mapped else 0.0

        return ImageAnalysisResult(
            provider=AIProvider.HUGGINGFACE,
            raw_labels=raw_labels,
            mapped_identifications=mapped,
            confidence=confidence,
            processing_time_ms=0,  # Will be set by caller
            image_hash="",  # Will be set by caller
            notes=["Used Hugging Face plant disease model"]
        )

    async def _analyze_with_local_model(self, image_bytes: bytes, crop: str) -> ImageAnalysisResult:
        """Analyze image using local TensorFlow model"""

        # Preprocess image
        image = self._preprocess_image(image_bytes)
        image_array = np.array(image) / 255.0
        image_array = np.expand_dims(image_array, axis=0)

        # Run inference
        predictions = self.local_model.predict(image_array)

        # Get class labels (stored with model or in separate file)
        class_labels = self._get_model_classes()

        # Get top predictions
        top_indices = np.argsort(predictions[0])[-5:][::-1]
        raw_labels = [
            {"label": class_labels[i] if i < len(class_labels) else f"class_{i}",
             "score": float(predictions[0][i])}
            for i in top_indices
        ]

        # Map to knowledge base
        mapped = self._map_labels_to_knowledge_base(raw_labels, crop)

        return ImageAnalysisResult(
            provider=AIProvider.LOCAL_MODEL,
            raw_labels=raw_labels,
            mapped_identifications=mapped,
            confidence=max([m["confidence"] for m in mapped]) if mapped else 0.0,
            processing_time_ms=0,
            image_hash="",
            notes=[f"Used local model: {self.local_model_path.name}"]
        )

    def _get_model_classes(self) -> List[str]:
        """Get class labels for local model"""
        # Try to load from classes.json
        classes_file = self.models_dir / "classes.json"
        if classes_file.exists():
            with open(classes_file) as f:
                return json.load(f)

        # Default classes based on our knowledge base
        return list(self.keyword_lookup.keys())

    def _map_labels_to_knowledge_base(self, raw_labels: List[Dict], crop: str) -> List[Dict]:
        """Map AI labels to our pest/disease knowledge base"""
        mapped = []
        seen = set()

        for label_data in raw_labels:
            label = label_data.get("label", "").lower()
            score = label_data.get("score", 0)

            # Check for direct matches in knowledge base
            matches = self._find_knowledge_base_matches(label, crop)

            for match in matches:
                if match["name"] not in seen:
                    seen.add(match["name"])
                    mapped.append({
                        "type": match["type"],
                        "name": match["data"]["common_name"],
                        "scientific_name": match["data"].get("scientific_name", ""),
                        "confidence": round(score * 100, 1),
                        "description": match["data"].get("description", ""),
                        "damage_symptoms": match["data"].get("damage_symptoms", ""),
                        "economic_threshold": match["data"].get("economic_threshold", ""),
                        "management_notes": match["data"].get("management_notes", ""),
                        "raw_label": label,
                        "crop": crop
                    })

        # Sort by confidence
        mapped.sort(key=lambda x: x["confidence"], reverse=True)

        # Return top 5
        return mapped[:5]

    def _find_knowledge_base_matches(self, label: str, crop: str) -> List[Dict]:
        """Find matches in knowledge base for a label"""
        matches = []
        label_lower = label.lower()

        # Check label mappings
        for keyword, possible_names in self.LABEL_MAPPINGS.items():
            if keyword in label_lower:
                for name in possible_names:
                    if name.lower() in self.keyword_lookup:
                        for match in self.keyword_lookup[name.lower()]:
                            if match["crop"] == crop.lower() or crop.lower() == "all":
                                matches.append(match)

        # Direct keyword search
        for word in label_lower.split():
            word = word.strip("_-()[]")
            if len(word) > 2 and word in self.keyword_lookup:
                for match in self.keyword_lookup[word]:
                    if match["crop"] == crop.lower() or crop.lower() == "all":
                        if match not in matches:
                            matches.append(match)

        return matches

    def _get_common_issues(self, crop: str) -> List[Dict]:
        """Get common issues for a crop when AI is unavailable"""
        common = []

        if crop.lower() in self.knowledge_base:
            # Add top pests
            for name, data in list(self.knowledge_base[crop.lower()]["pests"].items())[:3]:
                common.append({
                    "type": "pest",
                    "name": data["common_name"],
                    "scientific_name": data.get("scientific_name", ""),
                    "confidence": 0,
                    "description": data.get("description", ""),
                    "note": "Common pest in this crop - verify visually"
                })

            # Add top diseases
            for name, data in list(self.knowledge_base[crop.lower()]["diseases"].items())[:3]:
                common.append({
                    "type": "disease",
                    "name": data["common_name"],
                    "scientific_name": data.get("scientific_name", ""),
                    "confidence": 0,
                    "description": data.get("description", ""),
                    "note": "Common disease in this crop - verify visually"
                })

        return common

    def _save_training_image(self, image_bytes: bytes, image_hash: str, crop: str,
                             growth_stage: Optional[str], result: ImageAnalysisResult):
        """Save image for training data collection"""
        # Save image file
        image_dir = self.training_data_dir / crop
        image_dir.mkdir(parents=True, exist_ok=True)

        image_path = image_dir / f"{image_hash}.jpg"

        # Save as JPEG
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(image_path, "JPEG", quality=90)

        # Save metadata to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get top identification
        top_id = result.mapped_identifications[0] if result.mapped_identifications else None

        cursor.execute("""
            INSERT OR REPLACE INTO ai_training_images
            (image_hash, file_path, crop, growth_stage, identification_type, label,
             confidence, ai_provider, ai_raw_response, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            image_hash,
            str(image_path),
            crop,
            growth_stage,
            top_id["type"] if top_id else "unknown",
            top_id["name"] if top_id else "unknown",
            top_id["confidence"] if top_id else 0,
            result.provider.value,
            json.dumps(result.raw_labels),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def _save_prediction(self, image_hash: str, result: ImageAnalysisResult):
        """Save prediction for model improvement tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for mapped in result.mapped_identifications[:3]:
            cursor.execute("""
                INSERT INTO ai_predictions
                (image_hash, provider, prediction_label, confidence, mapped_to, processing_time_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                image_hash,
                result.provider.value,
                mapped.get("raw_label", ""),
                mapped["confidence"],
                mapped["name"],
                result.processing_time_ms
            ))

        conn.commit()
        conn.close()

    def submit_feedback(self, image_hash: str, is_correct: bool,
                        correct_label: Optional[str] = None, user_id: Optional[int] = None) -> bool:
        """
        Submit user feedback on AI prediction

        Args:
            image_hash: Hash of the analyzed image
            is_correct: Whether the top prediction was correct
            correct_label: The correct identification if wrong
            user_id: User submitting feedback

        Returns:
            Success status
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Update prediction feedback
            cursor.execute("""
                UPDATE ai_predictions
                SET is_correct = ?, user_feedback = ?
                WHERE image_hash = ?
            """, (is_correct, correct_label, image_hash))

            # If correction provided, update training image
            if correct_label:
                cursor.execute("""
                    UPDATE ai_training_images
                    SET label = ?, verified = TRUE, verified_by_user_id = ?,
                        verified_at = ?, updated_at = ?
                    WHERE image_hash = ?
                """, (correct_label, user_id, datetime.now().isoformat(),
                      datetime.now().isoformat(), image_hash))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error saving feedback: {e}")
            return False
        finally:
            conn.close()

    def get_training_stats(self) -> Dict:
        """Get statistics about collected training data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total images
        cursor.execute("SELECT COUNT(*) FROM ai_training_images")
        total_images = cursor.fetchone()[0]

        # Verified images
        cursor.execute("SELECT COUNT(*) FROM ai_training_images WHERE verified = TRUE")
        verified_images = cursor.fetchone()[0]

        # By crop
        cursor.execute("""
            SELECT crop, COUNT(*) as count
            FROM ai_training_images
            GROUP BY crop
        """)
        by_crop = dict(cursor.fetchall())

        # By identification type
        cursor.execute("""
            SELECT identification_type, COUNT(*) as count
            FROM ai_training_images
            GROUP BY identification_type
        """)
        by_type = dict(cursor.fetchall())

        # Prediction accuracy (from feedback)
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN is_correct = TRUE THEN 1 END) as correct,
                COUNT(*) as total
            FROM ai_predictions
            WHERE is_correct IS NOT NULL
        """)
        accuracy_data = cursor.fetchone()

        conn.close()

        return {
            "total_images": total_images,
            "verified_images": verified_images,
            "unverified_images": total_images - verified_images,
            "by_crop": by_crop,
            "by_type": by_type,
            "prediction_accuracy": {
                "correct": accuracy_data[0] if accuracy_data else 0,
                "total": accuracy_data[1] if accuracy_data else 0,
                "percentage": round(accuracy_data[0] / accuracy_data[1] * 100, 1)
                              if accuracy_data and accuracy_data[1] > 0 else 0
            },
            "ready_for_training": verified_images >= 100,
            "recommendation": self._get_training_recommendation(total_images, verified_images)
        }

    def _get_training_recommendation(self, total: int, verified: int) -> str:
        """Get recommendation based on training data status"""
        if total < 50:
            return "Keep collecting images. Need at least 100 verified images per class for training."
        elif verified < 100:
            return f"Have {total} images, but only {verified} verified. Review and verify more images."
        elif verified < 500:
            return "Ready for initial training. More data will improve accuracy."
        else:
            return "Excellent dataset. Ready for full model training with good expected accuracy."

    def export_training_data(self, output_dir: str, crop: Optional[str] = None) -> Dict:
        """
        Export training data for model training

        Args:
            output_dir: Directory to export to
            crop: Optional crop filter

        Returns:
            Export statistics
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT image_hash, file_path, crop, identification_type, label
            FROM ai_training_images
            WHERE verified = TRUE
        """
        params = []

        if crop:
            query += " AND crop = ?"
            params.append(crop)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Organize by label
        by_label = {}
        for row in rows:
            image_hash, file_path, crop, id_type, label = row
            if label not in by_label:
                by_label[label] = []
            by_label[label].append({
                "hash": image_hash,
                "path": file_path,
                "crop": crop,
                "type": id_type
            })

        # Create label directories and copy images
        import shutil
        exported = 0

        for label, images in by_label.items():
            label_dir = output_path / label.replace(" ", "_").lower()
            label_dir.mkdir(exist_ok=True)

            for img in images:
                src = Path(img["path"])
                if src.exists():
                    dst = label_dir / f"{img['hash']}.jpg"
                    shutil.copy2(src, dst)
                    exported += 1

        # Save labels manifest
        manifest = {
            "labels": list(by_label.keys()),
            "image_count": exported,
            "by_label": {k: len(v) for k, v in by_label.items()},
            "exported_at": datetime.now().isoformat()
        }

        with open(output_path / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

        return manifest


# Singleton instance
_ai_image_service: Optional[AIImageService] = None


def get_ai_image_service() -> AIImageService:
    """Get or create AI image service singleton"""
    global _ai_image_service
    if _ai_image_service is None:
        _ai_image_service = AIImageService()
    return _ai_image_service
