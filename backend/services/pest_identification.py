"""
Pest Identification Service
Hybrid approach: Symptom-based guided identification + AI image recognition
"""

from typing import List, Dict, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.seed_data import CORN_PESTS, SOYBEAN_PESTS


class PestIdentifier:
    """Professional pest identification system"""

    def __init__(self):
        self.corn_pests = CORN_PESTS
        self.soybean_pests = SOYBEAN_PESTS

    def identify_by_symptoms(
        self,
        crop: str,
        symptoms: List[str],
        growth_stage: str,
        field_conditions: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Identify pest based on symptoms and field observations

        Args:
            crop: 'corn' or 'soybean'
            symptoms: List of symptom strings (e.g., ['leaf_holes', 'silk_clipping', 'whorl_damage'])
            growth_stage: Current growth stage
            field_conditions: Additional context (weather, field history, etc.)

        Returns:
            List of pest matches with confidence scores
        """

        # Get pest database for crop
        if crop.lower() == "corn":
            pest_database = self.corn_pests
        elif crop.lower() == "soybean":
            pest_database = self.soybean_pests
        else:
            pest_database = self.corn_pests + self.soybean_pests

        # Score each pest based on symptom matching
        matches = []

        for idx, pest in enumerate(pest_database):
            confidence = self._calculate_confidence(
                pest=pest,
                symptoms=symptoms,
                growth_stage=growth_stage,
                field_conditions=field_conditions
            )

            if confidence > 0.2:  # Only return reasonable matches
                matches.append({
                    "id": idx,
                    "common_name": pest["common_name"],
                    "scientific_name": pest["scientific_name"],
                    "confidence": round(confidence, 3),
                    "description": pest["description"],
                    "damage_symptoms": pest["damage_symptoms"],
                    "identification_features": pest["identification_features"],
                    "economic_threshold": pest.get("economic_threshold", "Consult extension resources"),
                    "management_notes": pest.get("management_notes", "")
                })

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        # Return top 5 matches
        return matches[:5]

    def _calculate_confidence(
        self,
        pest: Dict,
        symptoms: List[str],
        growth_stage: str,
        field_conditions: Optional[Dict]
    ) -> float:
        """Calculate confidence score for pest match"""

        confidence = 0.0

        # Symptom matching (most important factor)
        symptom_score = self._match_symptoms(pest, symptoms)
        confidence += symptom_score * 0.6  # 60% weight

        # Timing/growth stage matching
        timing_score = self._match_timing(pest, growth_stage)
        confidence += timing_score * 0.25  # 25% weight

        # Field conditions matching
        if field_conditions:
            conditions_score = self._match_conditions(pest, field_conditions)
            confidence += conditions_score * 0.15  # 15% weight

        return min(confidence, 1.0)  # Cap at 1.0

    def _match_symptoms(self, pest: Dict, symptoms: List[str]) -> float:
        """Match symptoms against pest damage patterns"""

        if not symptoms:
            return 0.0

        damage_description = pest.get("damage_symptoms", "").lower()
        identification_features = pest.get("identification_features", "").lower()
        combined_text = damage_description + " " + identification_features

        matches = 0
        total_symptoms = len(symptoms)

        # Symptom keyword mapping
        symptom_keywords = {
            "leaf_holes": ["holes", "defoliation", "feeding", "skeletonizing"],
            "whorl_damage": ["whorl", "shothole"],
            "silk_clipping": ["silk", "pollination"],
            "root_damage": ["root", "pruning", "lodging", "goose-neck"],
            "stalk_tunneling": ["stalk", "tunnel", "borer"],
            "yellowing": ["yellow", "chlorosis", "stunted"],
            "wilting": ["wilt", "drooping"],
            "stippling": ["stippling", "speckling", "mite"],
            "webbing": ["web", "silk"],
            "curled_leaves": ["curl", "distorted"],
            "pod_damage": ["pod", "seed"],
            "stem_damage": ["stem", "girdling"],
            "dead_heart": ["dead heart", "dead whorl"],
            "ear_damage": ["ear", "kernel"],
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
                    matches += 0.8  # Slightly lower weight for keyword match

        return matches / total_symptoms if total_symptoms > 0 else 0.0

    def _match_timing(self, pest: Dict, growth_stage: str) -> float:
        """Match growth stage to typical pest timing"""

        # Extract timing information from pest data
        lifecycle = pest.get("lifecycle", "").lower()
        management_notes = pest.get("management_notes", "").lower()

        # Growth stage categories
        early_stages = ["ve", "v1", "v2", "v3", "v4"]
        mid_stages = ["v5", "v6", "vt"]
        reproductive_stages = ["r1", "r2", "r3", "r4", "r5", "r6"]

        stage_lower = growth_stage.lower()

        # Early season pests
        early_season_pests = ["cutworm", "wireworm", "seedcorn maggot", "flea beetle"]
        if any(name in pest["common_name"].lower() for name in early_season_pests):
            if stage_lower in early_stages:
                return 1.0
            else:
                return 0.3

        # Mid-season pests
        mid_season_pests = ["corn borer", "armyworm"]
        if any(name in pest["common_name"].lower() for name in mid_season_pests):
            if stage_lower in mid_stages:
                return 1.0
            elif stage_lower in early_stages:
                return 0.6
            else:
                return 0.4

        # Late season pests
        late_season_pests = ["rootworm adult", "japanese beetle", "stink bug", "spider mite"]
        if any(name in pest["common_name"].lower() for name in late_season_pests):
            if stage_lower in reproductive_stages:
                return 1.0
            else:
                return 0.4

        # Default - timing is possible but not optimal
        return 0.5

    def _match_conditions(self, pest: Dict, field_conditions: Dict) -> float:
        """Match field conditions to pest preferences"""

        score = 0.5  # Base score

        # Weather conditions
        if "weather" in field_conditions:
            weather = field_conditions["weather"]

            # Hot, dry weather favors mites
            if "mite" in pest["common_name"].lower():
                if weather.get("hot_dry", False):
                    score = 1.0
                else:
                    score = 0.3

        # Crop rotation
        if "previous_crop" in field_conditions:
            previous_crop = field_conditions["previous_crop"].lower()

            # Corn rootworm issues in continuous corn
            if "rootworm" in pest["common_name"].lower():
                if previous_crop == "corn":
                    score = 1.0
                else:
                    score = 0.2

        # Field edge vs. interior
        if "location" in field_conditions:
            location = field_conditions["location"]

            # Some pests more common on edges
            edge_pests = ["stalk borer", "grasshopper", "japanese beetle"]
            if any(name in pest["common_name"].lower() for name in edge_pests):
                if location == "field_edge":
                    score = 1.0

        return score


# Guided identification questions
GUIDED_QUESTIONS = [
    {
        "id": 1,
        "question": "Where on the plant is the damage?",
        "category": "location",
        "answers": [
            {"text": "Leaves (holes, chewed edges)", "narrows_to": ["armyworm", "beetle", "grasshopper", "looper"]},
            {"text": "Whorl (shothole damage)", "narrows_to": ["corn borer", "armyworm"]},
            {"text": "Roots (pruning, lodging)", "narrows_to": ["rootworm", "wireworm"]},
            {"text": "Silks (clipped, chewed)", "narrows_to": ["rootworm adult", "japanese beetle", "corn earworm"]},
            {"text": "Stalks (tunneling, boring)", "narrows_to": ["corn borer", "stalk borer"]},
            {"text": "Entire plant (stunted, yellow)", "narrows_to": ["aphid", "rootworm", "nematode", "disease"]},
            {"text": "Pods/seeds", "narrows_to": ["stink bug", "bean leaf beetle", "corn earworm"]},
        ]
    },
    {
        "id": 2,
        "question": "What does the pest look like (if visible)?",
        "category": "identification",
        "answers": [
            {"text": "Small green/yellow insects on leaves", "narrows_to": ["aphid"]},
            {"text": "Beetle (1/4 inch, various colors)", "narrows_to": ["bean leaf beetle", "rootworm adult", "flea beetle"]},
            {"text": "Beetle (metallic green/bronze)", "narrows_to": ["japanese beetle"]},
            {"text": "Caterpillar/worm", "narrows_to": ["armyworm", "corn borer", "cutworm", "corn earworm", "looper"]},
            {"text": "Very tiny specks (mites)", "narrows_to": ["spider mite"]},
            {"text": "Shield-shaped bugs", "narrows_to": ["stink bug"]},
            {"text": "Large hoppers", "narrows_to": ["grasshopper"]},
            {"text": "Haven't seen the pest", "narrows_to": ["all"]},
        ]
    },
    {
        "id": 3,
        "question": "When did the damage start?",
        "category": "timing",
        "answers": [
            {"text": "At or shortly after emergence", "narrows_to": ["cutworm", "wireworm", "flea beetle", "seedcorn maggot"]},
            {"text": "Mid-season (V6-VT)", "narrows_to": ["corn borer", "armyworm", "grasshopper"]},
            {"text": "Late season (after tassel/flowering)", "narrows_to": ["rootworm adult", "japanese beetle", "aphid", "spider mite", "stink bug"]},
            {"text": "Not sure", "narrows_to": ["all"]},
        ]
    }
]


def identify_pest_by_symptoms(*args, **kwargs):
    """Module-level function for API"""
    identifier = PestIdentifier()
    return identifier.identify_by_symptoms(*args, **kwargs)


# Example usage
if __name__ == "__main__":
    identifier = PestIdentifier()

    # Example 1: Soybean aphid identification
    print("=== EXAMPLE 1: Soybean Aphid ===")
    results = identifier.identify_by_symptoms(
        crop="soybean",
        symptoms=["curled_leaves", "yellowing", "sticky_residue"],
        growth_stage="R2",
        field_conditions={"weather": "warm"}
    )

    for result in results[:3]:
        print(f"\n{result['common_name']} (Confidence: {result['confidence']*100:.1f}%)")
        print(f"  Symptoms: {result['damage_symptoms'][:100]}...")
        print(f"  Threshold: {result['economic_threshold'][:80]}...")

    # Example 2: Corn rootworm adults
    print("\n\n=== EXAMPLE 2: Corn Rootworm Adults ===")
    results = identifier.identify_by_symptoms(
        crop="corn",
        symptoms=["silk_clipping", "root_damage", "lodging"],
        growth_stage="R1",
        field_conditions={"previous_crop": "corn"}
    )

    for result in results[:3]:
        print(f"\n{result['common_name']} (Confidence: {result['confidence']*100:.1f}%)")
        print(f"  Symptoms: {result['damage_symptoms'][:100]}...")
