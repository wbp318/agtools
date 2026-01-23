"""
Grant Operations Service for AgTools
Version: 3.7.0

This service provides comprehensive grant operations support:
- Grant Application Manager (deadlines, requirements, status tracking)
- Regulatory Compliance Tracker (EPA WPS, licenses, RUP records)
- Enterprise Budgets & Scenarios (crop budgets, break-even, projections)
- Outreach & Impact Tracker (field days, presentations, publications)
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

# ----- Grant Application Manager -----

class ApplicationStatus(Enum):
    """Grant application status"""
    IDENTIFIED = "identified"
    PREPARING = "preparing"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    AWARDED = "awarded"
    NOT_FUNDED = "not_funded"
    WITHDRAWN = "withdrawn"


class DocumentStatus(Enum):
    """Required document status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    SUBMITTED = "submitted"


@dataclass
class GrantApplication:
    """Grant application record"""
    id: str
    program: str
    program_name: str
    funding_amount: float
    deadline: date
    status: ApplicationStatus
    project_title: str
    project_description: str
    required_documents: Dict[str, DocumentStatus]
    submitted_date: Optional[date]
    decision_date: Optional[date]
    notes: str
    created_date: date


# ----- Regulatory Compliance -----

class LicenseType(Enum):
    """Types of regulatory licenses"""
    PRIVATE_APPLICATOR = "private_applicator"
    COMMERCIAL_APPLICATOR = "commercial_applicator"
    RUP_DEALER = "rup_dealer"
    SEED_DEALER = "seed_dealer"
    FERTILIZER_DEALER = "fertilizer_dealer"
    GRAIN_DEALER = "grain_dealer"


class ComplianceCategory(Enum):
    """Compliance categories"""
    PESTICIDE = "pesticide"
    WORKER_PROTECTION = "worker_protection"
    ENVIRONMENTAL = "environmental"
    FOOD_SAFETY = "food_safety"
    LABOR = "labor"
    EQUIPMENT = "equipment"


@dataclass
class License:
    """License/certification record"""
    id: str
    license_type: LicenseType
    license_number: str
    holder_name: str
    issue_date: date
    expiration_date: date
    issuing_authority: str
    categories: List[str]  # Pesticide categories like 1a, 1b, 10, etc.
    ceu_required: int
    ceu_earned: int
    status: str  # active, expired, pending_renewal


@dataclass
class RUPRecord:
    """Restricted Use Pesticide application record"""
    id: str
    application_date: date
    product_name: str
    epa_reg_number: str
    active_ingredient: str
    field_name: str
    acres_treated: float
    rate_per_acre: float
    rate_unit: str
    total_amount: float
    target_pest: str
    applicator_name: str
    applicator_license: str
    weather_conditions: Dict[str, Any]
    rei_hours: int
    phi_days: int
    notes: str


@dataclass
class WPSRecord:
    """Worker Protection Standard compliance record"""
    id: str
    record_type: str  # training, notification, decontamination, etc.
    date: date
    description: str
    participants: List[str]
    trainer: Optional[str]
    documentation_path: Optional[str]
    next_due: Optional[date]


# ----- Enterprise Budgets -----

class CropType(Enum):
    """Crop types for budgeting"""
    CORN = "corn"
    SOYBEANS = "soybeans"
    WHEAT = "wheat"
    COTTON = "cotton"
    RICE = "rice"
    GRAIN_SORGHUM = "grain_sorghum"


@dataclass
class EnterpriseBudget:
    """Crop enterprise budget"""
    id: str
    crop: CropType
    year: int
    acres: float
    expected_yield: float
    expected_price: float

    # Revenue
    gross_revenue: float
    crop_insurance: float
    other_revenue: float
    total_revenue: float

    # Variable costs
    seed: float
    fertilizer: float
    chemicals: float
    crop_insurance_premium: float
    custom_hire: float
    fuel_lube: float
    repairs: float
    drying: float
    hauling: float
    other_variable: float
    total_variable: float

    # Fixed costs
    land_rent: float
    equipment_depreciation: float
    equipment_interest: float
    labor: float
    overhead: float
    total_fixed: float

    # Returns
    total_costs: float
    net_return: float
    return_per_acre: float
    break_even_yield: float
    break_even_price: float


# ----- Outreach & Impact -----

class OutreachType(Enum):
    """Types of outreach activities"""
    FIELD_DAY = "field_day"
    PRESENTATION = "presentation"
    PUBLICATION = "publication"
    MEDIA_INTERVIEW = "media_interview"
    WORKSHOP = "workshop"
    FARM_TOUR = "farm_tour"
    WEBINAR = "webinar"
    SOCIAL_MEDIA = "social_media"
    PODCAST = "podcast"
    NEWSLETTER = "newsletter"


@dataclass
class OutreachActivity:
    """Outreach activity record"""
    id: str
    activity_type: OutreachType
    title: str
    date: date
    description: str
    audience: str
    attendance: int
    location: str
    partners: List[str]
    topics: List[str]
    materials_path: Optional[str]
    follow_up_contacts: int
    notes: str


@dataclass
class Publication:
    """Publication record"""
    id: str
    pub_type: str  # journal, extension, trade, blog, etc.
    title: str
    authors: List[str]
    publication_venue: str
    date: date
    doi_or_url: Optional[str]
    abstract: str
    keywords: List[str]
    grant_acknowledgment: Optional[str]


# =============================================================================
# GRANT PROGRAM DATABASE
# =============================================================================

