"""
Smart Expense Categorization Service
Phase 4 of AgTools AI/ML Intelligence Suite (v3.0)

Features:
- Auto-categorize expenses from descriptions
- Learn from user corrections over time
- Improve QuickBooks import accuracy
- Vendor recognition and pattern matching
- Confidence scoring for categorizations
"""

import os
import re
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from collections import Counter

import numpy as np

# Try to import sklearn for ML-based categorization
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    import pickle
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("scikit-learn not available - using rule-based categorization")


class ExpenseCategory(str, Enum):
    """Farm expense categories"""
    SEED = "seed"
    FERTILIZER = "fertilizer"
    CHEMICAL = "chemical"
    FUEL = "fuel"
    REPAIRS = "repairs"
    LABOR = "labor"
    CUSTOM_HIRE = "custom_hire"
    LAND_RENT = "land_rent"
    CROP_INSURANCE = "crop_insurance"
    UTILITIES = "utilities"
    IRRIGATION = "irrigation"
    DRYING_STORAGE = "drying_storage"
    EQUIPMENT = "equipment"
    INTEREST = "interest"
    TAXES = "taxes"
    SUPPLIES = "supplies"
    PROFESSIONAL = "professional"
    TRUCKING = "trucking"
    OTHER = "other"


@dataclass
class CategorizationResult:
    """Result of expense categorization"""
    description: str
    predicted_category: ExpenseCategory
    confidence: float
    alternative_categories: List[Tuple[ExpenseCategory, float]]
    matching_rules: List[str]
    vendor_recognized: bool
    vendor_category_history: Optional[str]


# Keyword rules for rule-based categorization
CATEGORY_KEYWORDS = {
    ExpenseCategory.SEED: [
        'seed', 'seeds', 'corn seed', 'soybean seed', 'wheat seed',
        'pioneer', 'dekalb', 'asgrow', 'channel', 'beck', 'golden harvest',
        'seed treatment', 'planting seed', 'certified seed'
    ],
    ExpenseCategory.FERTILIZER: [
        'fertilizer', 'fert', 'nitrogen', 'urea', 'anhydrous', 'ammonia',
        'uan', '28-0-0', '32-0-0', 'dap', 'map', 'potash', 'phosphate',
        'starter', 'lime', 'gypsum', 'sulfur', 'micronutrients', 'foliar',
        'nutrien', 'cargill', 'mosaic', 'cf industries'
    ],
    ExpenseCategory.CHEMICAL: [
        'chemical', 'herbicide', 'pesticide', 'fungicide', 'insecticide',
        'roundup', 'glyphosate', 'liberty', 'dicamba', 'atrazine',
        'warrant', 'dual', 'prowl', 'chlorpyrifos', 'bifenthrin',
        'spraying', 'spray', 'application', 'syngenta', 'basf', 'bayer',
        'corteva', 'fmc', 'adama'
    ],
    ExpenseCategory.FUEL: [
        'fuel', 'diesel', 'gas', 'gasoline', 'def', 'petroleum',
        'fill up', 'fuel purchase', 'bulk fuel', 'fuel tank',
        'casey', 'kum & go', 'cenex', 'sinclair', 'phillips 66'
    ],
    ExpenseCategory.REPAIRS: [
        'repair', 'repairs', 'parts', 'maintenance', 'service',
        'fix', 'rebuilt', 'replace', 'bearing', 'belt', 'hydraulic',
        'oil change', 'filter', 'tire', 'battery', 'alternator',
        'john deere', 'case ih', 'agco', 'napa', 'o\'reilly'
    ],
    ExpenseCategory.LABOR: [
        'labor', 'wages', 'salary', 'payroll', 'employee', 'worker',
        'hired hand', 'overtime', 'bonus', 'hourly'
    ],
    ExpenseCategory.CUSTOM_HIRE: [
        'custom', 'custom hire', 'custom work', 'custom spraying',
        'custom harvest', 'custom hauling', 'custom planting',
        'aerial', 'flying', 'drone', 'applicator'
    ],
    ExpenseCategory.LAND_RENT: [
        'rent', 'land rent', 'cash rent', 'lease', 'landlord',
        'farm rent', 'crop share'
    ],
    ExpenseCategory.CROP_INSURANCE: [
        'insurance', 'crop insurance', 'hail insurance', 'premium',
        'crop hail', 'multi-peril', 'rma', 'crop ins'
    ],
    ExpenseCategory.UTILITIES: [
        'utility', 'utilities', 'electric', 'electricity', 'power',
        'phone', 'internet', 'water', 'natural gas', 'propane'
    ],
    ExpenseCategory.IRRIGATION: [
        'irrigation', 'pivot', 'center pivot', 'drip', 'water rights',
        'pump', 'well', 'irrigation repair', 'nozzle'
    ],
    ExpenseCategory.DRYING_STORAGE: [
        'drying', 'storage', 'grain bin', 'elevator', 'grain storage',
        'shrink', 'handling', 'grain drying', 'propane drying'
    ],
    ExpenseCategory.EQUIPMENT: [
        'equipment', 'machinery', 'tractor', 'combine', 'planter',
        'sprayer', 'tillage', 'implement', 'purchase', 'down payment'
    ],
    ExpenseCategory.INTEREST: [
        'interest', 'loan', 'finance', 'financing', 'note',
        'operating loan', 'line of credit'
    ],
    ExpenseCategory.TAXES: [
        'tax', 'taxes', 'property tax', 'real estate tax'
    ],
    ExpenseCategory.SUPPLIES: [
        'supplies', 'office', 'twine', 'wire', 'marker', 'flag',
        'tape', 'gloves', 'ppe', 'safety'
    ],
    ExpenseCategory.PROFESSIONAL: [
        'accounting', 'legal', 'consultant', 'advisor', 'cpa',
        'attorney', 'professional', 'agronomist', 'fee'
    ],
    ExpenseCategory.TRUCKING: [
        'trucking', 'hauling', 'freight', 'shipping', 'transport',
        'semi', 'grain hauling'
    ]
}

