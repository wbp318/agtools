"""
Grant Application Assistant Service
Automated grant proposal generation, eligibility assessment, and compliance tracking.

Features:
- Grant program database with requirements
- Eligibility pre-screening
- Auto-generated proposal sections
- Impact metrics calculator
- Budget template generation
- Timeline/milestone planning
- Required documentation checklist
- Grant deadline tracking
- Success probability scoring
- Application status tracking
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math


class GrantCategory(str, Enum):
    CONSERVATION = "conservation"
    CLIMATE = "climate"
    RESEARCH = "research"
    TECHNOLOGY = "technology"
    SUSTAINABILITY = "sustainability"
    BEGINNING_FARMER = "beginning_farmer"
    VALUE_ADDED = "value_added"
    LOCAL_FOOD = "local_food"
    ORGANIC = "organic"
    SPECIALTY_CROP = "specialty_crop"


class GrantStatus(str, Enum):
    IDENTIFIED = "identified"
    RESEARCHING = "researching"
    PREPARING = "preparing"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    AWARDED = "awarded"
    REJECTED = "rejected"
    COMPLETED = "completed"


class FundingAgency(str, Enum):
    USDA_NRCS = "usda_nrcs"
    USDA_FSA = "usda_fsa"
    USDA_RD = "usda_rd"
    USDA_NIFA = "usda_nifa"
    EPA = "epa"
    STATE_AG = "state_ag"
    FOUNDATION = "foundation"
    CORPORATE = "corporate"


# Comprehensive grant program database
GRANT_PROGRAMS = {
    "eqip": {
        "name": "Environmental Quality Incentives Program (EQIP)",
        "agency": FundingAgency.USDA_NRCS,
        "category": GrantCategory.CONSERVATION,
        "description": "Financial and technical assistance for conservation practices",
        "funding_range": {"min": 1500, "max": 450000},
        "cost_share_rate": 0.75,  # 75% cost share
        "eligible_applicants": [
            "Agricultural producers",
            "Forest landowners",
            "Tribes"
        ],
        "eligible_practices": [
            "Cover crops", "No-till", "Nutrient management",
            "Irrigation efficiency", "Wildlife habitat",
            "Prescribed grazing", "Forest management"
        ],
        "application_periods": ["October - December (varies by state)"],
        "typical_timeline": "6-12 months to funding",
        "key_requirements": [
            "Farm records number (FSA)",
            "Conservation plan",
            "Meet adjusted gross income limitation ($900,000)",
            "Control of land for contract period"
        ],
        "success_factors": [
            "Resource concerns documented",
            "Clear conservation goals",
            "Cost-effective practices",
            "Beginning/limited resource farmer status"
        ],
        "documentation_needed": [
            "FSA-578 (acreage report)",
            "Conservation plan",
            "Financial documentation",
            "Land control documentation"
        ]
    },
    "csp": {
        "name": "Conservation Stewardship Program (CSP)",
        "agency": FundingAgency.USDA_NRCS,
        "category": GrantCategory.CONSERVATION,
        "description": "Annual payments for maintaining and improving existing conservation",
        "funding_range": {"min": 1500, "max": 200000},
        "cost_share_rate": 1.0,  # Annual payments, not cost-share
        "eligible_applicants": [
            "Agricultural producers with existing conservation"
        ],
        "eligible_practices": [
            "Conservation enhancements",
            "Cover crop bundles",
            "Pollinator habitat",
            "Soil health improvement",
            "Resource-conserving crop rotation"
        ],
        "application_periods": ["Sign-up periods announced annually"],
        "typical_timeline": "5-year contracts",
        "key_requirements": [
            "Meet stewardship threshold on at least one resource concern",
            "Commit to meet threshold on additional concerns",
            "Address at least one priority resource concern"
        ],
        "success_factors": [
            "Existing conservation practices",
            "Willingness to adopt enhancements",
            "High baseline conservation score"
        ],
        "documentation_needed": [
            "Current conservation practices documentation",
            "Resource inventory",
            "Enhancement commitments"
        ]
    },
    "sare_producer": {
        "name": "SARE Producer Grant",
        "agency": FundingAgency.USDA_NIFA,
        "category": GrantCategory.RESEARCH,
        "description": "On-farm research and demonstration projects",
        "funding_range": {"min": 500, "max": 23000},
        "cost_share_rate": 0,  # Grant, not cost-share
        "eligible_applicants": [
            "Farmers", "Ranchers", "Agricultural professionals"
        ],
        "eligible_practices": [
            "Sustainable agriculture research",
            "On-farm trials",
            "Demonstration projects",
            "Outreach activities"
        ],
        "application_periods": ["Varies by region - typically fall"],
        "typical_timeline": "1-2 year projects",
        "key_requirements": [
            "Focus on sustainable agriculture",
            "Producer-led research",
            "Clear research objectives",
            "Outreach/education component"
        ],
        "success_factors": [
            "Innovative approach",
            "Clear methodology",
            "Farmer involvement",
            "Replicability",
            "Strong outreach plan"
        ],
        "documentation_needed": [
            "Project narrative",
            "Budget",
            "Timeline",
            "Outreach plan",
            "Letters of support"
        ]
    },
    "reap": {
        "name": "Rural Energy for America Program (REAP)",
        "agency": FundingAgency.USDA_RD,
        "category": GrantCategory.TECHNOLOGY,
        "description": "Grants and loans for renewable energy and efficiency",
        "funding_range": {"min": 2500, "max": 1000000},
        "cost_share_rate": 0.25,  # Up to 25% grant
        "eligible_applicants": [
            "Agricultural producers",
            "Rural small businesses"
        ],
        "eligible_practices": [
            "Solar installations",
            "Wind energy",
            "Biogas digesters",
            "Energy efficiency improvements",
            "Grain dryers",
            "Irrigation efficiency"
        ],
        "application_periods": ["Rolling applications, quarterly deadlines"],
        "typical_timeline": "3-6 months for grants",
        "key_requirements": [
            "Rural location",
            "Energy audit for efficiency projects",
            "Technical report for renewable energy",
            "Financial feasibility"
        ],
        "success_factors": [
            "Strong energy savings/production",
            "Good payback period",
            "Complete technical documentation",
            "Demonstrated need"
        ],
        "documentation_needed": [
            "Energy audit (efficiency) or technical report (renewable)",
            "Financial projections",
            "Vendor quotes",
            "Business financials"
        ]
    },
    "value_added_producer": {
        "name": "Value-Added Producer Grant (VAPG)",
        "agency": FundingAgency.USDA_RD,
        "category": GrantCategory.VALUE_ADDED,
        "description": "Grants for value-added agricultural businesses",
        "funding_range": {"min": 10000, "max": 250000},
        "cost_share_rate": 0.50,  # 50% match required
        "eligible_applicants": [
            "Independent producers",
            "Agricultural producer groups",
            "Cooperatives"
        ],
        "eligible_practices": [
            "Planning grants (up to $75,000)",
            "Working capital (up to $250,000)",
            "Marketing",
            "Processing",
            "Product development"
        ],
        "application_periods": ["Annual - typically January-March"],
        "typical_timeline": "6-9 months to award",
        "key_requirements": [
            "Producer ownership of raw commodity",
            "Value-added product",
            "Viable business plan",
            "Matching funds (1:1)"
        ],
        "success_factors": [
            "Clear value-added strategy",
            "Market research",
            "Financial viability",
            "Producer involvement",
            "Priority applicant status"
        ],
        "documentation_needed": [
            "Business plan",
            "Feasibility study",
            "Market analysis",
            "Financial statements",
            "Letters of commitment for matching funds"
        ]
    },
    "bfrdp": {
        "name": "Beginning Farmer and Rancher Development Program",
        "agency": FundingAgency.USDA_NIFA,
        "category": GrantCategory.BEGINNING_FARMER,
        "description": "Training and technical assistance for beginning farmers",
        "funding_range": {"min": 50000, "max": 750000},
        "cost_share_rate": 0.25,  # 25% match required
        "eligible_applicants": [
            "Collaborative state/tribal/local government entities",
            "Land-grant universities",
            "Non-profit organizations"
        ],
        "eligible_practices": [
            "Education and training programs",
            "Technical assistance",
            "Financial training",
            "Land access programs"
        ],
        "application_periods": ["Annual - typically spring"],
        "typical_timeline": "3-year projects",
        "key_requirements": [
            "Focus on beginning farmers/ranchers",
            "Educational/training component",
            "Measurable outcomes"
        ],
        "success_factors": [
            "Partnership with established organizations",
            "Clear training curriculum",
            "Veteran or socially disadvantaged focus",
            "Sustainable program design"
        ],
        "documentation_needed": [
            "Project narrative",
            "Training curriculum outline",
            "Partner commitments",
            "Evaluation plan"
        ]
    },
    "specialty_crop_block": {
        "name": "Specialty Crop Block Grant Program",
        "agency": FundingAgency.STATE_AG,
        "category": GrantCategory.SPECIALTY_CROP,
        "description": "State-administered grants for specialty crop competitiveness",
        "funding_range": {"min": 5000, "max": 200000},
        "cost_share_rate": 0,  # Varies by state
        "eligible_applicants": [
            "Specialty crop producers",
            "Producer groups",
            "Research institutions"
        ],
        "eligible_practices": [
            "Research",
            "Marketing",
            "Food safety",
            "Pest management",
            "Production efficiency"
        ],
        "application_periods": ["Varies by state - typically fall"],
        "typical_timeline": "1-3 year projects",
        "key_requirements": [
            "Focus on specialty crops",
            "Benefit to specialty crop industry",
            "Measurable outcomes"
        ],
        "success_factors": [
            "Industry-wide benefit",
            "Strong evaluation plan",
            "Partnership with state department",
            "Clear ROI"
        ],
        "documentation_needed": [
            "Project proposal",
            "Budget",
            "Performance measures",
            "Letters of support"
        ]
    },
    "climate_smart_commodities": {
        "name": "USDA Climate-Smart Commodities",
        "agency": FundingAgency.USDA_NRCS,
        "category": GrantCategory.CLIMATE,
        "description": "Large-scale climate-smart agriculture partnerships",
        "funding_range": {"min": 5000000, "max": 100000000},
        "cost_share_rate": 0.25,  # Partner contribution
        "eligible_applicants": [
            "Partnership groups",
            "Supply chain participants",
            "Producer organizations"
        ],
        "eligible_practices": [
            "Carbon sequestration",
            "Emission reduction",
            "Climate-smart supply chains",
            "Market development"
        ],
        "application_periods": ["Special funding opportunities"],
        "typical_timeline": "3-5 year projects",
        "key_requirements": [
            "Large-scale impact",
            "Supply chain involvement",
            "Measurable GHG reductions"
        ],
        "success_factors": [
            "Strong partnerships",
            "Proven climate practices",
            "Scale of impact",
            "Market connections"
        ],
        "documentation_needed": [
            "Partnership agreements",
            "Climate impact projections",
            "MRV plan",
            "Market commitments"
        ]
    }
}


@dataclass
class GrantApplication:
    """Track a grant application"""
    application_id: str
    grant_program: str
    status: GrantStatus
    project_title: str
    requested_amount: float
    match_amount: float
    submission_date: Optional[date] = None
    deadline: Optional[date] = None
    award_date: Optional[date] = None
    award_amount: float = 0
    project_period_start: Optional[date] = None
    project_period_end: Optional[date] = None
    contact_person: str = ""
    notes: str = ""
    documents_submitted: List[str] = field(default_factory=list)
    milestones: List[Dict] = field(default_factory=list)


@dataclass
class GrantMilestone:
    """Project milestone tracking"""
    milestone_id: str
    application_id: str
    title: str
    description: str
    due_date: date
    completed_date: Optional[date] = None
    deliverables: List[str] = field(default_factory=list)
    status: str = "pending"


class GrantAssistantService:
    """
    Comprehensive grant application assistance service.
    Helps identify, prepare, and track grant applications.
    """

    def __init__(self):
        self.applications: List[GrantApplication] = []
        self.milestones: List[GrantMilestone] = []

    # =========================================================================
    # GRANT DISCOVERY & ELIGIBILITY
    # =========================================================================

    def find_matching_grants(
        self,
        farm_characteristics: Dict
    ) -> Dict:
        """
        Find grants that match farm characteristics.

        farm_characteristics should include:
        - farm_acres: Total farm acreage
        - years_farming: Years of experience
        - annual_revenue: Annual gross revenue
        - crops: List of crop types
        - has_livestock: Boolean
        - existing_conservation: List of practices
        - interests: List of interest areas
        - location: State/region
        """

        matching_grants = []

        for program_id, program in GRANT_PROGRAMS.items():
            match_score = 0
            match_reasons = []

            # Check interests alignment
            interests = farm_characteristics.get("interests", [])
            if program["category"].value in [i.lower() for i in interests]:
                match_score += 30
                match_reasons.append(f"Aligns with interest in {program['category'].value}")

            # Check for conservation practices alignment
            existing_practices = farm_characteristics.get("existing_conservation", [])
            matching_practices = [
                p for p in program.get("eligible_practices", [])
                if any(ep.lower() in p.lower() for ep in existing_practices)
            ]
            if matching_practices:
                match_score += 20
                match_reasons.append(f"Existing practices qualify: {matching_practices[:3]}")

            # Beginning farmer bonus
            years_farming = farm_characteristics.get("years_farming", 10)
            if years_farming < 10 and program["category"] == GrantCategory.BEGINNING_FARMER:
                match_score += 25
                match_reasons.append("Beginning farmer priority")
            elif years_farming < 10 and "beginning" in str(program.get("success_factors", [])).lower():
                match_score += 15
                match_reasons.append("Beginning farmer eligible")

            # Size appropriateness
            farm_acres = farm_characteristics.get("farm_acres", 0)
            funding_max = program["funding_range"]["max"]
            if farm_acres < 500 and funding_max < 100000:
                match_score += 15
                match_reasons.append("Appropriate scale")
            elif farm_acres >= 500 and funding_max >= 100000:
                match_score += 15
                match_reasons.append("Appropriate scale")

            # Check revenue threshold
            annual_revenue = farm_characteristics.get("annual_revenue", 0)
            if annual_revenue < 900000 and "AGI" in str(program.get("key_requirements", [])):
                match_score += 10
                match_reasons.append("Meets income eligibility")

            # Category-specific bonuses
            crops = farm_characteristics.get("crops", [])
            if program["category"] == GrantCategory.SPECIALTY_CROP:
                specialty_crops = ["vegetables", "fruits", "nuts", "nursery", "horticulture"]
                if any(c.lower() in specialty_crops for c in crops):
                    match_score += 20
                    match_reasons.append("Grows specialty crops")

            if match_score >= 30:  # Minimum threshold
                matching_grants.append({
                    "program_id": program_id,
                    "program_name": program["name"],
                    "agency": program["agency"].value,
                    "category": program["category"].value,
                    "match_score": match_score,
                    "match_reasons": match_reasons,
                    "funding_range": program["funding_range"],
                    "cost_share": f"{program['cost_share_rate'] * 100:.0f}%",
                    "timeline": program["typical_timeline"]
                })

        # Sort by match score
        matching_grants.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "farm_profile": farm_characteristics,
            "grants_found": len(matching_grants),
            "matching_grants": matching_grants,
            "recommendations": self._generate_grant_recommendations(
                matching_grants, farm_characteristics
            )
        }

    def _generate_grant_recommendations(
        self,
        grants: List[Dict],
        farm_chars: Dict
    ) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []

        if not grants:
            recommendations.append(
                "Consider developing conservation practices to qualify for EQIP/CSP programs"
            )
            return recommendations

        # Top grant recommendation
        if grants:
            top = grants[0]
            recommendations.append(
                f"Top match: {top['program_name']} - {top['match_reasons'][0]}"
            )

        # Conservation-specific
        existing = farm_chars.get("existing_conservation", [])
        if not existing:
            recommendations.append(
                "Starting conservation practices (cover crops, no-till) would unlock "
                "significant EQIP and CSP funding opportunities"
            )

        # Beginning farmer
        if farm_chars.get("years_farming", 10) < 10:
            recommendations.append(
                "As a beginning farmer, you receive priority consideration for most USDA programs"
            )

        return recommendations[:5]

    def get_program_details(self, program_id: str) -> Dict:
        """Get detailed information about a specific grant program"""

        program = GRANT_PROGRAMS.get(program_id)
        if not program:
            return {"error": f"Program '{program_id}' not found"}

        return {
            "program_id": program_id,
            "name": program["name"],
            "agency": program["agency"].value,
            "category": program["category"].value,
            "description": program["description"],
            "funding": {
                "minimum": f"${program['funding_range']['min']:,}",
                "maximum": f"${program['funding_range']['max']:,}",
                "cost_share_rate": f"{program['cost_share_rate'] * 100:.0f}%"
            },
            "eligibility": {
                "eligible_applicants": program["eligible_applicants"],
                "eligible_practices": program["eligible_practices"],
                "key_requirements": program["key_requirements"]
            },
            "timeline": {
                "application_periods": program["application_periods"],
                "typical_timeline": program["typical_timeline"]
            },
            "success_factors": program["success_factors"],
            "documentation_needed": program["documentation_needed"]
        }

    # =========================================================================
    # ELIGIBILITY ASSESSMENT
    # =========================================================================

    def assess_eligibility(
        self,
        program_id: str,
        applicant_data: Dict
    ) -> Dict:
        """
        Detailed eligibility assessment for a specific program.

        applicant_data should include:
        - farm_acres
        - years_farming
        - annual_revenue
        - has_fsn: Has Farm Service Agency number
        - has_conservation_plan: Has NRCS conservation plan
        - location: State
        - current_practices: List of conservation practices
        """

        program = GRANT_PROGRAMS.get(program_id)
        if not program:
            return {"error": "Program not found"}

        eligibility_checks = []
        passed_checks = 0
        total_checks = 0

        # Check FSA registration (required for USDA programs)
        if program["agency"] in [FundingAgency.USDA_NRCS, FundingAgency.USDA_FSA]:
            total_checks += 1
            has_fsn = applicant_data.get("has_fsn", False)
            if has_fsn:
                passed_checks += 1
                eligibility_checks.append({
                    "requirement": "FSA Farm Number",
                    "status": "PASS",
                    "detail": "Registered with Farm Service Agency"
                })
            else:
                eligibility_checks.append({
                    "requirement": "FSA Farm Number",
                    "status": "ACTION NEEDED",
                    "detail": "Must register with local FSA office"
                })

        # Check income threshold for NRCS programs
        if "AGI" in str(program.get("key_requirements", [])):
            total_checks += 1
            revenue = applicant_data.get("annual_revenue", 0)
            if revenue < 900000:
                passed_checks += 1
                eligibility_checks.append({
                    "requirement": "Adjusted Gross Income",
                    "status": "PASS",
                    "detail": "Under $900,000 threshold"
                })
            else:
                eligibility_checks.append({
                    "requirement": "Adjusted Gross Income",
                    "status": "FAIL",
                    "detail": "Exceeds $900,000 AGI limit (exceptions may apply)"
                })

        # Check for conservation plan (EQIP/CSP)
        if "Conservation plan" in program.get("key_requirements", []):
            total_checks += 1
            has_plan = applicant_data.get("has_conservation_plan", False)
            if has_plan:
                passed_checks += 1
                eligibility_checks.append({
                    "requirement": "Conservation Plan",
                    "status": "PASS",
                    "detail": "Active conservation plan on file"
                })
            else:
                eligibility_checks.append({
                    "requirement": "Conservation Plan",
                    "status": "ACTION NEEDED",
                    "detail": "Contact NRCS to develop conservation plan"
                })

        # Check for existing practices (CSP)
        if program_id == "csp":
            total_checks += 1
            practices = applicant_data.get("current_practices", [])
            if len(practices) >= 2:
                passed_checks += 1
                eligibility_checks.append({
                    "requirement": "Existing Conservation",
                    "status": "PASS",
                    "detail": f"Has {len(practices)} conservation practices"
                })
            else:
                eligibility_checks.append({
                    "requirement": "Existing Conservation",
                    "status": "FAIL",
                    "detail": "CSP requires baseline conservation practices"
                })

        # Calculate eligibility score
        eligibility_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        return {
            "program_id": program_id,
            "program_name": program["name"],
            "eligibility_score": round(eligibility_score, 0),
            "eligible": eligibility_score >= 70,
            "checks_passed": passed_checks,
            "total_checks": total_checks,
            "eligibility_details": eligibility_checks,
            "actions_needed": [
                check["detail"] for check in eligibility_checks
                if check["status"] == "ACTION NEEDED"
            ],
            "disqualifying_factors": [
                check["detail"] for check in eligibility_checks
                if check["status"] == "FAIL"
            ],
            "next_steps": self._get_eligibility_next_steps(eligibility_checks, program_id)
        }

    def _get_eligibility_next_steps(
        self,
        checks: List[Dict],
        program_id: str
    ) -> List[str]:
        """Generate next steps based on eligibility assessment"""
        steps = []

        action_needed = [c for c in checks if c["status"] == "ACTION NEEDED"]
        for check in action_needed:
            if "FSA" in check["requirement"]:
                steps.append("1. Visit local FSA office to register and get Farm Number")
            if "Conservation Plan" in check["requirement"]:
                steps.append("2. Schedule meeting with NRCS to develop conservation plan")

        if not action_needed:
            steps.append(f"Ready to apply! Gather documentation for {program_id.upper()}")

        return steps

    # =========================================================================
    # PROPOSAL GENERATION
    # =========================================================================

    def generate_proposal_outline(
        self,
        program_id: str,
        project_data: Dict
    ) -> Dict:
        """
        Generate a proposal outline with suggested content.

        project_data should include:
        - project_title
        - project_description
        - farm_name
        - farm_location
        - farm_acres
        - practices_planned: List of practices to implement
        - expected_outcomes: List of expected outcomes
        - budget_estimate: Estimated total cost
        - timeline_months: Project duration
        """

        program = GRANT_PROGRAMS.get(program_id)
        if not program:
            return {"error": "Program not found"}

        outline = {
            "program": program["name"],
            "project_title": project_data.get("project_title", ""),
            "sections": []
        }

        # Executive Summary
        outline["sections"].append({
            "section": "Executive Summary",
            "suggested_length": "1 page",
            "content_guidance": [
                f"Introduce {project_data.get('farm_name', 'your operation')}",
                f"State the problem/opportunity being addressed",
                f"Summarize proposed {', '.join(project_data.get('practices_planned', [])[:3])}",
                f"Highlight expected outcomes",
                f"State funding request: ${project_data.get('budget_estimate', 0):,}"
            ],
            "sample_opening": (
                f"{project_data.get('farm_name', '[Farm Name]')} requests "
                f"${project_data.get('budget_estimate', 0):,} from {program['name']} to implement "
                f"{', '.join(project_data.get('practices_planned', ['conservation practices'])[:2])} "
                f"on {project_data.get('farm_acres', 0)} acres in {project_data.get('farm_location', '[Location]')}."
            )
        })

        # Need Statement
        outline["sections"].append({
            "section": "Statement of Need",
            "suggested_length": "1-2 pages",
            "content_guidance": [
                "Describe current resource concerns",
                "Provide baseline data (soil health, water quality, etc.)",
                "Explain urgency and importance",
                "Connect to program priorities"
            ],
            "data_to_include": [
                "Current soil test results",
                "Water quality data if available",
                "Historical yield data",
                "Climate/weather challenges"
            ]
        })

        # Project Description
        outline["sections"].append({
            "section": "Project Description",
            "suggested_length": "2-3 pages",
            "content_guidance": [
                "Describe each practice in detail",
                "Explain implementation approach",
                "Provide technical specifications",
                "Describe operation and maintenance"
            ],
            "practices_detail": [
                {
                    "practice": practice,
                    "describe": [
                        "What will be implemented",
                        "Where on the farm",
                        "How it addresses resource concerns",
                        "Expected lifespan"
                    ]
                }
                for practice in project_data.get("practices_planned", [])
            ]
        })

        # Expected Outcomes
        outline["sections"].append({
            "section": "Expected Outcomes & Evaluation",
            "suggested_length": "1-2 pages",
            "content_guidance": [
                "List measurable outcomes",
                "Describe evaluation methods",
                "Provide timeline for achieving outcomes"
            ],
            "suggested_metrics": self._suggest_outcome_metrics(
                project_data.get("practices_planned", [])
            )
        })

        # Budget
        budget_template = self.generate_budget_template(
            program_id,
            project_data.get("practices_planned", []),
            project_data.get("budget_estimate", 0)
        )
        outline["sections"].append({
            "section": "Budget",
            "suggested_length": "1 page + detailed budget form",
            "content_guidance": [
                "Itemize all costs",
                "Show cost-share calculations",
                "Justify costs"
            ],
            "budget_template": budget_template
        })

        # Timeline
        outline["sections"].append({
            "section": "Timeline",
            "suggested_length": "1 page",
            "content_guidance": [
                "Provide month-by-month implementation plan",
                "Identify key milestones",
                "Show evaluation checkpoints"
            ],
            "sample_timeline": self.generate_project_timeline(
                project_data.get("practices_planned", []),
                project_data.get("timeline_months", 12)
            )
        })

        return outline

    def _suggest_outcome_metrics(self, practices: List[str]) -> List[Dict]:
        """Suggest outcome metrics based on practices"""
        metrics_map = {
            "cover crop": [
                {"metric": "Acres planted to cover crops", "measurement": "GPS mapping"},
                {"metric": "Soil organic matter change", "measurement": "Soil testing"},
                {"metric": "Erosion reduction estimate", "measurement": "RUSLE2 modeling"}
            ],
            "no-till": [
                {"metric": "Acres under no-till", "measurement": "GPS mapping"},
                {"metric": "Fuel savings", "measurement": "Fuel records"},
                {"metric": "Soil health improvement", "measurement": "Soil testing"}
            ],
            "nutrient management": [
                {"metric": "Nutrient use efficiency", "measurement": "Soil/tissue testing"},
                {"metric": "Cost savings", "measurement": "Input records"},
                {"metric": "Water quality improvement", "measurement": "Edge-of-field monitoring"}
            ],
            "irrigation": [
                {"metric": "Water savings", "measurement": "Flow meters"},
                {"metric": "Energy savings", "measurement": "Utility bills"},
                {"metric": "Yield impact", "measurement": "Harvest records"}
            ],
            "pollinator": [
                {"metric": "Acres of pollinator habitat", "measurement": "GPS mapping"},
                {"metric": "Pollinator species observed", "measurement": "Visual surveys"},
                {"metric": "Bloom period coverage", "measurement": "Phenology tracking"}
            ]
        }

        suggested = []
        for practice in practices:
            practice_lower = practice.lower()
            for key, metrics in metrics_map.items():
                if key in practice_lower:
                    suggested.extend(metrics)

        return suggested[:6]  # Return top 6 metrics

    def generate_budget_template(
        self,
        program_id: str,
        practices: List[str],
        total_budget: float
    ) -> Dict:
        """Generate a budget template for the grant"""

        program = GRANT_PROGRAMS.get(program_id, {})
        cost_share_rate = program.get("cost_share_rate", 0.5)

        # Practice cost estimates (simplified)
        practice_costs = {
            "cover crops": 45,  # $/acre
            "no-till": 25,  # $/acre equipment modification
            "nutrient management": 15,  # $/acre
            "irrigation efficiency": 200,  # $/acre
            "pollinator habitat": 500,  # $/acre establishment
            "windbreak": 2000,  # per 100 linear feet
            "wetland": 1500,  # $/acre
        }

        line_items = []
        estimated_total = 0

        for practice in practices:
            practice_lower = practice.lower()
            for key, unit_cost in practice_costs.items():
                if key in practice_lower:
                    # Estimate based on typical acreage
                    estimated_quantity = 100  # Default
                    estimated_cost = estimated_quantity * unit_cost
                    estimated_total += estimated_cost

                    line_items.append({
                        "category": practice,
                        "unit_cost": f"${unit_cost}/acre or unit",
                        "estimated_quantity": estimated_quantity,
                        "estimated_cost": estimated_cost
                    })
                    break

        if not line_items:
            estimated_total = total_budget

        grant_request = estimated_total * cost_share_rate
        match_required = estimated_total * (1 - cost_share_rate)

        return {
            "line_items": line_items,
            "totals": {
                "estimated_project_cost": round(estimated_total, 2),
                "grant_request": round(grant_request, 2),
                "cost_share_rate": f"{cost_share_rate * 100:.0f}%",
                "applicant_match": round(match_required, 2),
                "match_rate": f"{(1 - cost_share_rate) * 100:.0f}%"
            },
            "budget_justification_notes": [
                "Include vendor quotes for major items",
                "Document in-kind contributions",
                "Show calculation methodology",
                "Reference NRCS payment schedules where applicable"
            ]
        }

    def generate_project_timeline(
        self,
        practices: List[str],
        duration_months: int
    ) -> List[Dict]:
        """Generate a project timeline"""

        timeline = []

        # Phase 1: Planning (first 1-2 months)
        timeline.append({
            "phase": "Planning & Design",
            "months": "1-2",
            "activities": [
                "Finalize conservation plan with NRCS",
                "Complete site assessments",
                "Obtain necessary permits",
                "Contract with suppliers/contractors"
            ]
        })

        # Phase 2: Implementation
        impl_months = duration_months - 4
        timeline.append({
            "phase": "Implementation",
            "months": f"3-{3 + impl_months}",
            "activities": [
                f"Install/implement {practice}"
                for practice in practices
            ] + [
                "Document progress with photos",
                "Submit interim reports"
            ]
        })

        # Phase 3: Monitoring & Evaluation
        timeline.append({
            "phase": "Monitoring & Evaluation",
            "months": f"{3 + impl_months}-{duration_months}",
            "activities": [
                "Collect baseline and post-implementation data",
                "Conduct effectiveness monitoring",
                "Document outcomes",
                "Prepare final report"
            ]
        })

        return timeline

    # =========================================================================
    # IMPACT METRICS
    # =========================================================================

    def calculate_project_impact(
        self,
        project_data: Dict
    ) -> Dict:
        """
        Calculate expected impact metrics for grant application.

        project_data should include:
        - acres: Project acres
        - practices: List of practices
        - soil_type: Soil type
        - baseline_om: Baseline organic matter %
        - current_yield: Current yield bu/acre
        """

        acres = project_data.get("acres", 100)
        practices = project_data.get("practices", [])

        impacts = {
            "environmental": {},
            "economic": {},
            "social": {}
        }

        # Calculate practice-specific impacts
        for practice in practices:
            practice_lower = practice.lower()

            # Cover crops
            if "cover" in practice_lower:
                impacts["environmental"]["carbon_sequestration_tons"] = round(acres * 0.4, 1)
                impacts["environmental"]["erosion_reduction_tons"] = round(acres * 3.5, 1)
                impacts["environmental"]["nitrogen_capture_lbs"] = round(acres * 40, 0)
                impacts["economic"]["soil_health_value"] = round(acres * 20, 0)

            # No-till
            if "no-till" in practice_lower or "no till" in practice_lower:
                impacts["environmental"]["carbon_sequestration_tons"] += round(acres * 0.5, 1)
                impacts["environmental"]["fuel_gallons_saved"] = round(acres * 2.5, 0)
                impacts["economic"]["fuel_savings"] = round(acres * 2.5 * 3.50, 0)
                impacts["economic"]["labor_savings"] = round(acres * 8, 0)

            # Nutrient management
            if "nutrient" in practice_lower:
                impacts["environmental"]["nitrogen_reduction_lbs"] = round(acres * 25, 0)
                impacts["environmental"]["phosphorus_reduction_lbs"] = round(acres * 5, 0)
                impacts["economic"]["input_savings"] = round(acres * 15, 0)

            # Irrigation efficiency
            if "irrigation" in practice_lower:
                impacts["environmental"]["water_savings_acre_inches"] = round(acres * 3, 0)
                impacts["environmental"]["energy_savings_kwh"] = round(acres * 150, 0)
                impacts["economic"]["water_energy_savings"] = round(acres * 45, 0)

            # Pollinator habitat
            if "pollinator" in practice_lower:
                impacts["environmental"]["pollinator_habitat_acres"] = acres
                impacts["environmental"]["bee_species_supported"] = 25
                impacts["economic"]["pollination_value"] = round(acres * 150, 0)

        # Social impacts
        impacts["social"]["jobs_supported"] = max(1, round(acres / 500, 1))
        impacts["social"]["knowledge_transfer"] = "Field days and publications"
        impacts["social"]["community_benefit"] = "Improved water quality and ecosystem services"

        # ROI calculation
        total_environmental_value = sum(
            v for k, v in impacts["environmental"].items()
            if isinstance(v, (int, float)) and "value" not in k
        ) * 5  # Rough value per unit

        total_economic_value = sum(
            v for v in impacts["economic"].values()
            if isinstance(v, (int, float))
        )

        return {
            "project_acres": acres,
            "practices_analyzed": practices,
            "impacts": impacts,
            "summary": {
                "total_environmental_benefits": f"~${round(total_environmental_value, 0):,}/year",
                "total_economic_benefits": f"${round(total_economic_value, 0):,}/year",
                "benefit_cost_ratio": round((total_environmental_value + total_economic_value) /
                                           project_data.get("budget", 10000), 2)
            },
            "grant_talking_points": [
                f"Project will sequester an estimated {impacts['environmental'].get('carbon_sequestration_tons', 0)} tons of carbon annually",
                f"Economic benefits of ${round(total_economic_value, 0):,} per year",
                f"Environmental benefits valued at ~${round(total_environmental_value, 0):,} annually",
                f"Project supports {impacts['social']['jobs_supported']} jobs"
            ]
        }

    # =========================================================================
    # APPLICATION TRACKING
    # =========================================================================

    def create_application(self, app_data: Dict) -> Dict:
        """Create a new grant application tracking record"""

        application = GrantApplication(
            application_id=f"APP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            grant_program=app_data.get("grant_program", ""),
            status=GrantStatus.IDENTIFIED,
            project_title=app_data.get("project_title", ""),
            requested_amount=app_data.get("requested_amount", 0),
            match_amount=app_data.get("match_amount", 0),
            deadline=app_data.get("deadline"),
            contact_person=app_data.get("contact_person", "")
        )

        self.applications.append(application)

        return {
            "success": True,
            "application_id": application.application_id,
            "program": application.grant_program,
            "status": application.status.value,
            "message": "Application tracking started"
        }

    def update_application_status(
        self,
        application_id: str,
        new_status: GrantStatus,
        details: Dict = None
    ) -> Dict:
        """Update application status"""

        app = next((a for a in self.applications if a.application_id == application_id), None)
        if not app:
            return {"success": False, "message": "Application not found"}

        old_status = app.status
        app.status = new_status

        if details:
            if new_status == GrantStatus.SUBMITTED:
                app.submission_date = details.get("submission_date", date.today())
                app.documents_submitted = details.get("documents", [])
            elif new_status == GrantStatus.AWARDED:
                app.award_date = details.get("award_date", date.today())
                app.award_amount = details.get("award_amount", app.requested_amount)
                app.project_period_start = details.get("start_date")
                app.project_period_end = details.get("end_date")

        return {
            "success": True,
            "application_id": application_id,
            "previous_status": old_status.value,
            "new_status": new_status.value,
            "message": f"Status updated to {new_status.value}"
        }

    def get_application_dashboard(self) -> Dict:
        """Get overview of all grant applications"""

        if not self.applications:
            return {
                "total_applications": 0,
                "message": "No applications tracked"
            }

        by_status = {}
        for app in self.applications:
            status = app.status.value
            if status not in by_status:
                by_status[status] = []
            by_status[status].append({
                "id": app.application_id,
                "program": app.grant_program,
                "title": app.project_title,
                "amount": app.requested_amount,
                "deadline": app.deadline.isoformat() if app.deadline else None
            })

        # Calculate totals
        total_requested = sum(a.requested_amount for a in self.applications)
        total_awarded = sum(a.award_amount for a in self.applications if a.status == GrantStatus.AWARDED)

        # Upcoming deadlines
        upcoming = [
            {
                "id": a.application_id,
                "program": a.grant_program,
                "deadline": a.deadline.isoformat(),
                "days_until": (a.deadline - date.today()).days
            }
            for a in self.applications
            if a.deadline and a.deadline >= date.today() and a.status in [GrantStatus.IDENTIFIED, GrantStatus.PREPARING]
        ]
        upcoming.sort(key=lambda x: x["days_until"])

        return {
            "total_applications": len(self.applications),
            "by_status": by_status,
            "financials": {
                "total_requested": round(total_requested, 0),
                "total_awarded": round(total_awarded, 0),
                "success_rate": round(
                    len([a for a in self.applications if a.status == GrantStatus.AWARDED]) /
                    len([a for a in self.applications if a.status in [GrantStatus.AWARDED, GrantStatus.REJECTED]]) * 100, 0
                ) if any(a.status in [GrantStatus.AWARDED, GrantStatus.REJECTED] for a in self.applications) else 0
            },
            "upcoming_deadlines": upcoming[:5],
            "action_items": self._get_application_action_items()
        }

    def _get_application_action_items(self) -> List[str]:
        """Get priority action items for applications"""
        actions = []

        for app in self.applications:
            if app.deadline and app.status == GrantStatus.PREPARING:
                days_left = (app.deadline - date.today()).days
                if days_left <= 14:
                    actions.append(f"URGENT: {app.grant_program} deadline in {days_left} days")
                elif days_left <= 30:
                    actions.append(f"{app.grant_program} deadline in {days_left} days - finalize application")

            if app.status == GrantStatus.IDENTIFIED:
                actions.append(f"Start preparing {app.grant_program} application")

        return actions[:5]

    # =========================================================================
    # SUCCESS SCORING
    # =========================================================================

    def calculate_success_probability(
        self,
        program_id: str,
        application_strength: Dict
    ) -> Dict:
        """
        Calculate estimated success probability.

        application_strength should include:
        - eligibility_score: From eligibility assessment
        - proposal_completeness: 0-100
        - prior_awards: Number of prior grants
        - partnerships: Number of partner organizations
        - data_quality: 0-100 (baseline data availability)
        - innovation: 0-100 (innovation score)
        - match_availability: Boolean
        """

        program = GRANT_PROGRAMS.get(program_id)
        if not program:
            return {"error": "Program not found"}

        # Base probability by program type
        base_probabilities = {
            "eqip": 0.65,  # High success rate
            "csp": 0.55,
            "sare_producer": 0.30,  # Competitive
            "reap": 0.50,
            "value_added_producer": 0.25,  # Very competitive
            "specialty_crop_block": 0.35
        }

        base_prob = base_probabilities.get(program_id, 0.40)

        # Adjust for application factors
        adjustments = []

        # Eligibility
        elig_score = application_strength.get("eligibility_score", 70)
        if elig_score >= 90:
            base_prob += 0.10
            adjustments.append("+10%: Strong eligibility")
        elif elig_score < 70:
            base_prob -= 0.15
            adjustments.append("-15%: Eligibility concerns")

        # Proposal completeness
        completeness = application_strength.get("proposal_completeness", 70)
        if completeness >= 90:
            base_prob += 0.10
            adjustments.append("+10%: Complete proposal")
        elif completeness < 60:
            base_prob -= 0.20
            adjustments.append("-20%: Incomplete proposal")

        # Prior awards (track record)
        prior = application_strength.get("prior_awards", 0)
        if prior >= 2:
            base_prob += 0.08
            adjustments.append("+8%: Proven track record")

        # Partnerships
        partners = application_strength.get("partnerships", 0)
        if partners >= 2:
            base_prob += 0.07
            adjustments.append("+7%: Strong partnerships")

        # Data quality
        data_quality = application_strength.get("data_quality", 50)
        if data_quality >= 80:
            base_prob += 0.08
            adjustments.append("+8%: Strong baseline data")

        # Match availability
        has_match = application_strength.get("match_availability", True)
        if not has_match and program["cost_share_rate"] < 1.0:
            base_prob -= 0.20
            adjustments.append("-20%: Match funding uncertain")

        # Clamp probability
        final_prob = max(0.05, min(0.90, base_prob))

        return {
            "program_id": program_id,
            "program_name": program["name"],
            "base_probability": base_probabilities.get(program_id, 0.40),
            "adjusted_probability": round(final_prob, 2),
            "probability_percent": f"{round(final_prob * 100, 0)}%",
            "adjustments": adjustments,
            "confidence": "Medium - based on general program statistics",
            "improvement_suggestions": self._get_probability_improvements(
                application_strength, final_prob
            )
        }

    def _get_probability_improvements(
        self,
        strengths: Dict,
        current_prob: float
    ) -> List[str]:
        """Get suggestions to improve success probability"""
        suggestions = []

        if strengths.get("eligibility_score", 70) < 90:
            suggestions.append("Address eligibility gaps before applying")

        if strengths.get("proposal_completeness", 70) < 90:
            suggestions.append("Complete all proposal sections thoroughly")

        if strengths.get("data_quality", 50) < 80:
            suggestions.append("Gather baseline data (soil tests, yields, etc.)")

        if strengths.get("partnerships", 0) < 2:
            suggestions.append("Develop partnerships with extension, universities, or other producers")

        if not suggestions:
            suggestions.append("Strong application - submit early and follow up")

        return suggestions[:4]

    # =========================================================================
    # REPORTING
    # =========================================================================

    def generate_grant_portfolio_report(self) -> Dict:
        """Generate comprehensive grant portfolio report"""

        dashboard = self.get_application_dashboard()

        awarded = [a for a in self.applications if a.status == GrantStatus.AWARDED]
        completed = [a for a in self.applications if a.status == GrantStatus.COMPLETED]

        return {
            "report_title": "Grant Portfolio Report",
            "generated_date": datetime.now().isoformat(),
            "portfolio_summary": {
                "total_applications": dashboard.get("total_applications", 0),
                "total_requested": dashboard.get("financials", {}).get("total_requested", 0),
                "total_awarded": dashboard.get("financials", {}).get("total_awarded", 0),
                "success_rate": dashboard.get("financials", {}).get("success_rate", 0)
            },
            "active_grants": [
                {
                    "program": a.grant_program,
                    "title": a.project_title,
                    "award_amount": a.award_amount,
                    "period": f"{a.project_period_start} to {a.project_period_end}"
                    if a.project_period_start and a.project_period_end else "TBD"
                }
                for a in awarded
            ],
            "completed_grants": [
                {
                    "program": a.grant_program,
                    "award_amount": a.award_amount
                }
                for a in completed
            ],
            "upcoming_opportunities": dashboard.get("upcoming_deadlines", []),
            "action_items": dashboard.get("action_items", []),
            "grant_capacity": {
                "current_active_grants": len(awarded),
                "capacity_for_new_grants": "High" if len(awarded) < 3 else "Medium" if len(awarded) < 5 else "Limited",
                "recommended_next_grant": self._recommend_next_grant()
            }
        }

    def _recommend_next_grant(self) -> str:
        """Recommend next grant to pursue"""
        current_programs = [a.grant_program for a in self.applications]

        priorities = ["eqip", "csp", "sare_producer", "reap"]

        for prog in priorities:
            if prog not in current_programs:
                return GRANT_PROGRAMS[prog]["name"]

        return "Consider advanced programs or expanding existing conservation"


# Create singleton instance
grant_assistant_service = GrantAssistantService()
