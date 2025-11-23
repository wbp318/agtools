"""
Disease Identification Service
Symptom-based disease diagnosis for corn and soybeans
"""

from typing import List, Dict, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.seed_data import CORN_DISEASES, SOYBEAN_DISEASES


class DiseaseIdentifier:
    """Professional disease identification system"""

    def __init__(self):
        self.corn_diseases = CORN_DISEASES
        self.soybean_diseases = SOYBEAN_DISEASES

    def identify_by_symptoms(
        self,
        crop: str,
        symptoms: List[str],
        growth_stage: str,
        weather_conditions: Optional[str] = None
    ) -> List[Dict]:
        """
        Identify disease based on symptoms and conditions

        Args:
            crop: 'corn' or 'soybean'
            symptoms: List of symptom strings
            growth_stage: Current growth stage
            weather_conditions: Weather description

        Returns:
            List of disease matches with confidence scores
        """

        # Get disease database for crop
        if crop.lower() == "corn":
            disease_database = self.corn_diseases
        elif crop.lower() == "soybean":
            disease_database = self.soybean_diseases
        else:
            disease_database = self.corn_diseases + self.soybean_diseases

        # Score each disease
        matches = []

        for idx, disease in enumerate(disease_database):
            confidence = self._calculate_confidence(
                disease=disease,
                symptoms=symptoms,
                growth_stage=growth_stage,
                weather_conditions=weather_conditions
            )

            if confidence > 0.2:
                matches.append({
                    "id": idx,
                    "common_name": disease["common_name"],
                    "scientific_name": disease["scientific_name"],
                    "confidence": round(confidence, 3),
                    "description": disease["description"],
                    "symptoms": disease["symptoms"],
                    "favorable_conditions": disease["favorable_conditions"],
                    "management": disease["management"]
                })

        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        return matches[:5]

    def _calculate_confidence(
        self,
        disease: Dict,
        symptoms: List[str],
        growth_stage: str,
        weather_conditions: Optional[str]
    ) -> float:
        """Calculate confidence score for disease match"""

        confidence = 0.0

        # Symptom matching (60% weight)
        symptom_score = self._match_symptoms(disease, symptoms)
        confidence += symptom_score * 0.6

        # Weather/environmental conditions (30% weight)
        if weather_conditions:
            conditions_score = self._match_conditions(disease, weather_conditions)
            confidence += conditions_score * 0.3
        else:
            # If no weather info, give base score
            confidence += 0.15

        # Timing (10% weight)
        timing_score = self._match_timing(disease, growth_stage)
        confidence += timing_score * 0.1

        return min(confidence, 1.0)

    def _match_symptoms(self, disease: Dict, symptoms: List[str]) -> float:
        """Match symptoms against disease presentation"""

        if not symptoms:
            return 0.0

        disease_symptoms = disease.get("symptoms", "").lower()
        disease_description = disease.get("description", "").lower()
        combined_text = disease_symptoms + " " + disease_description

        matches = 0
        total_symptoms = len(symptoms)

        # Symptom keyword mapping for diseases
        symptom_keywords = {
            "leaf_spots": ["spot", "lesion", "blotch"],
            "yellowing": ["yellow", "chlorosis"],
            "tan_lesions": ["tan", "brown", "necrotic"],
            "gray_lesions": ["gray", "grey"],
            "rectangular_lesions": ["rectangular", "parallel"],
            "circular_spots": ["circular", "round", "oval"],
            "pustules": ["pustule", "rust", "orange", "reddish"],
            "black_specks": ["black", "tar spot", "stromata"],
            "white_mold": ["white", "cottony", "fluffy"],
            "root_rot": ["root rot", "brown roots", "rotted"],
            "wilting": ["wilt", "wilted", "drooping"],
            "stem_discoloration": ["stem", "stalk", "vascular", "brown pith"],
            "ear_rot": ["ear rot", "mold on ear", "kernel mold"],
            "defoliation": ["defoliation", "leaf death", "premature death"],
        }

        for symptom in symptoms:
            symptom_lower = symptom.lower()

            # Direct match
            if symptom_lower in combined_text:
                matches += 1
                continue

            # Keyword match
            if symptom_lower in symptom_keywords:
                keywords = symptom_keywords[symptom_lower]
                if any(keyword in combined_text for keyword in keywords):
                    matches += 0.8

        return matches / total_symptoms if total_symptoms > 0 else 0.0

    def _match_conditions(self, disease: Dict, weather_conditions: str) -> float:
        """Match weather conditions to disease-favorable conditions"""

        favorable = disease.get("favorable_conditions", "").lower()
        weather_lower = weather_conditions.lower()

        score = 0.0

        # Weather condition mappings
        weather_keywords = {
            "wet": ["wet", "humid", "rain", "moisture", "high humidity"],
            "cool": ["cool", "60", "65", "70"],
            "warm": ["warm", "75", "80", "85"],
            "hot": ["hot", "85", "90"],
            "dry": ["dry", "drought"],
        }

        # Check if weather matches favorable conditions
        for condition in ["wet", "cool", "warm", "hot", "dry"]:
            if condition in weather_lower:
                keywords = weather_keywords[condition]
                if any(keyword in favorable for keyword in keywords):
                    score += 0.5

        return min(score, 1.0)

    def _match_timing(self, disease: Dict, growth_stage: str) -> float:
        """Match growth stage to typical disease timing"""

        # Some diseases are more common at certain stages
        disease_name = disease["common_name"].lower()

        early_stages = ["ve", "v1", "v2", "v3"]
        mid_stages = ["v4", "v5", "v6", "vt"]
        reproductive_stages = ["r1", "r2", "r3", "r4", "r5", "r6"]

        stage_lower = growth_stage.lower()

        # Seedling diseases
        seedling_diseases = ["pythium", "rhizoctonia", "fusarium seedling"]
        if any(name in disease_name for name in seedling_diseases):
            return 1.0 if stage_lower in early_stages else 0.3

        # Mid-late season foliar diseases
        foliar_diseases = ["gray leaf spot", "rust", "tar spot", "blight"]
        if any(name in disease_name for name in foliar_diseases):
            if stage_lower in reproductive_stages:
                return 1.0
            elif stage_lower in mid_stages:
                return 0.7
            else:
                return 0.4

        # White mold (flowering time)
        if "white mold" in disease_name or "sclerotinia" in disease_name:
            return 1.0 if stage_lower in ["r1", "r2"] else 0.5

        # Default
        return 0.5