# Vendor to category mappings (learned from historical data)
DEFAULT_VENDOR_MAPPINGS = {
    # Seed companies
    'pioneer': ExpenseCategory.SEED,
    'dekalb': ExpenseCategory.SEED,
    'asgrow': ExpenseCategory.SEED,
    'channel': ExpenseCategory.SEED,
    'beck': ExpenseCategory.SEED,
    'golden harvest': ExpenseCategory.SEED,

    # Fertilizer companies
    'nutrien': ExpenseCategory.FERTILIZER,
    'cf industries': ExpenseCategory.FERTILIZER,
    'mosaic': ExpenseCategory.FERTILIZER,
    'cargill fertilizer': ExpenseCategory.FERTILIZER,

    # Chemical companies
    'syngenta': ExpenseCategory.CHEMICAL,
    'basf': ExpenseCategory.CHEMICAL,
    'bayer': ExpenseCategory.CHEMICAL,
    'corteva': ExpenseCategory.CHEMICAL,
    'fmc': ExpenseCategory.CHEMICAL,

    # Fuel
    'casey': ExpenseCategory.FUEL,
    'kum & go': ExpenseCategory.FUEL,
    'cenex': ExpenseCategory.FUEL,
    'sinclair': ExpenseCategory.FUEL,

    # Equipment dealers
    'john deere': ExpenseCategory.REPAIRS,
    'case ih': ExpenseCategory.REPAIRS,
    'agco': ExpenseCategory.REPAIRS,
    'titan machinery': ExpenseCategory.REPAIRS,
    'murphy tractor': ExpenseCategory.REPAIRS,

    # Parts stores
    'napa': ExpenseCategory.REPAIRS,
    'o\'reilly': ExpenseCategory.REPAIRS,
    'autozone': ExpenseCategory.REPAIRS,
    'fastenal': ExpenseCategory.SUPPLIES,
}