GRANT_PROGRAMS = {
    "USDA_SBIR": {
        "name": "USDA SBIR/STTR Phase I",
        "agency": "USDA NIFA",
        "funding_range": (125000, 175000),
        "typical_deadline_month": 1,  # January
        "required_documents": [
            "Technical Proposal (15 pages)",
            "Budget and Budget Justification",
            "Biographical Sketches",
            "Current/Pending Support",
            "Facilities/Equipment",
            "Data Management Plan",
            "Letters of Support",
            "Commercialization Plan"
        ],
        "timeline_weeks": 12,
        "review_period_months": 6
    },
    "SARE_PRODUCER": {
        "name": "Southern SARE Producer Grant",
        "agency": "USDA SARE",
        "funding_range": (10000, 30000),
        "typical_deadline_month": 5,  # May
        "required_documents": [
            "Project Narrative",
            "Budget",
            "Farm Description",
            "Outreach Plan",
            "Timeline",
            "Letters of Support"
        ],
        "timeline_weeks": 8,
        "review_period_months": 3
    },
    "CIG": {
        "name": "Conservation Innovation Grant",
        "agency": "USDA NRCS",
        "funding_range": (250000, 2000000),
        "typical_deadline_month": 6,  # June
        "required_documents": [
            "Project Narrative",
            "Budget SF-424",
            "Letters of Commitment",
            "Environmental Compliance",
            "Logic Model",
            "Evaluation Plan",
            "Match Documentation"
        ],
        "timeline_weeks": 16,
        "review_period_months": 4
    },
    "EQIP": {
        "name": "Environmental Quality Incentives Program",
        "agency": "USDA NRCS",
        "funding_range": (5000, 450000),
        "typical_deadline_month": 0,  # Rolling
        "required_documents": [
            "Application CPA-1200",
            "Conservation Plan",
            "Farm Maps",
            "Soil Survey Data",
            "Environmental Evaluation"
        ],
        "timeline_weeks": 4,
        "review_period_months": 2
    },
    "LA_ON_FARM": {
        "name": "Louisiana On Farm Research Grant",
        "agency": "LSSAC",
        "funding_range": (10000, 50000),
        "typical_deadline_month": 11,  # November
        "required_documents": [
            "Project Proposal",
            "Budget",
            "Farm Operation Description",
            "Research Plan",
            "Outreach Component"
        ],
        "timeline_weeks": 6,
        "review_period_months": 2
    },
    "NSF_SBIR": {
        "name": "NSF SBIR Phase I",
        "agency": "National Science Foundation",
        "funding_range": (275000, 275000),
        "typical_deadline_month": 0,  # Rolling
        "required_documents": [
            "Project Pitch (required first)",
            "Full Proposal",
            "Budget",
            "Biographical Sketches",
            "Current/Pending Support",
            "Commercialization Plan",
            "Letters of Support"
        ],
        "timeline_weeks": 12,
        "review_period_months": 5
    },
}


# =============================================================================
# LOUISIANA CROP BUDGET DEFAULTS (2024/2025)
# =============================================================================

CROP_BUDGET_DEFAULTS = {
    CropType.CORN: {
        "expected_yield": 180,
        "expected_price": 4.75,
        "seed": 120.00,
        "fertilizer": 180.00,
        "chemicals": 85.00,
        "crop_insurance_premium": 35.00,
        "custom_hire": 25.00,
        "fuel_lube": 45.00,
        "repairs": 35.00,
        "drying": 30.00,
        "hauling": 15.00,
        "other_variable": 20.00,
        "land_rent": 180.00,
        "equipment_depreciation": 65.00,
        "equipment_interest": 25.00,
        "labor": 30.00,
        "overhead": 20.00,
        "unit": "bu/acre"
    },
    CropType.SOYBEANS: {
        "expected_yield": 50,
        "expected_price": 11.50,
        "seed": 65.00,
        "fertilizer": 45.00,
        "chemicals": 75.00,
        "crop_insurance_premium": 25.00,
        "custom_hire": 20.00,
        "fuel_lube": 35.00,
        "repairs": 30.00,
        "drying": 0.00,
        "hauling": 12.00,
        "other_variable": 15.00,
        "land_rent": 180.00,
        "equipment_depreciation": 55.00,
        "equipment_interest": 20.00,
        "labor": 25.00,
        "overhead": 18.00,
        "unit": "bu/acre"
    },
    CropType.RICE: {
        "expected_yield": 7200,
        "expected_price": 0.075,  # per lb
        "seed": 45.00,
        "fertilizer": 150.00,
        "chemicals": 120.00,
        "crop_insurance_premium": 40.00,
        "custom_hire": 80.00,  # Water pumping
        "fuel_lube": 60.00,
        "repairs": 45.00,
        "drying": 55.00,
        "hauling": 20.00,
        "other_variable": 25.00,
        "land_rent": 200.00,
        "equipment_depreciation": 70.00,
        "equipment_interest": 28.00,
        "labor": 35.00,
        "overhead": 22.00,
        "unit": "lbs/acre"
    },
    CropType.COTTON: {
        "expected_yield": 1100,
        "expected_price": 0.75,  # per lb
        "seed": 85.00,
        "fertilizer": 140.00,
        "chemicals": 180.00,
        "crop_insurance_premium": 55.00,
        "custom_hire": 120.00,  # Picking
        "fuel_lube": 50.00,
        "repairs": 40.00,
        "drying": 0.00,
        "hauling": 25.00,
        "other_variable": 30.00,
        "land_rent": 175.00,
        "equipment_depreciation": 75.00,
        "equipment_interest": 30.00,
        "labor": 35.00,
        "overhead": 22.00,
        "unit": "lbs/acre"
    },
    CropType.WHEAT: {
        "expected_yield": 55,
        "expected_price": 5.50,
        "seed": 35.00,
        "fertilizer": 95.00,
        "chemicals": 55.00,
        "crop_insurance_premium": 20.00,
        "custom_hire": 15.00,
        "fuel_lube": 30.00,
        "repairs": 25.00,
        "drying": 10.00,
        "hauling": 10.00,
        "other_variable": 12.00,
        "land_rent": 150.00,
        "equipment_depreciation": 45.00,
        "equipment_interest": 18.00,
        "labor": 20.00,
        "overhead": 15.00,
        "unit": "bu/acre"
    },
    CropType.GRAIN_SORGHUM: {
        "expected_yield": 95,
        "expected_price": 4.25,
        "seed": 25.00,
        "fertilizer": 110.00,
        "chemicals": 65.00,
        "crop_insurance_premium": 22.00,
        "custom_hire": 18.00,
        "fuel_lube": 38.00,
        "repairs": 28.00,
        "drying": 20.00,
        "hauling": 12.00,
        "other_variable": 15.00,
        "land_rent": 160.00,
        "equipment_depreciation": 50.00,
        "equipment_interest": 20.00,
        "labor": 22.00,
        "overhead": 16.00,
        "unit": "bu/acre"
    },
}