def identify_disease_by_symptoms(*args, **kwargs):
    """Module-level function for API"""
    identifier = DiseaseIdentifier()
    return identifier.identify_by_symptoms(*args, **kwargs)


# Example usage
if __name__ == "__main__":
    identifier = DiseaseIdentifier()

    # Example 1: Gray leaf spot
    print("=== EXAMPLE 1: Gray Leaf Spot ===")
    results = identifier.identify_by_symptoms(
        crop="corn",
        symptoms=["rectangular_lesions", "gray_lesions", "tan_lesions"],
        growth_stage="R2",
        weather_conditions="warm, humid, cloudy"
    )

    for result in results[:3]:
        print(f"\n{result['common_name']} (Confidence: {result['confidence']*100:.1f}%)")
        print(f"  Symptoms: {result['symptoms'][:100]}...")
        print(f"  Management: {result['management'][:100]}...")

    # Example 2: White mold
    print("\n\n=== EXAMPLE 2: White Mold ===")
    results = identifier.identify_by_symptoms(
        crop="soybean",
        symptoms=["white_mold", "stem_discoloration", "wilting"],
        growth_stage="R3",
        weather_conditions="cool, wet"
    )

    for result in results[:3]:
        print(f"\n{result['common_name']} (Confidence: {result['confidence']*100:.1f}%)")
        print(f"  Symptoms: {result['symptoms'][:100]}...")
