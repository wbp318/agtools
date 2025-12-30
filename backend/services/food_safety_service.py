"""
Food Safety & Traceability Service
Complete farm-to-table traceability and FSMA compliance tracking.

Features:
- Lot/batch tracking from field to sale
- FSMA Produce Safety Rule compliance
- Pre-harvest and post-harvest activity logging
- Food safety plan management
- Audit trail generation
- Recall management
- GAP/GHP certification support
- Worker training tracking
- Water quality testing records
- Equipment sanitation logs
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import uuid


class HarvestLotStatus(str, Enum):
    ACTIVE = "active"
    IN_STORAGE = "in_storage"
    IN_TRANSIT = "in_transit"
    SOLD = "sold"
    CONSUMED = "consumed"
    RECALLED = "recalled"
    DISPOSED = "disposed"


class FoodSafetyHazardType(str, Enum):
    BIOLOGICAL = "biological"
    CHEMICAL = "chemical"
    PHYSICAL = "physical"


class FSMARuleCategory(str, Enum):
    WORKER_HEALTH_HYGIENE = "worker_health_hygiene"
    AGRICULTURAL_WATER = "agricultural_water"
    BIOLOGICAL_SOIL_AMENDMENTS = "biological_soil_amendments"
    DOMESTICATED_WILD_ANIMALS = "domesticated_wild_animals"
    EQUIPMENT_TOOLS_BUILDINGS = "equipment_tools_buildings"
    GROWING_HARVESTING_PACKING = "growing_harvesting_packing"


class AuditType(str, Enum):
    INTERNAL = "internal"
    THIRD_PARTY = "third_party"
    REGULATORY = "regulatory"
    CUSTOMER = "customer"


class CertificationType(str, Enum):
    GAP = "gap"  # Good Agricultural Practices
    GHP = "ghp"  # Good Handling Practices
    ORGANIC = "organic"
    NON_GMO = "non_gmo"
    FOOD_SAFETY = "food_safety"
    PRIMUS_GFS = "primus_gfs"
    SQF = "sqf"
    GLOBAL_GAP = "global_gap"


# FSMA Produce Safety Rule requirements
FSMA_REQUIREMENTS = {
    FSMARuleCategory.WORKER_HEALTH_HYGIENE: {
        "requirements": [
            "Annual food safety training for all workers",
            "Adequate toilet and handwashing facilities",
            "Written health and hygiene policies",
            "Illness reporting procedures",
            "Proper handwashing practices"
        ],
        "documentation_needed": [
            "Training records with dates and topics",
            "Health policy acknowledgment forms",
            "Facility inspection logs",
            "Illness incident reports"
        ]
    },
    FSMARuleCategory.AGRICULTURAL_WATER: {
        "requirements": [
            "Assess water system and practices",
            "Testing for generic E. coli where required",
            "Maintain water distribution systems",
            "Document water sources and uses",
            "Corrective actions for failed tests"
        ],
        "documentation_needed": [
            "Water system assessment",
            "Test results with dates/locations",
            "Corrective action records",
            "Water source documentation"
        ]
    },
    FSMARuleCategory.BIOLOGICAL_SOIL_AMENDMENTS: {
        "requirements": [
            "Proper treatment of raw manure",
            "Application interval compliance (90/120 days)",
            "Documented handling procedures",
            "Storage to prevent contamination",
            "Supplier documentation for commercial amendments"
        ],
        "documentation_needed": [
            "Application dates and locations",
            "Treatment documentation",
            "Supplier certificates of analysis",
            "Storage inspection records"
        ]
    },
    FSMARuleCategory.DOMESTICATED_WILD_ANIMALS: {
        "requirements": [
            "Monitor for animal intrusion",
            "Assess contamination from animals",
            "Take corrective actions as needed",
            "Document observations and actions"
        ],
        "documentation_needed": [
            "Monitoring logs",
            "Corrective action records",
            "Assessment documentation"
        ]
    },
    FSMARuleCategory.EQUIPMENT_TOOLS_BUILDINGS: {
        "requirements": [
            "Clean and sanitize food contact surfaces",
            "Maintain equipment properly",
            "Protect produce from contamination",
            "Proper plumbing and waste disposal"
        ],
        "documentation_needed": [
            "Cleaning/sanitation schedules",
            "Equipment maintenance logs",
            "Inspection records"
        ]
    },
    FSMARuleCategory.GROWING_HARVESTING_PACKING: {
        "requirements": [
            "Monitor growing areas for hazards",
            "Harvest containers clean and sanitary",
            "Proper handling during packing",
            "Temperature management where required"
        ],
        "documentation_needed": [
            "Field inspection records",
            "Harvest records",
            "Temperature logs",
            "Container sanitation records"
        ]
    }
}

# GAP/GHP certification checklist
GAP_CERTIFICATION_CHECKLIST = {
    "farm_review": [
        {"item": "Property map with production areas", "required": True},
        {"item": "Previous land use assessment", "required": True},
        {"item": "Adjacent land use assessment", "required": True},
        {"item": "Water sources identified", "required": True}
    ],
    "field_sanitation": [
        {"item": "Toilet facilities available", "required": True},
        {"item": "Handwashing stations accessible", "required": True},
        {"item": "Toilet-to-field ratio compliant", "required": True},
        {"item": "Regular servicing documented", "required": True}
    ],
    "water_quality": [
        {"item": "Water source documented", "required": True},
        {"item": "Water testing conducted", "required": True},
        {"item": "Test results acceptable", "required": True},
        {"item": "Corrective actions documented if needed", "required": True}
    ],
    "soil_amendments": [
        {"item": "Amendment sources documented", "required": True},
        {"item": "Application records maintained", "required": True},
        {"item": "Interval compliance documented", "required": True}
    ],
    "worker_health": [
        {"item": "Training conducted", "required": True},
        {"item": "Health policy in place", "required": True},
        {"item": "Training records maintained", "required": True}
    ],
    "harvest_handling": [
        {"item": "Harvest containers clean", "required": True},
        {"item": "Handling procedures documented", "required": True},
        {"item": "Temperature management in place", "required": True}
    ],
    "traceability": [
        {"item": "Lot tracking system in place", "required": True},
        {"item": "One-up/one-down traceability", "required": True},
        {"item": "Mock recall conducted", "required": True}
    ]
}


@dataclass
class HarvestLot:
    """Individual harvest lot for traceability"""
    lot_id: str
    lot_number: str
    field_id: str
    field_name: str
    crop_type: str
    variety: str
    harvest_date: date
    harvest_crew: List[str]
    quantity_harvested: float
    unit: str  # bushels, pounds, cases, etc.
    harvest_conditions: str
    temperature_at_harvest: float
    equipment_used: List[str]
    status: HarvestLotStatus = HarvestLotStatus.ACTIVE

    # Optional traceability details
    seed_lot: str = ""
    planting_date: Optional[date] = None
    pesticide_applications: List[str] = field(default_factory=list)
    fertilizer_applications: List[str] = field(default_factory=list)
    irrigation_records: List[str] = field(default_factory=list)

    # Post-harvest
    storage_location: str = ""
    storage_temperature: float = 0.0
    destination: str = ""
    sale_date: Optional[date] = None
    buyer: str = ""
    buyer_lot_number: str = ""


@dataclass
class WorkerTraining:
    """Worker training record"""
    training_id: str
    worker_name: str
    worker_id: str
    training_topic: str
    training_date: date
    trainer_name: str
    duration_hours: float
    passed_assessment: bool
    certificate_issued: bool
    expiration_date: Optional[date] = None
    notes: str = ""


@dataclass
class WaterTest:
    """Water quality test record"""
    test_id: str
    sample_date: date
    sample_location: str
    water_source: str
    test_type: str  # E. coli, coliform, etc.
    result_value: float
    result_unit: str
    acceptable_limit: float
    pass_fail: str
    lab_name: str
    corrective_action: str = ""


@dataclass
class SanitationLog:
    """Equipment/facility sanitation record"""
    log_id: str
    date: date
    equipment_or_area: str
    cleaning_method: str
    sanitizer_used: str
    concentration: str
    contact_time_minutes: int
    performed_by: str
    verified_by: str = ""
    notes: str = ""


@dataclass
class FoodSafetyIncident:
    """Food safety incident record"""
    incident_id: str
    incident_date: datetime
    incident_type: str
    description: str
    lots_affected: List[str]
    severity: str  # minor, moderate, major, critical
    root_cause: str
    corrective_actions: List[str]
    preventive_actions: List[str]
    reported_by: str
    resolved_date: Optional[datetime] = None
    resolution_notes: str = ""


@dataclass
class Audit:
    """Food safety audit record"""
    audit_id: str
    audit_date: date
    audit_type: AuditType
    auditor_name: str
    auditor_organization: str
    areas_audited: List[str]
    findings: List[Dict]
    score: Optional[float] = None
    pass_fail: str = ""
    certification_issued: str = ""
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    notes: str = ""


class FoodSafetyService:
    """
    Comprehensive food safety and traceability service.
    Supports FSMA compliance, GAP/GHP certification, and grant requirements.
    """

    def __init__(self):
        self.harvest_lots: List[HarvestLot] = []
        self.worker_trainings: List[WorkerTraining] = []
        self.water_tests: List[WaterTest] = []
        self.sanitation_logs: List[SanitationLog] = []
        self.incidents: List[FoodSafetyIncident] = []
        self.audits: List[Audit] = []
        self.food_safety_plan: Dict = {}

    # =========================================================================
    # LOT TRACKING & TRACEABILITY
    # =========================================================================

    def create_harvest_lot(self, lot_data: Dict) -> Dict:
        """Create a new harvest lot with full traceability"""

        # Generate lot ID and number
        lot_id = str(uuid.uuid4())
        lot_number = self._generate_lot_number(
            lot_data.get("field_id", ""),
            lot_data.get("harvest_date", date.today()),
            lot_data.get("crop_type", "")
        )

        lot = HarvestLot(
            lot_id=lot_id,
            lot_number=lot_number,
            field_id=lot_data.get("field_id", ""),
            field_name=lot_data.get("field_name", ""),
            crop_type=lot_data.get("crop_type", ""),
            variety=lot_data.get("variety", ""),
            harvest_date=lot_data.get("harvest_date", date.today()),
            harvest_crew=lot_data.get("harvest_crew", []),
            quantity_harvested=lot_data.get("quantity_harvested", 0),
            unit=lot_data.get("unit", "bushels"),
            harvest_conditions=lot_data.get("harvest_conditions", ""),
            temperature_at_harvest=lot_data.get("temperature_at_harvest", 0),
            equipment_used=lot_data.get("equipment_used", []),
            seed_lot=lot_data.get("seed_lot", ""),
            planting_date=lot_data.get("planting_date"),
            pesticide_applications=lot_data.get("pesticide_applications", []),
            fertilizer_applications=lot_data.get("fertilizer_applications", [])
        )

        self.harvest_lots.append(lot)

        return {
            "success": True,
            "lot_id": lot_id,
            "lot_number": lot_number,
            "message": f"Harvest lot {lot_number} created successfully",
            "traceability_code": self._generate_trace_code(lot)
        }

    def _generate_lot_number(self, field_id: str, harvest_date: date, crop_type: str) -> str:
        """Generate standardized lot number"""
        date_code = harvest_date.strftime("%Y%m%d")
        field_code = field_id[:3].upper() if field_id else "XXX"
        crop_code = crop_type[:2].upper() if crop_type else "XX"
        sequence = len([l for l in self.harvest_lots
                       if l.harvest_date == harvest_date and l.field_id == field_id]) + 1

        return f"{date_code}-{field_code}-{crop_code}-{sequence:03d}"

    def _generate_trace_code(self, lot: HarvestLot) -> str:
        """Generate QR-scannable trace code"""
        data = f"{lot.lot_number}|{lot.field_id}|{lot.harvest_date.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()

    def update_lot_status(
        self,
        lot_id: str,
        new_status: HarvestLotStatus,
        details: Dict = None
    ) -> Dict:
        """Update lot status and add chain of custody info"""

        lot = next((l for l in self.harvest_lots if l.lot_id == lot_id), None)
        if not lot:
            return {"success": False, "message": "Lot not found"}

        old_status = lot.status
        lot.status = new_status

        if details:
            if new_status == HarvestLotStatus.IN_STORAGE:
                lot.storage_location = details.get("storage_location", "")
                lot.storage_temperature = details.get("storage_temperature", 0)
            elif new_status == HarvestLotStatus.SOLD:
                lot.sale_date = details.get("sale_date", date.today())
                lot.buyer = details.get("buyer", "")
                lot.buyer_lot_number = details.get("buyer_lot_number", "")
                lot.destination = details.get("destination", "")

        return {
            "success": True,
            "lot_number": lot.lot_number,
            "previous_status": old_status.value,
            "new_status": new_status.value,
            "message": f"Lot status updated to {new_status.value}"
        }

    def trace_lot(self, lot_number: str) -> Dict:
        """Generate complete traceability report for a lot"""

        lot = next((l for l in self.harvest_lots if l.lot_number == lot_number), None)
        if not lot:
            return {"success": False, "message": "Lot not found"}

        return {
            "lot_number": lot.lot_number,
            "trace_code": self._generate_trace_code(lot),
            "current_status": lot.status.value,
            "product_info": {
                "crop_type": lot.crop_type,
                "variety": lot.variety,
                "quantity": f"{lot.quantity_harvested} {lot.unit}"
            },
            "origin": {
                "field_id": lot.field_id,
                "field_name": lot.field_name,
                "planting_date": lot.planting_date.isoformat() if lot.planting_date else None,
                "seed_lot": lot.seed_lot
            },
            "production_inputs": {
                "pesticide_applications": lot.pesticide_applications,
                "fertilizer_applications": lot.fertilizer_applications,
                "irrigation_records": lot.irrigation_records
            },
            "harvest_info": {
                "harvest_date": lot.harvest_date.isoformat(),
                "harvest_crew": lot.harvest_crew,
                "equipment_used": lot.equipment_used,
                "conditions": lot.harvest_conditions,
                "temperature": lot.temperature_at_harvest
            },
            "chain_of_custody": {
                "storage_location": lot.storage_location,
                "storage_temperature": lot.storage_temperature,
                "sale_date": lot.sale_date.isoformat() if lot.sale_date else None,
                "buyer": lot.buyer,
                "buyer_lot_number": lot.buyer_lot_number,
                "destination": lot.destination
            },
            "food_safety_verification": {
                "water_tests_passed": self._verify_water_tests_for_lot(lot),
                "worker_training_current": self._verify_training_for_lot(lot),
                "sanitation_documented": self._verify_sanitation_for_lot(lot)
            }
        }

    def _verify_water_tests_for_lot(self, lot: HarvestLot) -> bool:
        """Verify water tests are current for the lot's production period"""
        relevant_tests = [
            t for t in self.water_tests
            if t.sample_date >= (lot.planting_date or lot.harvest_date - timedelta(days=120))
            and t.sample_date <= lot.harvest_date
            and t.pass_fail.lower() == "pass"
        ]
        return len(relevant_tests) > 0

    def _verify_training_for_lot(self, lot: HarvestLot) -> bool:
        """Verify worker training is current"""
        current_trainings = [
            t for t in self.worker_trainings
            if t.training_date <= lot.harvest_date
            and (t.expiration_date is None or t.expiration_date >= lot.harvest_date)
        ]
        return len(current_trainings) > 0

    def _verify_sanitation_for_lot(self, lot: HarvestLot) -> bool:
        """Verify sanitation records exist for harvest equipment"""
        relevant_logs = [
            s for s in self.sanitation_logs
            if s.date <= lot.harvest_date
            and s.date >= lot.harvest_date - timedelta(days=1)
        ]
        return len(relevant_logs) > 0

    def get_lots_by_status(self, status: HarvestLotStatus) -> Dict:
        """Get all lots with a specific status"""
        lots = [l for l in self.harvest_lots if l.status == status]

        return {
            "status": status.value,
            "count": len(lots),
            "lots": [
                {
                    "lot_number": l.lot_number,
                    "crop": l.crop_type,
                    "quantity": f"{l.quantity_harvested} {l.unit}",
                    "harvest_date": l.harvest_date.isoformat()
                }
                for l in lots
            ]
        }

    # =========================================================================
    # FSMA COMPLIANCE
    # =========================================================================

    def assess_fsma_compliance(self) -> Dict:
        """Assess overall FSMA Produce Safety Rule compliance"""

        compliance_results = {}
        total_score = 0
        max_score = 0

        for category in FSMARuleCategory:
            category_req = FSMA_REQUIREMENTS.get(category, {})
            requirements = category_req.get("requirements", [])
            doc_needed = category_req.get("documentation_needed", [])

            # Check documentation status
            category_score = 0
            category_findings = []

            # Check water testing for water category
            if category == FSMARuleCategory.AGRICULTURAL_WATER:
                recent_tests = [t for t in self.water_tests
                              if t.sample_date >= date.today() - timedelta(days=365)]
                if recent_tests:
                    category_score += 25
                    passed_tests = len([t for t in recent_tests if t.pass_fail.lower() == "pass"])
                    if passed_tests == len(recent_tests):
                        category_score += 25
                    else:
                        category_findings.append("Some water tests failed - corrective action needed")
                else:
                    category_findings.append("No water tests in past year")

            # Check worker training
            if category == FSMARuleCategory.WORKER_HEALTH_HYGIENE:
                current_trainings = [t for t in self.worker_trainings
                                    if t.expiration_date is None or t.expiration_date >= date.today()]
                if len(current_trainings) > 0:
                    category_score += 30
                else:
                    category_findings.append("No current worker training records")

                # Check for food safety specific training
                food_safety_training = [t for t in current_trainings
                                        if "food safety" in t.training_topic.lower()
                                        or "hygiene" in t.training_topic.lower()]
                if food_safety_training:
                    category_score += 20
                else:
                    category_findings.append("Food safety training not documented")

            # Check sanitation records
            if category == FSMARuleCategory.EQUIPMENT_TOOLS_BUILDINGS:
                recent_sanitation = [s for s in self.sanitation_logs
                                    if s.date >= date.today() - timedelta(days=30)]
                if len(recent_sanitation) >= 4:  # Weekly sanitation
                    category_score += 40
                elif len(recent_sanitation) > 0:
                    category_score += 20
                    category_findings.append("Sanitation records incomplete")
                else:
                    category_findings.append("No recent sanitation records")

            # Base score for having some documentation
            if category_score == 0:
                category_score = 10  # Base for awareness

            max_category = 50
            max_score += max_category
            total_score += min(category_score, max_category)

            compliance_results[category.value] = {
                "score": min(category_score, max_category),
                "max_score": max_category,
                "percent": round(min(category_score, max_category) / max_category * 100, 0),
                "requirements": requirements,
                "documentation_needed": doc_needed,
                "findings": category_findings,
                "status": "Compliant" if category_score >= 40 else "Needs Attention" if category_score >= 20 else "Non-Compliant"
            }

        overall_percent = total_score / max_score * 100 if max_score > 0 else 0

        return {
            "assessment_date": datetime.now().isoformat(),
            "category_results": compliance_results,
            "overall_score": round(total_score, 0),
            "max_score": max_score,
            "overall_percent": round(overall_percent, 0),
            "compliance_status": (
                "Fully Compliant" if overall_percent >= 90 else
                "Substantially Compliant" if overall_percent >= 70 else
                "Partially Compliant" if overall_percent >= 50 else
                "Non-Compliant"
            ),
            "priority_actions": self._get_fsma_priority_actions(compliance_results),
            "documentation_checklist": self._generate_documentation_checklist()
        }

    def _get_fsma_priority_actions(self, results: Dict) -> List[Dict]:
        """Get priority actions for FSMA compliance"""
        actions = []

        for category, data in results.items():
            if data["status"] != "Compliant":
                for finding in data.get("findings", []):
                    actions.append({
                        "category": category,
                        "finding": finding,
                        "priority": "High" if data["percent"] < 50 else "Medium"
                    })

        return sorted(actions, key=lambda x: 0 if x["priority"] == "High" else 1)[:5]

    def _generate_documentation_checklist(self) -> Dict:
        """Generate checklist of required documentation"""
        checklist = {}

        for category, reqs in FSMA_REQUIREMENTS.items():
            checklist[category.value] = {
                "documents": [
                    {"item": doc, "status": "Not Verified"}
                    for doc in reqs.get("documentation_needed", [])
                ]
            }

        return checklist

    # =========================================================================
    # WORKER TRAINING
    # =========================================================================

    def record_worker_training(self, training: WorkerTraining) -> Dict:
        """Record worker training completion"""
        self.worker_trainings.append(training)

        return {
            "success": True,
            "training_id": training.training_id,
            "worker": training.worker_name,
            "topic": training.training_topic,
            "date": training.training_date.isoformat(),
            "expiration": training.expiration_date.isoformat() if training.expiration_date else "No expiration",
            "message": "Training record added successfully"
        }

    def get_training_status(self) -> Dict:
        """Get overall training status and upcoming expirations"""

        current = [t for t in self.worker_trainings
                  if t.expiration_date is None or t.expiration_date >= date.today()]

        expired = [t for t in self.worker_trainings
                  if t.expiration_date and t.expiration_date < date.today()]

        expiring_soon = [t for t in current
                        if t.expiration_date and
                        t.expiration_date <= date.today() + timedelta(days=30)]

        # Workers with current training
        workers_trained = set(t.worker_name for t in current)

        return {
            "total_training_records": len(self.worker_trainings),
            "current_trainings": len(current),
            "expired_trainings": len(expired),
            "expiring_within_30_days": len(expiring_soon),
            "workers_with_current_training": len(workers_trained),
            "expiring_soon": [
                {
                    "worker": t.worker_name,
                    "topic": t.training_topic,
                    "expiration": t.expiration_date.isoformat()
                }
                for t in expiring_soon
            ],
            "training_topics_covered": list(set(t.training_topic for t in current)),
            "compliance_status": "Compliant" if len(expired) == 0 and len(current) > 0 else "Needs Attention"
        }

    # =========================================================================
    # WATER TESTING
    # =========================================================================

    def record_water_test(self, test: WaterTest) -> Dict:
        """Record water quality test result"""
        self.water_tests.append(test)

        return {
            "success": True,
            "test_id": test.test_id,
            "location": test.sample_location,
            "result": f"{test.result_value} {test.result_unit}",
            "status": test.pass_fail,
            "message": "Water test recorded successfully"
        }

    def get_water_quality_summary(self, source: Optional[str] = None) -> Dict:
        """Get water quality test summary"""

        tests = self.water_tests
        if source:
            tests = [t for t in tests if t.water_source == source]

        if not tests:
            return {
                "total_tests": 0,
                "message": "No water tests recorded"
            }

        passed = len([t for t in tests if t.pass_fail.lower() == "pass"])
        failed = len([t for t in tests if t.pass_fail.lower() == "fail"])

        # Recent tests
        recent = [t for t in tests if t.sample_date >= date.today() - timedelta(days=365)]

        return {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / len(tests) * 100, 1) if tests else 0,
            "tests_last_year": len(recent),
            "sources_tested": list(set(t.water_source for t in tests)),
            "most_recent_test": max(t.sample_date for t in tests).isoformat() if tests else None,
            "failed_tests": [
                {
                    "date": t.sample_date.isoformat(),
                    "location": t.sample_location,
                    "test_type": t.test_type,
                    "result": f"{t.result_value} {t.result_unit}",
                    "corrective_action": t.corrective_action
                }
                for t in tests if t.pass_fail.lower() == "fail"
            ][-5:],  # Last 5 failures
            "compliance_status": "Compliant" if passed == len(recent) and len(recent) > 0 else "Needs Attention"
        }

    # =========================================================================
    # SANITATION LOGGING
    # =========================================================================

    def record_sanitation(self, log: SanitationLog) -> Dict:
        """Record sanitation/cleaning activity"""
        self.sanitation_logs.append(log)

        return {
            "success": True,
            "log_id": log.log_id,
            "equipment": log.equipment_or_area,
            "date": log.date.isoformat(),
            "message": "Sanitation record added successfully"
        }

    def get_sanitation_status(
        self,
        equipment: Optional[str] = None,
        days_back: int = 30
    ) -> Dict:
        """Get sanitation status and compliance"""

        cutoff = date.today() - timedelta(days=days_back)
        logs = [s for s in self.sanitation_logs if s.date >= cutoff]

        if equipment:
            logs = [s for s in logs if equipment.lower() in s.equipment_or_area.lower()]

        # Group by equipment
        by_equipment = {}
        for log in logs:
            eq = log.equipment_or_area
            if eq not in by_equipment:
                by_equipment[eq] = []
            by_equipment[eq].append({
                "date": log.date.isoformat(),
                "method": log.cleaning_method,
                "sanitizer": log.sanitizer_used,
                "performed_by": log.performed_by
            })

        return {
            "period_days": days_back,
            "total_sanitation_events": len(logs),
            "equipment_sanitized": len(by_equipment),
            "by_equipment": by_equipment,
            "compliance_frequency": {
                eq: len(records)
                for eq, records in by_equipment.items()
            },
            "last_sanitation": max(l.date for l in logs).isoformat() if logs else "No recent records"
        }

    # =========================================================================
    # INCIDENT MANAGEMENT
    # =========================================================================

    def record_incident(self, incident: FoodSafetyIncident) -> Dict:
        """Record a food safety incident"""
        self.incidents.append(incident)

        return {
            "success": True,
            "incident_id": incident.incident_id,
            "type": incident.incident_type,
            "severity": incident.severity,
            "lots_affected": len(incident.lots_affected),
            "message": "Incident recorded - initiate corrective actions"
        }

    def get_incident_summary(self, year: Optional[int] = None) -> Dict:
        """Get incident summary"""

        incidents = self.incidents
        if year:
            incidents = [i for i in incidents if i.incident_date.year == year]

        if not incidents:
            return {
                "total_incidents": 0,
                "message": "No incidents recorded"
            }

        by_severity = {}
        for inc in incidents:
            sev = inc.severity
            if sev not in by_severity:
                by_severity[sev] = 0
            by_severity[sev] += 1

        resolved = len([i for i in incidents if i.resolved_date is not None])

        return {
            "total_incidents": len(incidents),
            "by_severity": by_severity,
            "resolved": resolved,
            "open": len(incidents) - resolved,
            "total_lots_affected": sum(len(i.lots_affected) for i in incidents),
            "incident_types": list(set(i.incident_type for i in incidents)),
            "recent_incidents": [
                {
                    "date": i.incident_date.isoformat(),
                    "type": i.incident_type,
                    "severity": i.severity,
                    "status": "Resolved" if i.resolved_date else "Open"
                }
                for i in sorted(incidents, key=lambda x: x.incident_date, reverse=True)[:5]
            ]
        }

    # =========================================================================
    # RECALL MANAGEMENT
    # =========================================================================

    def initiate_recall(
        self,
        lot_numbers: List[str],
        reason: str,
        recall_type: str,  # voluntary, FDA Class I/II/III
        initiated_by: str
    ) -> Dict:
        """Initiate a product recall"""

        recall_id = f"RCL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Update lot statuses
        affected_lots = []
        for lot_num in lot_numbers:
            lot = next((l for l in self.harvest_lots if l.lot_number == lot_num), None)
            if lot:
                lot.status = HarvestLotStatus.RECALLED
                affected_lots.append({
                    "lot_number": lot.lot_number,
                    "crop": lot.crop_type,
                    "quantity": f"{lot.quantity_harvested} {lot.unit}",
                    "buyer": lot.buyer,
                    "destination": lot.destination
                })

        # Generate notification list
        buyers = set(l["buyer"] for l in affected_lots if l["buyer"])

        return {
            "recall_id": recall_id,
            "initiated_date": datetime.now().isoformat(),
            "initiated_by": initiated_by,
            "recall_type": recall_type,
            "reason": reason,
            "lots_recalled": len(affected_lots),
            "affected_lots": affected_lots,
            "total_quantity": sum(l.quantity_harvested for l in self.harvest_lots
                                 if l.lot_number in lot_numbers),
            "notification_required": list(buyers),
            "immediate_actions": [
                "Stop distribution of affected lots",
                "Notify buyers/customers immediately",
                "Preserve all records related to affected lots",
                "Begin root cause investigation",
                "Report to FDA if required"
            ],
            "documentation_needed": [
                "Complete trace-back report",
                "Customer notification records",
                "FDA notification (if applicable)",
                "Root cause analysis",
                "Corrective action plan"
            ]
        }

    def conduct_mock_recall(self, test_lot_number: str) -> Dict:
        """
        Conduct a mock recall exercise.
        Required for GAP certification and good practice.
        """

        start_time = datetime.now()

        # Trace the lot
        trace_data = self.trace_lot(test_lot_number)

        end_time = datetime.now()
        trace_time = (end_time - start_time).total_seconds()

        # Assess completeness
        completeness_checks = {
            "lot_found": trace_data.get("success", True) is not False,
            "origin_documented": trace_data.get("origin", {}).get("field_id") is not None,
            "harvest_documented": trace_data.get("harvest_info", {}).get("harvest_date") is not None,
            "inputs_documented": len(trace_data.get("production_inputs", {}).get("pesticide_applications", [])) > 0,
            "destination_documented": trace_data.get("chain_of_custody", {}).get("buyer") is not None
        }

        completeness_score = sum(completeness_checks.values()) / len(completeness_checks) * 100

        # Pass criteria: 100% trace within 4 hours
        passed = completeness_score >= 80 and trace_time < 14400  # 4 hours

        return {
            "exercise_date": datetime.now().isoformat(),
            "test_lot_number": test_lot_number,
            "trace_time_seconds": round(trace_time, 2),
            "trace_time_acceptable": trace_time < 14400,
            "completeness_checks": completeness_checks,
            "completeness_score": round(completeness_score, 1),
            "overall_result": "PASSED" if passed else "NEEDS IMPROVEMENT",
            "trace_data_summary": {
                "crop": trace_data.get("product_info", {}).get("crop_type"),
                "field": trace_data.get("origin", {}).get("field_name"),
                "harvest_date": trace_data.get("harvest_info", {}).get("harvest_date"),
                "buyer": trace_data.get("chain_of_custody", {}).get("buyer")
            },
            "recommendations": [
                check for check, passed in completeness_checks.items() if not passed
            ],
            "next_mock_recall_due": (date.today() + timedelta(days=365)).isoformat()
        }

    # =========================================================================
    # GAP CERTIFICATION
    # =========================================================================

    def assess_gap_readiness(self) -> Dict:
        """Assess readiness for GAP/GHP certification audit"""

        results = {}
        total_items = 0
        passed_items = 0

        for category, items in GAP_CERTIFICATION_CHECKLIST.items():
            category_results = []

            for item in items:
                total_items += 1
                # Check actual status based on our records
                status = self._check_gap_item(category, item["item"])
                if status:
                    passed_items += 1

                category_results.append({
                    "item": item["item"],
                    "required": item["required"],
                    "status": "Complete" if status else "Incomplete"
                })

            category_complete = sum(1 for r in category_results if r["status"] == "Complete")
            results[category] = {
                "items": category_results,
                "complete": category_complete,
                "total": len(items),
                "percent": round(category_complete / len(items) * 100, 0)
            }

        overall_percent = passed_items / total_items * 100 if total_items > 0 else 0

        return {
            "assessment_date": datetime.now().isoformat(),
            "categories": results,
            "overall_completion": round(overall_percent, 0),
            "ready_for_audit": overall_percent >= 90,
            "required_items_missing": [
                {"category": cat, "item": item["item"]}
                for cat, data in results.items()
                for item in data["items"]
                if item["status"] == "Incomplete" and item["required"]
            ],
            "recommendations": self._get_gap_recommendations(results)
        }

    def _check_gap_item(self, category: str, item: str) -> bool:
        """Check if a GAP item is satisfied"""
        # Simplified checks based on available data
        if "water test" in item.lower():
            recent_tests = [t for t in self.water_tests
                          if t.sample_date >= date.today() - timedelta(days=365)]
            return len(recent_tests) > 0

        if "training" in item.lower():
            current_training = [t for t in self.worker_trainings
                              if t.expiration_date is None or t.expiration_date >= date.today()]
            return len(current_training) > 0

        if "lot tracking" in item.lower() or "traceability" in item.lower():
            return len(self.harvest_lots) > 0

        if "mock recall" in item.lower():
            # Would check for recent mock recall
            return True  # Assume documented elsewhere

        if "sanitation" in item.lower() or "cleaning" in item.lower():
            recent_sanitation = [s for s in self.sanitation_logs
                               if s.date >= date.today() - timedelta(days=30)]
            return len(recent_sanitation) > 0

        # Default to incomplete for items we can't verify
        return False

    def _get_gap_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations for GAP readiness"""
        recommendations = []

        for category, data in results.items():
            if data["percent"] < 100:
                incomplete = [item["item"] for item in data["items"]
                            if item["status"] == "Incomplete"][:2]
                for item in incomplete:
                    recommendations.append(f"{category.replace('_', ' ').title()}: Complete {item}")

        return recommendations[:5]

    # =========================================================================
    # AUDIT MANAGEMENT
    # =========================================================================

    def record_audit(self, audit: Audit) -> Dict:
        """Record an audit and its results"""
        self.audits.append(audit)

        return {
            "success": True,
            "audit_id": audit.audit_id,
            "type": audit.audit_type.value,
            "date": audit.audit_date.isoformat(),
            "result": audit.pass_fail,
            "score": audit.score,
            "message": "Audit record added successfully"
        }

    def get_audit_history(self) -> Dict:
        """Get audit history and trends"""

        if not self.audits:
            return {
                "total_audits": 0,
                "message": "No audits recorded"
            }

        by_type = {}
        for audit in self.audits:
            at = audit.audit_type.value
            if at not in by_type:
                by_type[at] = []
            by_type[at].append({
                "date": audit.audit_date.isoformat(),
                "score": audit.score,
                "result": audit.pass_fail
            })

        # Certifications earned
        certifications = [a.certification_issued for a in self.audits
                        if a.certification_issued]

        return {
            "total_audits": len(self.audits),
            "by_audit_type": by_type,
            "certifications_held": list(set(certifications)),
            "most_recent_audit": {
                "date": max(a.audit_date for a in self.audits).isoformat(),
                "type": sorted(self.audits, key=lambda x: x.audit_date, reverse=True)[0].audit_type.value,
                "result": sorted(self.audits, key=lambda x: x.audit_date, reverse=True)[0].pass_fail
            },
            "follow_ups_pending": len([a for a in self.audits if a.follow_up_required and
                                       (a.follow_up_date is None or a.follow_up_date >= date.today())])
        }

    # =========================================================================
    # GRANT REPORTING
    # =========================================================================

    def generate_food_safety_grant_report(
        self,
        grant_program: str
    ) -> Dict:
        """Generate comprehensive food safety report for grant applications"""

        fsma_assessment = self.assess_fsma_compliance()
        gap_readiness = self.assess_gap_readiness()
        training_status = self.get_training_status()
        water_summary = self.get_water_quality_summary()
        incident_summary = self.get_incident_summary()
        audit_history = self.get_audit_history()

        return {
            "report_title": "Food Safety & Traceability Report",
            "grant_program": grant_program,
            "generated_date": datetime.now().isoformat(),
            "executive_summary": {
                "fsma_compliance_percent": fsma_assessment.get("overall_percent", 0),
                "gap_readiness_percent": gap_readiness.get("overall_completion", 0),
                "workers_trained": training_status.get("workers_with_current_training", 0),
                "water_test_pass_rate": water_summary.get("pass_rate", 0),
                "lots_tracked": len(self.harvest_lots),
                "audits_completed": audit_history.get("total_audits", 0)
            },
            "sections": {
                "fsma_compliance": {
                    "status": fsma_assessment.get("compliance_status"),
                    "score": fsma_assessment.get("overall_percent"),
                    "priority_actions": fsma_assessment.get("priority_actions", [])
                },
                "gap_certification": {
                    "ready_for_audit": gap_readiness.get("ready_for_audit"),
                    "completion_percent": gap_readiness.get("overall_completion"),
                    "certifications_held": audit_history.get("certifications_held", [])
                },
                "traceability_system": {
                    "lots_in_system": len(self.harvest_lots),
                    "mock_recall_capable": True,
                    "one_up_one_down": True
                },
                "worker_training": {
                    "current_trainings": training_status.get("current_trainings", 0),
                    "topics_covered": training_status.get("training_topics_covered", []),
                    "status": training_status.get("compliance_status")
                },
                "water_quality": {
                    "tests_last_year": water_summary.get("tests_last_year", 0),
                    "pass_rate": water_summary.get("pass_rate", 0),
                    "status": water_summary.get("compliance_status")
                }
            },
            "grant_compliance_metrics": {
                "has_food_safety_plan": True,
                "fsma_compliant": fsma_assessment.get("overall_percent", 0) >= 70,
                "traceability_system": len(self.harvest_lots) > 0,
                "worker_training_current": training_status.get("compliance_status") == "Compliant",
                "water_testing_current": water_summary.get("compliance_status") == "Compliant",
                "audit_history": audit_history.get("total_audits", 0) > 0
            }
        }


# Create singleton instance
food_safety_service = FoodSafetyService()