# =============================================================================
# COMPLIANCE REQUIREMENTS
# =============================================================================

COMPLIANCE_REQUIREMENTS = {
    "pesticide_applicator": {
        "name": "Private Pesticide Applicator License",
        "authority": "Louisiana Department of Agriculture and Forestry",
        "renewal_years": 3,
        "ceu_required": 12,
        "requirements": [
            "Pass certification exam",
            "Complete training program",
            "Pay license fee",
            "Maintain CEU credits"
        ],
        "categories": {
            "1a": "Agricultural Plant Pest Control",
            "1b": "Agricultural Animal Pest Control",
            "10": "Demonstration and Research",
            "1c": "Forest Pest Control",
            "1d": "Seed Treatment"
        }
    },
    "wps_training": {
        "name": "EPA Worker Protection Standard Training",
        "authority": "EPA",
        "renewal_years": 1,
        "requirements": [
            "Annual training for handlers and workers",
            "Training before working with pesticides",
            "Training in language workers understand",
            "Maintain training records for 2 years"
        ]
    },
    "rup_records": {
        "name": "Restricted Use Pesticide Records",
        "authority": "EPA / State",
        "retention_years": 2,
        "required_info": [
            "Product name and EPA registration number",
            "Total amount applied",
            "Acres treated",
            "Date and time of application",
            "Location (field)",
            "Target pest",
            "Applicator name and certification number"
        ]
    },
    "pesticide_storage": {
        "name": "Pesticide Storage Requirements",
        "authority": "EPA / State",
        "requirements": [
            "Secure, locked storage",
            "Proper ventilation",
            "Spill containment",
            "Emergency contact information posted",
            "SDS sheets available"
        ]
    }
}


# =============================================================================
# GRANT OPERATIONS SERVICE CLASS
# =============================================================================