class ExpenseCategorizationService:
    """
    Smart Expense Categorization Service

    Uses ML and rule-based approaches to automatically categorize
    farm expenses. Learns from user corrections to improve over time.
    """

    def __init__(self, db_path: str = "agtools.db", model_path: str = "models/expense_categorizer.pkl"):
        """
        Initialize Expense Categorization Service

        Args:
            db_path: Path to SQLite database
            model_path: Path to save/load trained model
        """
        self.db_path = db_path
        self.model_path = model_path
        self.model = None
        self.vectorizer = None
        self.vendor_mappings = DEFAULT_VENDOR_MAPPINGS.copy()

        self._init_db()
        self._load_model()
        self._load_vendor_mappings()

    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Categorization training data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expense_categorization_training (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                vendor TEXT,
                amount REAL,
                category TEXT NOT NULL,
                source TEXT,
                user_corrected BOOLEAN DEFAULT FALSE,
                created_by_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Vendor category mappings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendor_category_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_pattern TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                occurrence_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Categorization log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorization_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                vendor TEXT,
                predicted_category TEXT NOT NULL,
                confidence REAL,
                method TEXT,
                user_corrected_to TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def _load_model(self):
        """Load trained ML model if available"""
        if HAS_SKLEARN and os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    saved = pickle.load(f)
                    self.model = saved.get('model')
                    self.vectorizer = saved.get('vectorizer')
                print("Loaded expense categorization model")
            except Exception as e:
                print(f"Failed to load model: {e}")

    def _load_vendor_mappings(self):
        """Load vendor mappings from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT vendor_pattern, category, confidence
            FROM vendor_category_mappings
            WHERE confidence >= 0.7
        """)

        for row in cursor.fetchall():
            try:
                self.vendor_mappings[row[0].lower()] = ExpenseCategory(row[1])
            except ValueError:
                pass

        conn.close()

    def categorize(
        self,
        description: str,
        vendor: Optional[str] = None,
        amount: Optional[float] = None,
        use_ml: bool = True
    ) -> CategorizationResult:
        """
        Categorize an expense

        Args:
            description: Expense description text
            vendor: Optional vendor name
            amount: Optional amount (can help with some categorizations)
            use_ml: Whether to use ML model if available

        Returns:
            CategorizationResult with category and confidence
        """
        description_lower = description.lower()
        vendor_lower = vendor.lower() if vendor else ""

        # Track which methods contributed
        matching_rules = []
        vendor_recognized = False
        vendor_category_history = None

        # 1. Check vendor mapping first
        vendor_category, vendor_conf = self._check_vendor(vendor_lower)
        if vendor_category:
            vendor_recognized = True
            vendor_category_history = vendor_category.value
            matching_rules.append(f"vendor_match:{vendor_lower}")

        # 2. Apply keyword rules
        rule_scores = self._apply_keyword_rules(description_lower)

        # 3. Use ML model if available
        ml_scores = {}
        if use_ml and self.model and HAS_SKLEARN:
            ml_scores = self._predict_with_ml(description)
            if ml_scores:
                matching_rules.append("ml_model")

        # 4. Combine scores
        final_scores = self._combine_scores(
            vendor_category, vendor_conf,
            rule_scores,
            ml_scores
        )

        # Get top category and alternatives
        sorted_categories = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

        if sorted_categories:
            top_category = sorted_categories[0][0]
            top_confidence = sorted_categories[0][1]
            alternatives = [(cat, score) for cat, score in sorted_categories[1:4] if score > 0.1]
        else:
            top_category = ExpenseCategory.OTHER
            top_confidence = 0.5
            alternatives = []

        return CategorizationResult(
            description=description,
            predicted_category=top_category,
            confidence=round(top_confidence, 3),
            alternative_categories=alternatives,
            matching_rules=matching_rules,
            vendor_recognized=vendor_recognized,
            vendor_category_history=vendor_category_history
        )

    def _check_vendor(self, vendor: str) -> Tuple[Optional[ExpenseCategory], float]:
        """Check if vendor maps to a known category"""
        if not vendor:
            return None, 0

        # Exact match
        if vendor in self.vendor_mappings:
            return self.vendor_mappings[vendor], 0.95

        # Partial match
        for pattern, category in self.vendor_mappings.items():
            if pattern in vendor or vendor in pattern:
                return category, 0.85

        return None, 0

    def _apply_keyword_rules(self, description: str) -> Dict[ExpenseCategory, float]:
        """Apply keyword rules to description"""
        scores = {cat: 0.0 for cat in ExpenseCategory}

        for category, keywords in CATEGORY_KEYWORDS.items():
            matches = 0
            for keyword in keywords:
                if keyword in description:
                    matches += 1
                    # Exact word match scores higher
                    if re.search(r'\b' + re.escape(keyword) + r'\b', description):
                        matches += 0.5

            if matches > 0:
                # Normalize score based on number of matches
                scores[category] = min(0.9, 0.3 + matches * 0.15)

        return scores

    def _predict_with_ml(self, description: str) -> Dict[ExpenseCategory, float]:
        """Predict category using ML model"""
        if not self.model or not self.vectorizer:
            return {}

        try:
            # Get probability predictions
            proba = self.model.predict_proba([description])[0]
            classes = self.model.classes_

            scores = {}
            for i, class_name in enumerate(classes):
                try:
                    category = ExpenseCategory(class_name)
                    scores[category] = proba[i]
                except ValueError:
                    pass

            return scores
        except Exception as e:
            print(f"ML prediction failed: {e}")
            return {}

    def _combine_scores(
        self,
        vendor_category: Optional[ExpenseCategory],
        vendor_conf: float,
        rule_scores: Dict[ExpenseCategory, float],
        ml_scores: Dict[ExpenseCategory, float]
    ) -> Dict[ExpenseCategory, float]:
        """Combine scores from different methods"""
        final_scores = {cat: 0.0 for cat in ExpenseCategory}

        # Weight factors
        vendor_weight = 0.4 if vendor_category else 0
        rule_weight = 0.35
        ml_weight = 0.25 if ml_scores else 0

        # Normalize weights
        total_weight = vendor_weight + rule_weight + ml_weight
        if total_weight > 0:
            vendor_weight /= total_weight
            rule_weight /= total_weight
            ml_weight /= total_weight

        # Add vendor score
        if vendor_category:
            final_scores[vendor_category] += vendor_conf * vendor_weight

        # Add rule scores
        for cat, score in rule_scores.items():
            final_scores[cat] += score * rule_weight

        # Add ML scores
        for cat, score in ml_scores.items():
            final_scores[cat] += score * ml_weight

        return final_scores

    def categorize_batch(
        self,
        expenses: List[Dict[str, Any]]
    ) -> List[CategorizationResult]:
        """
        Categorize multiple expenses

        Args:
            expenses: List of dicts with 'description', 'vendor', 'amount'

        Returns:
            List of CategorizationResults
        """
        results = []
        for expense in expenses:
            result = self.categorize(
                description=expense.get('description', ''),
                vendor=expense.get('vendor'),
                amount=expense.get('amount')
            )
            results.append(result)
        return results

    def submit_correction(
        self,
        description: str,
        correct_category: ExpenseCategory,
        vendor: Optional[str] = None,
        amount: Optional[float] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Submit a user correction for model improvement

        Args:
            description: Expense description
            correct_category: The correct category
            vendor: Optional vendor
            amount: Optional amount
            user_id: User making correction

        Returns:
            Success status
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Add to training data
            cursor.execute("""
                INSERT INTO expense_categorization_training
                (description, vendor, amount, category, source, user_corrected, created_by_user_id)
                VALUES (?, ?, ?, ?, 'user_correction', TRUE, ?)
            """, (description, vendor, amount, correct_category.value, user_id))

            # Update vendor mapping if vendor provided
            if vendor:
                vendor_lower = vendor.lower()
                cursor.execute("""
                    INSERT INTO vendor_category_mappings (vendor_pattern, category, occurrence_count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(vendor_pattern) DO UPDATE SET
                        category = CASE
                            WHEN category = ? THEN category
                            ELSE ?
                        END,
                        occurrence_count = occurrence_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                """, (vendor_lower, correct_category.value, correct_category.value, correct_category.value))

                # Update in-memory mapping
                self.vendor_mappings[vendor_lower] = correct_category

            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving correction: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def train_model(self, min_samples: int = 50) -> Dict[str, Any]:
        """
        Train ML categorization model on collected data

        Args:
            min_samples: Minimum samples required to train

        Returns:
            Training results
        """
        if not HAS_SKLEARN:
            return {
                "status": "error",
                "message": "scikit-learn not installed"
            }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get training data
        cursor.execute("""
            SELECT description, category
            FROM expense_categorization_training
        """)

        rows = cursor.fetchall()
        conn.close()

        if len(rows) < min_samples:
            return {
                "status": "error",
                "message": f"Need at least {min_samples} samples, have {len(rows)}"
            }

        descriptions = [row[0] for row in rows]
        categories = [row[1] for row in rows]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            descriptions, categories, test_size=0.2, random_state=42
        )

        # Create and train pipeline
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words='english'
            )),
            ('classifier', LogisticRegression(
                max_iter=500,
                class_weight='balanced'
            ))
        ])

        pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred = pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Save model
        os.makedirs(os.path.dirname(self.model_path) or '.', exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': pipeline,
                'vectorizer': pipeline.named_steps['tfidf']
            }, f)

        self.model = pipeline
        self.vectorizer = pipeline.named_steps['tfidf']

        # Category distribution
        category_counts = Counter(categories)

        return {
            "status": "success",
            "training_samples": len(rows),
            "test_samples": len(X_test),
            "accuracy": round(accuracy, 4),
            "categories_trained": len(set(categories)),
            "category_distribution": dict(category_counts)
        }

    def get_training_stats(self) -> Dict[str, Any]:
        """Get statistics about training data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total samples
        cursor.execute("SELECT COUNT(*) FROM expense_categorization_training")
        total = cursor.fetchone()[0]

        # User corrections
        cursor.execute("""
            SELECT COUNT(*) FROM expense_categorization_training
            WHERE user_corrected = TRUE
        """)
        corrections = cursor.fetchone()[0]

        # By category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM expense_categorization_training
            GROUP BY category
            ORDER BY count DESC
        """)
        by_category = dict(cursor.fetchall())

        # Vendor mappings
        cursor.execute("SELECT COUNT(*) FROM vendor_category_mappings")
        vendor_mappings = cursor.fetchone()[0]

        conn.close()

        return {
            "total_samples": total,
            "user_corrections": corrections,
            "by_category": by_category,
            "vendor_mappings_count": vendor_mappings + len(DEFAULT_VENDOR_MAPPINGS),
            "model_trained": self.model is not None,
            "ready_for_training": total >= 50,
            "sklearn_available": HAS_SKLEARN
        }

    def get_categories(self) -> List[Dict[str, str]]:
        """Get list of available categories"""
        return [
            {"value": cat.value, "name": cat.name.replace("_", " ").title()}
            for cat in ExpenseCategory
        ]

    def suggest_category_for_import(
        self,
        qb_account: str,
        description: str,
        vendor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest category for QuickBooks import

        Args:
            qb_account: QuickBooks account name
            description: Transaction description
            vendor: Optional vendor name

        Returns:
            Suggested category with confidence
        """
        # Combine QB account and description for better matching
        combined_text = f"{qb_account} {description}".lower()

        result = self.categorize(
            description=combined_text,
            vendor=vendor
        )

        return {
            "qb_account": qb_account,
            "suggested_category": result.predicted_category.value,
            "confidence": result.confidence,
            "alternatives": [
                {"category": cat.value, "confidence": conf}
                for cat, conf in result.alternative_categories
            ],
            "vendor_recognized": result.vendor_recognized
        }


# Singleton instance
_expense_categorization_service: Optional[ExpenseCategorizationService] = None


def get_expense_categorization_service() -> ExpenseCategorizationService:
    """Get or create expense categorization service singleton"""
    global _expense_categorization_service
    if _expense_categorization_service is None:
        _expense_categorization_service = ExpenseCategorizationService()
    return _expense_categorization_service