class GrantOperationsService:
    """Service for grant operations management"""

    def __init__(self):
        self.applications: Dict[str, GrantApplication] = {}
        self.licenses: Dict[str, License] = {}
        self.rup_records: Dict[str, RUPRecord] = {}
        self.wps_records: Dict[str, WPSRecord] = {}
        self.budgets: Dict[str, EnterpriseBudget] = {}
        self.outreach: Dict[str, OutreachActivity] = {}
        self.publications: Dict[str, Publication] = {}

        self._counters = {
            "app": 0, "lic": 0, "rup": 0, "wps": 0,
            "budget": 0, "outreach": 0, "pub": 0
        }

    def _next_id(self, prefix: str) -> str:
        self._counters[prefix] += 1
        return f"{prefix.upper()}-{self._counters[prefix]:04d}"

    # -------------------------------------------------------------------------
    # GRANT APPLICATION MANAGER
    # -------------------------------------------------------------------------

    def get_grant_programs(self) -> List[Dict[str, Any]]:
        """Get list of available grant programs with details"""
        return [
            {
                "id": prog_id,
                "name": info["name"],
                "agency": info["agency"],
                "funding_range": {
                    "min": info["funding_range"][0],
                    "max": info["funding_range"][1]
                },
                "typical_deadline_month": info["typical_deadline_month"],
                "required_documents": info["required_documents"],
                "timeline_weeks": info["timeline_weeks"],
                "review_period_months": info["review_period_months"]
            }
            for prog_id, info in GRANT_PROGRAMS.items()
        ]

    def create_application(
        self,
        program: str,
        project_title: str,
        project_description: str,
        funding_amount: float,
        deadline: date,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Create a new grant application"""
        if program not in GRANT_PROGRAMS:
            return {"error": f"Unknown program: {program}"}

        prog_info = GRANT_PROGRAMS[program]
        app_id = self._next_id("app")

        # Initialize required documents
        req_docs = {doc: DocumentStatus.NOT_STARTED for doc in prog_info["required_documents"]}

        application = GrantApplication(
            id=app_id,
            program=program,
            program_name=prog_info["name"],
            funding_amount=funding_amount,
            deadline=deadline,
            status=ApplicationStatus.IDENTIFIED,
            project_title=project_title,
            project_description=project_description,
            required_documents=req_docs,
            submitted_date=None,
            decision_date=None,
            notes=notes,
            created_date=date.today()
        )

        self.applications[app_id] = application

        days_until = (deadline - date.today()).days

        return {
            "id": app_id,
            "program": program,
            "program_name": prog_info["name"],
            "project_title": project_title,
            "funding_amount": funding_amount,
            "deadline": deadline.isoformat(),
            "days_until_deadline": days_until,
            "status": application.status.value,
            "required_documents": len(req_docs),
            "message": f"Application created for {prog_info['name']} - {days_until} days until deadline"
        }

    def update_application_status(
        self,
        application_id: str,
        status: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Update application status"""
        if application_id not in self.applications:
            return {"error": f"Application {application_id} not found"}

        try:
            new_status = ApplicationStatus(status)
        except ValueError:
            return {"error": f"Invalid status: {status}"}

        app = self.applications[application_id]
        old_status = app.status
        app.status = new_status

        if new_status == ApplicationStatus.SUBMITTED:
            app.submitted_date = date.today()
        elif new_status in [ApplicationStatus.AWARDED, ApplicationStatus.NOT_FUNDED]:
            app.decision_date = date.today()

        if notes:
            app.notes += f"\n{date.today()}: {notes}"

        return {
            "id": application_id,
            "previous_status": old_status.value,
            "new_status": new_status.value,
            "submitted_date": app.submitted_date.isoformat() if app.submitted_date else None,
            "decision_date": app.decision_date.isoformat() if app.decision_date else None
        }

    def update_document_status(
        self,
        application_id: str,
        document_name: str,
        status: str
    ) -> Dict[str, Any]:
        """Update status of a required document"""
        if application_id not in self.applications:
            return {"error": f"Application {application_id} not found"}

        try:
            doc_status = DocumentStatus(status)
        except ValueError:
            return {"error": f"Invalid status: {status}"}

        app = self.applications[application_id]

        if document_name not in app.required_documents:
            return {"error": f"Document '{document_name}' not in required list"}

        app.required_documents[document_name] = doc_status

        # Calculate completion
        total = len(app.required_documents)
        complete = sum(1 for s in app.required_documents.values()
                      if s in [DocumentStatus.COMPLETE, DocumentStatus.SUBMITTED])
        in_progress = sum(1 for s in app.required_documents.values()
                        if s == DocumentStatus.IN_PROGRESS)

        return {
            "application_id": application_id,
            "document": document_name,
            "status": doc_status.value,
            "progress": {
                "total_documents": total,
                "complete": complete,
                "in_progress": in_progress,
                "not_started": total - complete - in_progress,
                "completion_pct": round(complete / total * 100, 1)
            }
        }

    def get_application_summary(self, application_id: str) -> Dict[str, Any]:
        """Get detailed summary of an application"""
        if application_id not in self.applications:
            return {"error": f"Application {application_id} not found"}

        app = self.applications[application_id]
        days_until = (app.deadline - date.today()).days

        doc_status = {}
        for doc, status in app.required_documents.items():
            doc_status[doc] = status.value

        complete_count = sum(1 for s in app.required_documents.values()
                           if s in [DocumentStatus.COMPLETE, DocumentStatus.SUBMITTED])

        return {
            "id": app.id,
            "program": app.program,
            "program_name": app.program_name,
            "project_title": app.project_title,
            "project_description": app.project_description,
            "funding_amount": app.funding_amount,
            "deadline": app.deadline.isoformat(),
            "days_until_deadline": days_until,
            "status": app.status.value,
            "documents": doc_status,
            "document_progress": {
                "complete": complete_count,
                "total": len(app.required_documents),
                "pct": round(complete_count / len(app.required_documents) * 100, 1)
            },
            "submitted_date": app.submitted_date.isoformat() if app.submitted_date else None,
            "decision_date": app.decision_date.isoformat() if app.decision_date else None,
            "notes": app.notes,
            "urgency": "critical" if days_until < 14 else "high" if days_until < 30 else "normal"
        }

    def get_upcoming_deadlines(self, days_ahead: int = 90) -> List[Dict[str, Any]]:
        """Get applications with upcoming deadlines"""
        cutoff = date.today() + timedelta(days=days_ahead)
        upcoming = []

        for app in self.applications.values():
            if app.status in [ApplicationStatus.IDENTIFIED, ApplicationStatus.PREPARING]:
                if app.deadline <= cutoff:
                    days_until = (app.deadline - date.today()).days
                    complete = sum(1 for s in app.required_documents.values()
                                  if s in [DocumentStatus.COMPLETE, DocumentStatus.SUBMITTED])
                    total = len(app.required_documents)

                    upcoming.append({
                        "id": app.id,
                        "program_name": app.program_name,
                        "project_title": app.project_title,
                        "deadline": app.deadline.isoformat(),
                        "days_until": days_until,
                        "status": app.status.value,
                        "document_progress": f"{complete}/{total}",
                        "funding_amount": app.funding_amount,
                        "urgency": "critical" if days_until < 14 else "high" if days_until < 30 else "normal"
                    })

        upcoming.sort(key=lambda x: x["days_until"])
        return upcoming

    def get_application_dashboard(self) -> Dict[str, Any]:
        """Get dashboard summary of all applications"""
        by_status = {}
        total_requested = 0
        total_awarded = 0

        for app in self.applications.values():
            status = app.status.value
            by_status[status] = by_status.get(status, 0) + 1
            total_requested += app.funding_amount
            if app.status == ApplicationStatus.AWARDED:
                total_awarded += app.funding_amount

        upcoming = self.get_upcoming_deadlines(30)

        return {
            "total_applications": len(self.applications),
            "by_status": by_status,
            "total_funding_requested": total_requested,
            "total_funding_awarded": total_awarded,
            "upcoming_30_days": len(upcoming),
            "critical_deadlines": [u for u in upcoming if u["urgency"] == "critical"],
            "success_rate": round(
                by_status.get("awarded", 0) /
                (by_status.get("awarded", 0) + by_status.get("not_funded", 0)) * 100, 1
            ) if (by_status.get("awarded", 0) + by_status.get("not_funded", 0)) > 0 else None
        }

    # -------------------------------------------------------------------------
    # REGULATORY COMPLIANCE TRACKER
    # -------------------------------------------------------------------------

    def get_compliance_requirements(self) -> Dict[str, Any]:
        """Get list of compliance requirements"""
        return COMPLIANCE_REQUIREMENTS

    def add_license(
        self,
        license_type: str,
        license_number: str,
        holder_name: str,
        issue_date: date,
        expiration_date: date,
        issuing_authority: str,
        categories: List[str] = None,
        ceu_required: int = 0,
        ceu_earned: int = 0
    ) -> Dict[str, Any]:
        """Add a license/certification record"""
        try:
            lic_type = LicenseType(license_type)
        except ValueError:
            return {"error": f"Invalid license type: {license_type}"}

        lic_id = self._next_id("lic")
        days_until_exp = (expiration_date - date.today()).days
        status = "active" if days_until_exp > 0 else "expired"
        if 0 < days_until_exp <= 90:
            status = "expiring_soon"

        license = License(
            id=lic_id,
            license_type=lic_type,
            license_number=license_number,
            holder_name=holder_name,
            issue_date=issue_date,
            expiration_date=expiration_date,
            issuing_authority=issuing_authority,
            categories=categories or [],
            ceu_required=ceu_required,
            ceu_earned=ceu_earned,
            status=status
        )

        self.licenses[lic_id] = license

        return {
            "id": lic_id,
            "license_type": license_type,
            "license_number": license_number,
            "holder_name": holder_name,
            "expiration_date": expiration_date.isoformat(),
            "days_until_expiration": days_until_exp,
            "status": status,
            "ceu_progress": f"{ceu_earned}/{ceu_required}" if ceu_required > 0 else "N/A",
            "message": f"License {license_number} added - expires in {days_until_exp} days"
        }

    def record_ceu(
        self,
        license_id: str,
        ceu_amount: float,
        course_name: str,
        completion_date: date
    ) -> Dict[str, Any]:
        """Record CEU credits earned"""
        if license_id not in self.licenses:
            return {"error": f"License {license_id} not found"}

        lic = self.licenses[license_id]
        lic.ceu_earned += ceu_amount

        return {
            "license_id": license_id,
            "course_name": course_name,
            "ceu_added": ceu_amount,
            "ceu_total": lic.ceu_earned,
            "ceu_required": lic.ceu_required,
            "ceu_remaining": max(0, lic.ceu_required - lic.ceu_earned),
            "requirement_met": lic.ceu_earned >= lic.ceu_required
        }

    def record_rup_application(
        self,
        application_date: date,
        product_name: str,
        epa_reg_number: str,
        active_ingredient: str,
        field_name: str,
        acres_treated: float,
        rate_per_acre: float,
        rate_unit: str,
        target_pest: str,
        applicator_name: str,
        applicator_license: str,
        wind_speed_mph: float = 0,
        temperature_f: float = 0,
        humidity_pct: float = 0,
        rei_hours: int = 0,
        phi_days: int = 0,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Record a restricted use pesticide application"""
        rup_id = self._next_id("rup")

        record = RUPRecord(
            id=rup_id,
            application_date=application_date,
            product_name=product_name,
            epa_reg_number=epa_reg_number,
            active_ingredient=active_ingredient,
            field_name=field_name,
            acres_treated=acres_treated,
            rate_per_acre=rate_per_acre,
            rate_unit=rate_unit,
            total_amount=acres_treated * rate_per_acre,
            target_pest=target_pest,
            applicator_name=applicator_name,
            applicator_license=applicator_license,
            weather_conditions={
                "wind_speed_mph": wind_speed_mph,
                "temperature_f": temperature_f,
                "humidity_pct": humidity_pct
            },
            rei_hours=rei_hours,
            phi_days=phi_days,
            notes=notes
        )

        self.rup_records[rup_id] = record

        rei_end = datetime.combine(application_date, datetime.min.time()) + timedelta(hours=rei_hours)
        phi_end = application_date + timedelta(days=phi_days)

        return {
            "id": rup_id,
            "product_name": product_name,
            "epa_reg_number": epa_reg_number,
            "field_name": field_name,
            "acres_treated": acres_treated,
            "total_amount": f"{acres_treated * rate_per_acre:.2f} {rate_unit}",
            "applicator": applicator_name,
            "rei_ends": rei_end.isoformat(),
            "phi_ends": phi_end.isoformat(),
            "message": f"RUP application recorded - REI ends {rei_end.strftime('%m/%d %H:%M')}"
        }

    def record_wps_activity(
        self,
        record_type: str,
        activity_date: date,
        description: str,
        participants: List[str],
        trainer: str = None,
        documentation_path: str = None,
        next_due: date = None
    ) -> Dict[str, Any]:
        """Record a WPS compliance activity"""
        wps_id = self._next_id("wps")

        record = WPSRecord(
            id=wps_id,
            record_type=record_type,
            date=activity_date,
            description=description,
            participants=participants,
            trainer=trainer,
            documentation_path=documentation_path,
            next_due=next_due
        )

        self.wps_records[wps_id] = record

        return {
            "id": wps_id,
            "record_type": record_type,
            "date": activity_date.isoformat(),
            "participants_count": len(participants),
            "participants": participants,
            "next_due": next_due.isoformat() if next_due else None,
            "message": f"WPS {record_type} recorded for {len(participants)} participants"
        }

    def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get compliance status dashboard"""
        # License status
        license_alerts = []
        for lic in self.licenses.values():
            days_until = (lic.expiration_date - date.today()).days
            if days_until <= 90:
                license_alerts.append({
                    "license": lic.license_number,
                    "type": lic.license_type.value,
                    "holder": lic.holder_name,
                    "expires": lic.expiration_date.isoformat(),
                    "days_until": days_until,
                    "status": "expired" if days_until < 0 else "critical" if days_until < 30 else "warning"
                })

        # WPS status
        wps_due = []
        for wps in self.wps_records.values():
            if wps.next_due:
                days_until = (wps.next_due - date.today()).days
                if days_until <= 60:
                    wps_due.append({
                        "type": wps.record_type,
                        "next_due": wps.next_due.isoformat(),
                        "days_until": days_until
                    })

        # RUP records count
        current_year = date.today().year
        rup_this_year = sum(1 for r in self.rup_records.values()
                          if r.application_date.year == current_year)

        return {
            "licenses": {
                "total": len(self.licenses),
                "active": sum(1 for lic in self.licenses.values() if lic.status == "active"),
                "expiring_soon": len([a for a in license_alerts if a["status"] == "warning"]),
                "expired": sum(1 for lic in self.licenses.values() if lic.status == "expired"),
                "alerts": sorted(license_alerts, key=lambda x: x["days_until"])
            },
            "wps": {
                "total_records": len(self.wps_records),
                "upcoming_due": wps_due
            },
            "rup_records": {
                "total": len(self.rup_records),
                "this_year": rup_this_year,
                "retention_compliant": True  # Would check 2-year retention
            },
            "overall_status": "compliant" if not license_alerts or all(a["status"] == "warning" for a in license_alerts) else "action_needed"
        }

    # -------------------------------------------------------------------------
    # ENTERPRISE BUDGETS & SCENARIOS
    # -------------------------------------------------------------------------

    def get_crop_budget_defaults(self, crop: str) -> Dict[str, Any]:
        """Get default budget values for a crop"""
        try:
            crop_type = CropType(crop)
        except ValueError:
            return {"error": f"Unknown crop: {crop}"}

        defaults = CROP_BUDGET_DEFAULTS[crop_type]
        return {
            "crop": crop,
            "defaults": defaults
        }

    def create_enterprise_budget(
        self,
        crop: str,
        year: int,
        acres: float,
        expected_yield: float = None,
        expected_price: float = None,
        **cost_overrides
    ) -> Dict[str, Any]:
        """Create an enterprise budget for a crop"""
        try:
            crop_type = CropType(crop)
        except ValueError:
            return {"error": f"Unknown crop: {crop}"}

        defaults = CROP_BUDGET_DEFAULTS[crop_type]
        budget_id = self._next_id("budget")

        # Use defaults or provided values
        exp_yield = expected_yield if expected_yield else defaults["expected_yield"]
        exp_price = expected_price if expected_price else defaults["expected_price"]

        # Variable costs (per acre)
        seed = cost_overrides.get("seed", defaults["seed"])
        fertilizer = cost_overrides.get("fertilizer", defaults["fertilizer"])
        chemicals = cost_overrides.get("chemicals", defaults["chemicals"])
        crop_ins_prem = cost_overrides.get("crop_insurance_premium", defaults["crop_insurance_premium"])
        custom_hire = cost_overrides.get("custom_hire", defaults["custom_hire"])
        fuel_lube = cost_overrides.get("fuel_lube", defaults["fuel_lube"])
        repairs = cost_overrides.get("repairs", defaults["repairs"])
        drying = cost_overrides.get("drying", defaults["drying"])
        hauling = cost_overrides.get("hauling", defaults["hauling"])
        other_var = cost_overrides.get("other_variable", defaults["other_variable"])

        total_variable = (seed + fertilizer + chemicals + crop_ins_prem +
                         custom_hire + fuel_lube + repairs + drying + hauling + other_var)

        # Fixed costs (per acre)
        land_rent = cost_overrides.get("land_rent", defaults["land_rent"])
        equip_dep = cost_overrides.get("equipment_depreciation", defaults["equipment_depreciation"])
        equip_int = cost_overrides.get("equipment_interest", defaults["equipment_interest"])
        labor = cost_overrides.get("labor", defaults["labor"])
        overhead = cost_overrides.get("overhead", defaults["overhead"])

        total_fixed = land_rent + equip_dep + equip_int + labor + overhead

        # Revenue (per acre)
        gross_revenue = exp_yield * exp_price
        crop_insurance = cost_overrides.get("crop_insurance_indemnity", 0)
        other_revenue = cost_overrides.get("other_revenue", 0)
        total_revenue = gross_revenue + crop_insurance + other_revenue

        # Returns
        total_costs = total_variable + total_fixed
        net_return = total_revenue - total_costs
        return_per_acre = net_return

        # Break-even calculations
        break_even_yield = total_costs / exp_price if exp_price > 0 else 0
        break_even_price = total_costs / exp_yield if exp_yield > 0 else 0

        budget = EnterpriseBudget(
            id=budget_id,
            crop=crop_type,
            year=year,
            acres=acres,
            expected_yield=exp_yield,
            expected_price=exp_price,
            gross_revenue=gross_revenue,
            crop_insurance=crop_insurance,
            other_revenue=other_revenue,
            total_revenue=total_revenue,
            seed=seed,
            fertilizer=fertilizer,
            chemicals=chemicals,
            crop_insurance_premium=crop_ins_prem,
            custom_hire=custom_hire,
            fuel_lube=fuel_lube,
            repairs=repairs,
            drying=drying,
            hauling=hauling,
            other_variable=other_var,
            total_variable=total_variable,
            land_rent=land_rent,
            equipment_depreciation=equip_dep,
            equipment_interest=equip_int,
            labor=labor,
            overhead=overhead,
            total_fixed=total_fixed,
            total_costs=total_costs,
            net_return=net_return,
            return_per_acre=return_per_acre,
            break_even_yield=break_even_yield,
            break_even_price=break_even_price
        )

        self.budgets[budget_id] = budget

        return {
            "id": budget_id,
            "crop": crop,
            "year": year,
            "acres": acres,
            "summary": {
                "expected_yield": exp_yield,
                "expected_price": exp_price,
                "gross_revenue_per_acre": round(gross_revenue, 2),
                "total_costs_per_acre": round(total_costs, 2),
                "net_return_per_acre": round(net_return, 2),
                "total_farm_net": round(net_return * acres, 2)
            },
            "break_even": {
                "yield": round(break_even_yield, 1),
                "price": round(break_even_price, 2)
            },
            "profitability": "profitable" if net_return > 0 else "break_even" if net_return == 0 else "loss"
        }

    def run_scenario_analysis(
        self,
        budget_id: str,
        yield_scenarios: List[float] = None,
        price_scenarios: List[float] = None
    ) -> Dict[str, Any]:
        """Run what-if scenario analysis on a budget"""
        if budget_id not in self.budgets:
            return {"error": f"Budget {budget_id} not found"}

        budget = self.budgets[budget_id]

        if yield_scenarios is None:
            # Default: -20%, -10%, base, +10%, +20%
            yield_scenarios = [
                budget.expected_yield * 0.8,
                budget.expected_yield * 0.9,
                budget.expected_yield,
                budget.expected_yield * 1.1,
                budget.expected_yield * 1.2
            ]

        if price_scenarios is None:
            # Default: -20%, -10%, base, +10%, +20%
            price_scenarios = [
                budget.expected_price * 0.8,
                budget.expected_price * 0.9,
                budget.expected_price,
                budget.expected_price * 1.1,
                budget.expected_price * 1.2
            ]

        # Build scenario matrix
        scenarios = []
        for yield_val in yield_scenarios:
            for price_val in price_scenarios:
                revenue = yield_val * price_val
                net_return = revenue - budget.total_costs
                scenarios.append({
                    "yield": round(yield_val, 1),
                    "price": round(price_val, 2),
                    "revenue": round(revenue, 2),
                    "net_return": round(net_return, 2),
                    "total_farm": round(net_return * budget.acres, 2),
                    "profitable": net_return > 0
                })

        # Find best/worst cases
        sorted_scenarios = sorted(scenarios, key=lambda x: x["net_return"])

        return {
            "budget_id": budget_id,
            "crop": budget.crop.value,
            "acres": budget.acres,
            "base_case": {
                "yield": budget.expected_yield,
                "price": budget.expected_price,
                "net_return": round(budget.net_return, 2)
            },
            "scenarios": scenarios,
            "worst_case": sorted_scenarios[0],
            "best_case": sorted_scenarios[-1],
            "profitable_scenarios": sum(1 for s in scenarios if s["profitable"]),
            "total_scenarios": len(scenarios)
        }

    def get_farm_budget_summary(self, year: int = None) -> Dict[str, Any]:
        """Get summary of all enterprise budgets"""
        if year is None:
            year = date.today().year

        year_budgets = [b for b in self.budgets.values() if b.year == year]

        if not year_budgets:
            return {
                "year": year,
                "message": "No budgets for this year",
                "total_acres": 0,
                "total_revenue": 0,
                "total_costs": 0,
                "total_net": 0
            }

        total_acres = sum(b.acres for b in year_budgets)
        total_revenue = sum(b.total_revenue * b.acres for b in year_budgets)
        total_costs = sum(b.total_costs * b.acres for b in year_budgets)
        total_net = total_revenue - total_costs

        by_crop = []
        for b in year_budgets:
            by_crop.append({
                "crop": b.crop.value,
                "acres": b.acres,
                "pct_of_farm": round(b.acres / total_acres * 100, 1),
                "revenue": round(b.total_revenue * b.acres, 2),
                "costs": round(b.total_costs * b.acres, 2),
                "net": round(b.net_return * b.acres, 2),
                "return_per_acre": round(b.return_per_acre, 2)
            })

        return {
            "year": year,
            "total_acres": total_acres,
            "total_revenue": round(total_revenue, 2),
            "total_costs": round(total_costs, 2),
            "total_net": round(total_net, 2),
            "average_return_per_acre": round(total_net / total_acres, 2) if total_acres > 0 else 0,
            "by_crop": by_crop,
            "crops_count": len(year_budgets)
        }

    # -------------------------------------------------------------------------
    # OUTREACH & IMPACT TRACKER
    # -------------------------------------------------------------------------

    def record_outreach_activity(
        self,
        activity_type: str,
        title: str,
        activity_date: date,
        description: str,
        audience: str,
        attendance: int,
        location: str,
        partners: List[str] = None,
        topics: List[str] = None,
        materials_path: str = None,
        follow_up_contacts: int = 0,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Record an outreach activity"""
        try:
            out_type = OutreachType(activity_type)
        except ValueError:
            return {"error": f"Invalid activity type: {activity_type}"}

        out_id = self._next_id("outreach")

        activity = OutreachActivity(
            id=out_id,
            activity_type=out_type,
            title=title,
            date=activity_date,
            description=description,
            audience=audience,
            attendance=attendance,
            location=location,
            partners=partners or [],
            topics=topics or [],
            materials_path=materials_path,
            follow_up_contacts=follow_up_contacts,
            notes=notes
        )

        self.outreach[out_id] = activity

        return {
            "id": out_id,
            "activity_type": activity_type,
            "title": title,
            "date": activity_date.isoformat(),
            "attendance": attendance,
            "location": location,
            "message": f"Outreach activity recorded: {title} ({attendance} attendees)"
        }

    def record_publication(
        self,
        pub_type: str,
        title: str,
        authors: List[str],
        publication_venue: str,
        pub_date: date,
        doi_or_url: str = None,
        abstract: str = "",
        keywords: List[str] = None,
        grant_acknowledgment: str = None
    ) -> Dict[str, Any]:
        """Record a publication"""
        pub_id = self._next_id("pub")

        publication = Publication(
            id=pub_id,
            pub_type=pub_type,
            title=title,
            authors=authors,
            publication_venue=publication_venue,
            date=pub_date,
            doi_or_url=doi_or_url,
            abstract=abstract,
            keywords=keywords or [],
            grant_acknowledgment=grant_acknowledgment
        )

        self.publications[pub_id] = publication

        return {
            "id": pub_id,
            "pub_type": pub_type,
            "title": title,
            "authors": authors,
            "venue": publication_venue,
            "date": pub_date.isoformat(),
            "message": f"Publication recorded: {title}"
        }

    def get_outreach_summary(
        self,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """Get summary of outreach activities"""
        if start_date is None:
            start_date = date(date.today().year, 1, 1)
        if end_date is None:
            end_date = date.today()

        filtered = [
            o for o in self.outreach.values()
            if start_date <= o.date <= end_date
        ]

        # By type
        by_type = {}
        total_attendance = 0
        for o in filtered:
            t = o.activity_type.value
            if t not in by_type:
                by_type[t] = {"count": 0, "attendance": 0}
            by_type[t]["count"] += 1
            by_type[t]["attendance"] += o.attendance
            total_attendance += o.attendance

        # Publications in period
        pubs = [
            p for p in self.publications.values()
            if start_date <= p.date <= end_date
        ]

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "activities": {
                "total": len(filtered),
                "by_type": by_type,
                "total_attendance": total_attendance,
                "average_attendance": round(total_attendance / len(filtered), 1) if filtered else 0
            },
            "publications": {
                "total": len(pubs),
                "by_type": {}
            },
            "recent_activities": [
                {
                    "title": o.title,
                    "type": o.activity_type.value,
                    "date": o.date.isoformat(),
                    "attendance": o.attendance
                }
                for o in sorted(filtered, key=lambda x: x.date, reverse=True)[:5]
            ]
        }

    def generate_outreach_report(
        self,
        grant_program: str,
        project_title: str,
        reporting_period: Tuple[date, date]
    ) -> Dict[str, Any]:
        """Generate outreach report for grant reporting"""
        start_date, end_date = reporting_period

        activities = [
            o for o in self.outreach.values()
            if start_date <= o.date <= end_date
        ]

        pubs = [
            p for p in self.publications.values()
            if start_date <= p.date <= end_date
        ]

        # Calculate reach
        total_direct = sum(o.attendance for o in activities)
        total_follow_up = sum(o.follow_up_contacts for o in activities)

        # By activity type
        activity_details = []
        for o in activities:
            activity_details.append({
                "date": o.date.isoformat(),
                "type": o.activity_type.value,
                "title": o.title,
                "audience": o.audience,
                "attendance": o.attendance,
                "location": o.location,
                "partners": o.partners,
                "topics": o.topics
            })

        pub_details = []
        for p in pubs:
            pub_details.append({
                "date": p.date.isoformat(),
                "type": p.pub_type,
                "title": p.title,
                "authors": p.authors,
                "venue": p.publication_venue,
                "url": p.doi_or_url
            })

        return {
            "report_type": "Outreach & Impact Report",
            "grant_program": grant_program,
            "project_title": project_title,
            "reporting_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_activities": len(activities),
                "total_publications": len(pubs),
                "direct_reach": total_direct,
                "follow_up_contacts": total_follow_up,
                "estimated_indirect_reach": total_direct * 5  # Multiplier estimate
            },
            "activities": activity_details,
            "publications": pub_details,
            "narrative": self._generate_outreach_narrative(activities, pubs, total_direct)
        }

    def _generate_outreach_narrative(
        self,
        activities: List[OutreachActivity],
        publications: List[Publication],
        total_reach: int
    ) -> str:
        """Generate narrative text for outreach report"""
        if not activities and not publications:
            return "No outreach activities recorded for this period."

        activity_types = set(o.activity_type.value for o in activities)

        narrative = f"""Outreach Summary

During this reporting period, the project conducted {len(activities)} outreach activities
reaching approximately {total_reach} individuals directly. Activities included
{', '.join(activity_types)}.

"""
        if publications:
            narrative += f"""Additionally, {len(publications)} publication(s) were produced to disseminate
project findings to broader audiences.

"""

        if activities:
            field_days = [o for o in activities if o.activity_type == OutreachType.FIELD_DAY]
            if field_days:
                narrative += f"""Field days were particularly impactful, with {len(field_days)} events
attracting {sum(o.attendance for o in field_days)} participants total.

"""

        narrative += """These outreach efforts support the project's goal of sharing sustainable
agriculture practices and research findings with the farming community."""

        return narrative


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_grant_operations_service: Optional[GrantOperationsService] = None


def get_grant_operations_service() -> GrantOperationsService:
    """Get or create the grant operations service singleton"""
    global _grant_operations_service
    if _grant_operations_service is None:
        _grant_operations_service = GrantOperationsService()
    return _grant_operations_service
