"""
Farm Business Service for AgTools
Version: 4.2.0

Complete farm business management featuring:
- Tax Planning Tools (depreciation schedules, Section 179, income timing)
- Succession Planning (farm transition, estate planning tools)
- Benchmarking Dashboard (year-over-year, field-by-field, regional comparisons)
- Document Vault (centralized document management)
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import math


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

# ----- Tax Planning -----

class AssetType(Enum):
    """Depreciable asset types"""
    MACHINERY = "machinery"
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    BUILDING = "building"
    LAND_IMPROVEMENT = "land_improvement"
    LIVESTOCK_BREEDING = "livestock_breeding"
    COMPUTER = "computer"
    OFFICE_EQUIPMENT = "office_equipment"


class DepreciationMethod(Enum):
    """Depreciation methods"""
    STRAIGHT_LINE = "straight_line"
    MACRS_GDS = "macrs_gds"
    MACRS_ADS = "macrs_ads"
    SECTION_179 = "section_179"
    BONUS = "bonus_depreciation"


class TaxEntity(Enum):
    """Tax entity types"""
    SCHEDULE_F = "schedule_f"
    PARTNERSHIP = "partnership"
    S_CORP = "s_corp"
    C_CORP = "c_corp"


@dataclass
class DepreciableAsset:
    """Depreciable asset record"""
    id: str
    name: str
    asset_type: AssetType
    purchase_date: date
    purchase_price: float
    salvage_value: float
    useful_life_years: int
    depreciation_method: DepreciationMethod
    section_179_amount: float
    bonus_depreciation_pct: float
    accumulated_depreciation: float
    current_book_value: float
    notes: str


@dataclass
class TaxProjection:
    """Tax projection"""
    id: str
    tax_year: int
    entity_type: TaxEntity
    gross_income: float
    total_expenses: float
    depreciation: float
    net_farm_income: float
    self_employment_tax: float
    estimated_income_tax: float
    total_tax_liability: float


# ----- Succession Planning -----

class TransferMethod(Enum):
    """Asset transfer methods"""
    SALE = "sale"
    GIFT = "gift"
    INHERITANCE = "inheritance"
    INSTALLMENT_SALE = "installment_sale"
    LEASE_PURCHASE = "lease_purchase"
    TRUST = "trust"
    LLC_TRANSFER = "llc_transfer"


class SuccessorRole(Enum):
    """Successor roles"""
    PRIMARY_OPERATOR = "primary_operator"
    SECONDARY_OPERATOR = "secondary_operator"
    INVESTOR = "investor"
    LANDLORD = "landlord"
    ADVISOR = "advisor"


@dataclass
class FamilyMember:
    """Family member in succession plan"""
    id: str
    name: str
    relationship: str
    age: int
    role: SuccessorRole
    ownership_pct: float
    involved_in_operations: bool
    skills: List[str]
    interests: List[str]
    notes: str


@dataclass
class SuccessionMilestone:
    """Succession plan milestone"""
    id: str
    title: str
    target_date: date
    description: str
    responsible_party: str
    status: str  # planned, in_progress, completed
    notes: str


@dataclass
class AssetTransferPlan:
    """Asset transfer plan"""
    id: str
    asset_description: str
    current_owner: str
    future_owner: str
    transfer_method: TransferMethod
    estimated_value: float
    planned_date: date
    tax_implications: Dict[str, float]
    legal_requirements: List[str]
    status: str


# ----- Benchmarking -----

class BenchmarkMetric(Enum):
    """Benchmark metrics"""
    YIELD_PER_ACRE = "yield_per_acre"
    COST_PER_ACRE = "cost_per_acre"
    REVENUE_PER_ACRE = "revenue_per_acre"
    NET_INCOME_PER_ACRE = "net_income_per_acre"
    COST_PER_BUSHEL = "cost_per_bushel"
    RETURN_ON_ASSETS = "return_on_assets"
    DEBT_TO_ASSET = "debt_to_asset"
    WORKING_CAPITAL = "working_capital"
    INPUT_COST_RATIO = "input_cost_ratio"


@dataclass
class BenchmarkRecord:
    """Benchmark data record"""
    id: str
    year: int
    metric: BenchmarkMetric
    crop: str
    field_id: str
    actual_value: float
    farm_average: float
    regional_average: float
    top_quartile: float
    percentile_rank: int


# ----- Document Vault -----

class DocumentCategory(Enum):
    """Document categories"""
    TAX_RETURNS = "tax_returns"
    INSURANCE = "insurance"
    LEASES = "leases"
    DEEDS = "deeds"
    EQUIPMENT = "equipment"
    CROP_RECORDS = "crop_records"
    FINANCIAL = "financial"
    LEGAL = "legal"
    PERMITS = "permits"
    CERTIFICATIONS = "certifications"
    CONTRACTS = "contracts"
    RECEIPTS = "receipts"


@dataclass
class Document:
    """Document record"""
    id: str
    name: str
    category: DocumentCategory
    file_path: str
    file_type: str
    upload_date: date
    document_date: date
    year: int
    tags: List[str]
    description: str
    expiration_date: Optional[date]
    related_entity: str


# =============================================================================
# TAX AND FINANCIAL DATA
# =============================================================================

# MACRS recovery periods by asset type
MACRS_RECOVERY_PERIODS = {
    AssetType.MACHINERY: 7,
    AssetType.EQUIPMENT: 7,
    AssetType.VEHICLE: 5,
    AssetType.BUILDING: 20,  # Farm buildings
    AssetType.LAND_IMPROVEMENT: 15,
    AssetType.LIVESTOCK_BREEDING: 7,
    AssetType.COMPUTER: 5,
    AssetType.OFFICE_EQUIPMENT: 7
}

# MACRS 7-year GDS depreciation percentages
MACRS_7_YEAR = [14.29, 24.49, 17.49, 12.49, 8.93, 8.92, 8.93, 4.46]
MACRS_5_YEAR = [20.00, 32.00, 19.20, 11.52, 11.52, 5.76]
MACRS_15_YEAR = [5.00, 9.50, 8.55, 7.70, 6.93, 6.23, 5.90, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, 2.95]

# Section 179 limits (2024)
SECTION_179_LIMIT = 1160000
SECTION_179_PHASE_OUT = 2890000

# Self-employment tax rates
SE_TAX_RATE = 0.153
SE_TAX_WAGE_BASE = 168600  # 2024

# Regional benchmarks (Louisiana averages)
REGIONAL_BENCHMARKS = {
    "corn": {
        BenchmarkMetric.YIELD_PER_ACRE: 180,
        BenchmarkMetric.COST_PER_ACRE: 850,
        BenchmarkMetric.REVENUE_PER_ACRE: 810,
        BenchmarkMetric.COST_PER_BUSHEL: 4.72
    },
    "soybeans": {
        BenchmarkMetric.YIELD_PER_ACRE: 50,
        BenchmarkMetric.COST_PER_ACRE: 420,
        BenchmarkMetric.REVENUE_PER_ACRE: 512,
        BenchmarkMetric.COST_PER_BUSHEL: 8.40
    },
    "rice": {
        BenchmarkMetric.YIELD_PER_ACRE: 7200,
        BenchmarkMetric.COST_PER_ACRE: 950,
        BenchmarkMetric.REVENUE_PER_ACRE: 1044
    },
    "cotton": {
        BenchmarkMetric.YIELD_PER_ACRE: 1100,
        BenchmarkMetric.COST_PER_ACRE: 780,
        BenchmarkMetric.REVENUE_PER_ACRE: 792
    }
}


# =============================================================================
# FARM BUSINESS SERVICE CLASS
# =============================================================================

class FarmBusinessService:
    """Complete farm business management service"""

    def __init__(self):
        # Tax Planning
        self.assets: Dict[str, DepreciableAsset] = {}
        self.tax_projections: Dict[str, TaxProjection] = {}

        # Succession Planning
        self.family_members: Dict[str, FamilyMember] = {}
        self.milestones: Dict[str, SuccessionMilestone] = {}
        self.transfer_plans: Dict[str, AssetTransferPlan] = {}

        # Benchmarking
        self.benchmarks: Dict[str, BenchmarkRecord] = {}
        self.historical_data: Dict[str, List[Dict[str, Any]]] = {}

        # Document Vault
        self.documents: Dict[str, Document] = {}

        self._counters = {
            "asset": 0, "projection": 0, "family": 0, "milestone": 0,
            "transfer": 0, "benchmark": 0, "document": 0
        }

    def _next_id(self, prefix: str) -> str:
        self._counters[prefix] += 1
        return f"{prefix.upper()}-{self._counters[prefix]:04d}"

    # =========================================================================
    # TAX PLANNING TOOLS
    # =========================================================================

    def add_depreciable_asset(
        self,
        name: str,
        asset_type: str,
        purchase_date: date,
        purchase_price: float,
        salvage_value: float = 0,
        useful_life_years: int = None,
        depreciation_method: str = "macrs_gds",
        section_179_amount: float = 0,
        bonus_depreciation_pct: float = 0,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Add a depreciable asset"""
        try:
            atype = AssetType(asset_type)
            dmethod = DepreciationMethod(depreciation_method)
        except ValueError as e:
            return {"error": str(e)}

        asset_id = self._next_id("asset")

        # Default useful life from MACRS
        if useful_life_years is None:
            useful_life_years = MACRS_RECOVERY_PERIODS.get(atype, 7)

        # Calculate first year depreciation
        first_year_dep = self._calculate_first_year_depreciation(
            purchase_price, salvage_value, useful_life_years,
            dmethod, section_179_amount, bonus_depreciation_pct
        )

        asset = DepreciableAsset(
            id=asset_id,
            name=name,
            asset_type=atype,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            salvage_value=salvage_value,
            useful_life_years=useful_life_years,
            depreciation_method=dmethod,
            section_179_amount=section_179_amount,
            bonus_depreciation_pct=bonus_depreciation_pct,
            accumulated_depreciation=first_year_dep,
            current_book_value=purchase_price - first_year_dep,
            notes=notes
        )

        self.assets[asset_id] = asset

        return {
            "id": asset_id,
            "name": name,
            "asset_type": asset_type,
            "purchase_price": purchase_price,
            "depreciation_method": depreciation_method,
            "useful_life": useful_life_years,
            "first_year_depreciation": round(first_year_dep, 2),
            "current_book_value": round(asset.current_book_value, 2),
            "message": f"Asset '{name}' added - ${first_year_dep:,.2f} first year depreciation"
        }

    def _calculate_first_year_depreciation(
        self,
        cost: float,
        salvage: float,
        life: int,
        method: DepreciationMethod,
        section_179: float,
        bonus_pct: float
    ) -> float:
        """Calculate first year depreciation"""
        depreciable_base = cost - salvage

        if method == DepreciationMethod.SECTION_179:
            return min(section_179, depreciable_base, SECTION_179_LIMIT)

        # Apply Section 179 first
        remaining_base = depreciable_base - section_179

        # Apply bonus depreciation
        bonus = remaining_base * (bonus_pct / 100)
        remaining_base -= bonus

        # Apply regular depreciation
        if method == DepreciationMethod.STRAIGHT_LINE:
            regular = remaining_base / life
        elif method in [DepreciationMethod.MACRS_GDS, DepreciationMethod.MACRS_ADS]:
            if life == 5:
                regular = remaining_base * (MACRS_5_YEAR[0] / 100)
            elif life == 7:
                regular = remaining_base * (MACRS_7_YEAR[0] / 100)
            elif life == 15:
                regular = remaining_base * (MACRS_15_YEAR[0] / 100)
            else:
                regular = remaining_base / life
        else:
            regular = remaining_base / life

        return section_179 + bonus + regular

    def get_depreciation_schedule(self, asset_id: str) -> Dict[str, Any]:
        """Get full depreciation schedule for an asset"""
        if asset_id not in self.assets:
            return {"error": f"Asset {asset_id} not found"}

        asset = self.assets[asset_id]

        schedule = []
        book_value = asset.purchase_price
        depreciable_base = asset.purchase_price - asset.salvage_value
        remaining_base = depreciable_base - asset.section_179_amount
        bonus = remaining_base * (asset.bonus_depreciation_pct / 100)
        remaining_after_bonus = remaining_base - bonus

        # Year 1
        year1_dep = asset.section_179_amount + bonus
        if asset.useful_life_years == 5:
            year1_dep += remaining_after_bonus * (MACRS_5_YEAR[0] / 100)
        elif asset.useful_life_years == 7:
            year1_dep += remaining_after_bonus * (MACRS_7_YEAR[0] / 100)
        else:
            year1_dep += remaining_after_bonus / asset.useful_life_years

        book_value -= year1_dep
        schedule.append({
            "year": 1,
            "depreciation": round(year1_dep, 2),
            "accumulated": round(year1_dep, 2),
            "book_value": round(book_value, 2)
        })

        accumulated = year1_dep

        # Remaining years
        if asset.useful_life_years == 5:
            rates = MACRS_5_YEAR[1:]
        elif asset.useful_life_years == 7:
            rates = MACRS_7_YEAR[1:]
        elif asset.useful_life_years == 15:
            rates = MACRS_15_YEAR[1:]
        else:
            rates = [100 / asset.useful_life_years] * (asset.useful_life_years - 1)

        for i, rate in enumerate(rates):
            if asset.useful_life_years in [5, 7, 15]:
                year_dep = remaining_after_bonus * (rate / 100)
            else:
                year_dep = remaining_after_bonus / asset.useful_life_years

            book_value -= year_dep
            accumulated += year_dep

            if book_value < asset.salvage_value:
                book_value = asset.salvage_value

            schedule.append({
                "year": i + 2,
                "depreciation": round(year_dep, 2),
                "accumulated": round(accumulated, 2),
                "book_value": round(max(book_value, asset.salvage_value), 2)
            })

        return {
            "asset_id": asset_id,
            "asset_name": asset.name,
            "purchase_price": asset.purchase_price,
            "salvage_value": asset.salvage_value,
            "useful_life": asset.useful_life_years,
            "method": asset.depreciation_method.value,
            "section_179": asset.section_179_amount,
            "bonus_pct": asset.bonus_depreciation_pct,
            "schedule": schedule
        }

    def calculate_section_179_optimization(
        self,
        purchases: List[Dict[str, float]],  # [{name, cost}]
        current_section_179_used: float = 0
    ) -> Dict[str, Any]:
        """Optimize Section 179 elections"""
        available_179 = SECTION_179_LIMIT - current_section_179_used

        # Sort by cost descending to maximize deduction
        sorted_purchases = sorted(purchases, key=lambda x: x["cost"], reverse=True)

        recommendations = []
        total_179 = 0
        remaining_179 = available_179

        for purchase in sorted_purchases:
            if remaining_179 <= 0:
                recommendations.append({
                    "asset": purchase["name"],
                    "cost": purchase["cost"],
                    "section_179": 0,
                    "recommendation": "Use MACRS depreciation"
                })
            elif purchase["cost"] <= remaining_179:
                recommendations.append({
                    "asset": purchase["name"],
                    "cost": purchase["cost"],
                    "section_179": purchase["cost"],
                    "recommendation": "Full Section 179"
                })
                total_179 += purchase["cost"]
                remaining_179 -= purchase["cost"]
            else:
                recommendations.append({
                    "asset": purchase["name"],
                    "cost": purchase["cost"],
                    "section_179": remaining_179,
                    "recommendation": f"Partial 179 (${remaining_179:,.0f}), balance MACRS"
                })
                total_179 += remaining_179
                remaining_179 = 0

        return {
            "section_179_limit": SECTION_179_LIMIT,
            "previously_used": current_section_179_used,
            "available": available_179,
            "purchases_count": len(purchases),
            "total_purchases": sum(p["cost"] for p in purchases),
            "recommended_179_total": total_179,
            "remaining_179": available_179 - total_179,
            "recommendations": recommendations,
            "tax_savings_estimate": round(total_179 * 0.32, 2)  # Assuming 32% bracket
        }

    def project_tax_liability(
        self,
        tax_year: int,
        gross_income: float,
        expenses: Dict[str, float],
        depreciation: float,
        entity_type: str = "schedule_f"
    ) -> Dict[str, Any]:
        """Project farm tax liability"""
        try:
            etype = TaxEntity(entity_type)
        except ValueError:
            return {"error": f"Invalid entity type: {entity_type}"}

        projection_id = self._next_id("projection")

        total_expenses = sum(expenses.values())
        net_farm_income = gross_income - total_expenses - depreciation

        # Self-employment tax (for Schedule F)
        if etype == TaxEntity.SCHEDULE_F:
            se_income = net_farm_income * 0.9235  # Adjusted for SE tax
            se_tax = min(se_income, SE_TAX_WAGE_BASE) * SE_TAX_RATE
            if se_income > SE_TAX_WAGE_BASE:
                se_tax += (se_income - SE_TAX_WAGE_BASE) * 0.029  # Medicare
        else:
            se_tax = 0

        # Estimated income tax (simplified)
        taxable_income = net_farm_income - (se_tax / 2)  # SE deduction
        if taxable_income <= 0:
            income_tax = 0
        elif taxable_income <= 23200:  # 12% bracket married filing jointly
            income_tax = taxable_income * 0.12
        elif taxable_income <= 94300:
            income_tax = 2784 + (taxable_income - 23200) * 0.22
        else:
            income_tax = 18426 + (taxable_income - 94300) * 0.24

        total_tax = se_tax + income_tax

        projection = TaxProjection(
            id=projection_id,
            tax_year=tax_year,
            entity_type=etype,
            gross_income=gross_income,
            total_expenses=total_expenses,
            depreciation=depreciation,
            net_farm_income=net_farm_income,
            self_employment_tax=se_tax,
            estimated_income_tax=income_tax,
            total_tax_liability=total_tax
        )

        self.tax_projections[projection_id] = projection

        return {
            "id": projection_id,
            "tax_year": tax_year,
            "income_summary": {
                "gross_income": gross_income,
                "total_expenses": total_expenses,
                "depreciation": depreciation,
                "net_farm_income": round(net_farm_income, 2)
            },
            "tax_liability": {
                "self_employment_tax": round(se_tax, 2),
                "estimated_income_tax": round(income_tax, 2),
                "total_tax": round(total_tax, 2)
            },
            "effective_rate": f"{round(total_tax / net_farm_income * 100, 1)}%" if net_farm_income > 0 else "N/A",
            "quarterly_estimates": round(total_tax / 4, 2)
        }

    def income_timing_analysis(
        self,
        current_year_income: float,
        next_year_projected_income: float,
        deferrable_income: float
    ) -> Dict[str, Any]:
        """Analyze income timing strategies"""
        # Current year with all income
        current_with_all = self.project_tax_liability(
            date.today().year, current_year_income, {}, 0, "schedule_f"
        )

        # Current year with deferred income
        current_deferred = self.project_tax_liability(
            date.today().year, current_year_income - deferrable_income, {}, 0, "schedule_f"
        )

        # Next year scenarios
        next_with_deferred = self.project_tax_liability(
            date.today().year + 1, next_year_projected_income + deferrable_income, {}, 0, "schedule_f"
        )

        next_without = self.project_tax_liability(
            date.today().year + 1, next_year_projected_income, {}, 0, "schedule_f"
        )

        # Calculate total tax under each scenario
        scenario_a_tax = current_with_all["tax_liability"]["total_tax"] + next_without["tax_liability"]["total_tax"]
        scenario_b_tax = current_deferred["tax_liability"]["total_tax"] + next_with_deferred["tax_liability"]["total_tax"]

        savings = scenario_a_tax - scenario_b_tax

        return {
            "deferrable_income": deferrable_income,
            "scenario_a": {
                "description": "Recognize all income this year",
                "current_year_tax": current_with_all["tax_liability"]["total_tax"],
                "next_year_tax": next_without["tax_liability"]["total_tax"],
                "total_tax": round(scenario_a_tax, 2)
            },
            "scenario_b": {
                "description": "Defer income to next year",
                "current_year_tax": current_deferred["tax_liability"]["total_tax"],
                "next_year_tax": next_with_deferred["tax_liability"]["total_tax"],
                "total_tax": round(scenario_b_tax, 2)
            },
            "recommendation": "Defer income" if savings > 0 else "Recognize income now",
            "estimated_savings": round(abs(savings), 2),
            "note": "Consult tax professional for complete analysis"
        }

    # =========================================================================
    # SUCCESSION PLANNING
    # =========================================================================

    def add_family_member(
        self,
        name: str,
        relationship: str,
        age: int,
        role: str,
        ownership_pct: float = 0,
        involved_in_operations: bool = False,
        skills: List[str] = None,
        interests: List[str] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Add family member to succession plan"""
        try:
            srole = SuccessorRole(role)
        except ValueError:
            return {"error": f"Invalid role: {role}"}

        member_id = self._next_id("family")

        member = FamilyMember(
            id=member_id,
            name=name,
            relationship=relationship,
            age=age,
            role=srole,
            ownership_pct=ownership_pct,
            involved_in_operations=involved_in_operations,
            skills=skills or [],
            interests=interests or [],
            notes=notes
        )

        self.family_members[member_id] = member

        return {
            "id": member_id,
            "name": name,
            "relationship": relationship,
            "age": age,
            "role": role,
            "ownership_pct": ownership_pct,
            "message": f"Family member {name} added to succession plan"
        }

    def create_asset_transfer_plan(
        self,
        asset_description: str,
        current_owner: str,
        future_owner: str,
        transfer_method: str,
        estimated_value: float,
        planned_date: date,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Create an asset transfer plan"""
        try:
            tmethod = TransferMethod(transfer_method)
        except ValueError:
            return {"error": f"Invalid transfer method: {transfer_method}"}

        transfer_id = self._next_id("transfer")

        # Calculate tax implications
        tax_implications = self._calculate_transfer_taxes(tmethod, estimated_value)

        # Legal requirements
        legal_reqs = self._get_legal_requirements(tmethod)

        plan = AssetTransferPlan(
            id=transfer_id,
            asset_description=asset_description,
            current_owner=current_owner,
            future_owner=future_owner,
            transfer_method=tmethod,
            estimated_value=estimated_value,
            planned_date=planned_date,
            tax_implications=tax_implications,
            legal_requirements=legal_reqs,
            status="planned"
        )

        self.transfer_plans[transfer_id] = plan

        return {
            "id": transfer_id,
            "asset": asset_description,
            "from": current_owner,
            "to": future_owner,
            "method": transfer_method,
            "value": estimated_value,
            "planned_date": planned_date.isoformat(),
            "tax_implications": tax_implications,
            "legal_requirements": legal_reqs,
            "message": f"Transfer plan created for {asset_description}"
        }

    def _calculate_transfer_taxes(self, method: TransferMethod, value: float) -> Dict[str, float]:
        """Calculate estimated taxes for transfer"""
        if method == TransferMethod.SALE:
            # Capital gains (assuming long-term, 15%)
            return {
                "capital_gains_tax": round(value * 0.15, 2),
                "state_tax": round(value * 0.05, 2),
                "transfer_fees": round(value * 0.01, 2)
            }
        elif method == TransferMethod.GIFT:
            # Gift tax (exempt up to annual exclusion)
            annual_exclusion = 18000  # 2024
            taxable_gift = max(0, value - annual_exclusion)
            return {
                "gift_tax_filing": "Required" if value > annual_exclusion else "Not required",
                "uses_lifetime_exemption": taxable_gift,
                "actual_tax_due": 0  # Usually covered by lifetime exemption
            }
        elif method == TransferMethod.INHERITANCE:
            return {
                "estate_tax": 0,  # Below $13.61M exemption for most farms
                "stepped_up_basis": value,
                "income_tax": 0
            }
        elif method == TransferMethod.INSTALLMENT_SALE:
            return {
                "annual_gain_recognition": "Spread over payment period",
                "interest_income": "Taxable to seller",
                "capital_gains_rate": "15-20%"
            }
        else:
            return {"note": "Consult tax professional for specific implications"}

    def _get_legal_requirements(self, method: TransferMethod) -> List[str]:
        """Get legal requirements for transfer method"""
        base_reqs = ["Written agreement", "Legal review recommended"]

        if method == TransferMethod.SALE:
            return base_reqs + ["Bill of sale", "Title transfer", "Update registrations"]
        elif method == TransferMethod.GIFT:
            return base_reqs + ["Gift tax return (Form 709) if over annual exclusion", "Deed transfer for real property"]
        elif method == TransferMethod.INHERITANCE:
            return ["Will or trust document", "Probate (if no trust)", "Estate tax return if required"]
        elif method == TransferMethod.TRUST:
            return ["Trust document", "Asset retitling", "Trustee designation", "Beneficiary designations"]
        elif method == TransferMethod.LLC_TRANSFER:
            return ["Operating agreement amendment", "Membership interest transfer", "State filing if required"]
        else:
            return base_reqs

    def add_succession_milestone(
        self,
        title: str,
        target_date: date,
        description: str,
        responsible_party: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Add a succession planning milestone"""
        milestone_id = self._next_id("milestone")

        milestone = SuccessionMilestone(
            id=milestone_id,
            title=title,
            target_date=target_date,
            description=description,
            responsible_party=responsible_party,
            status="planned",
            notes=notes
        )

        self.milestones[milestone_id] = milestone

        return {
            "id": milestone_id,
            "title": title,
            "target_date": target_date.isoformat(),
            "responsible": responsible_party,
            "status": "planned",
            "message": f"Milestone '{title}' added"
        }

    def get_succession_timeline(self) -> Dict[str, Any]:
        """Get succession plan timeline"""
        milestones = sorted(
            self.milestones.values(),
            key=lambda x: x.target_date
        )

        timeline = []
        for m in milestones:
            days_until = (m.target_date - date.today()).days
            timeline.append({
                "id": m.id,
                "title": m.title,
                "target_date": m.target_date.isoformat(),
                "responsible": m.responsible_party,
                "status": m.status,
                "days_until": days_until,
                "urgency": "overdue" if days_until < 0 else "urgent" if days_until < 30 else "upcoming" if days_until < 90 else "planned"
            })

        return {
            "total_milestones": len(timeline),
            "completed": len([m for m in timeline if m["status"] == "completed"]),
            "overdue": len([m for m in timeline if m["urgency"] == "overdue"]),
            "timeline": timeline
        }

    def generate_succession_summary(self) -> Dict[str, Any]:
        """Generate comprehensive succession plan summary"""
        members = list(self.family_members.values())
        transfers = list(self.transfer_plans.values())
        milestones = list(self.milestones.values())

        total_ownership = sum(m.ownership_pct for m in members)
        total_transfer_value = sum(t.estimated_value for t in transfers)

        return {
            "family_members": {
                "count": len(members),
                "by_role": {
                    role.value: len([m for m in members if m.role == role])
                    for role in SuccessorRole
                },
                "total_ownership_allocated": total_ownership
            },
            "transfer_plans": {
                "count": len(transfers),
                "total_value": total_transfer_value,
                "by_method": {
                    method.value: len([t for t in transfers if t.transfer_method == method])
                    for method in TransferMethod if any(t.transfer_method == method for t in transfers)
                }
            },
            "milestones": {
                "total": len(milestones),
                "completed": len([m for m in milestones if m.status == "completed"]),
                "in_progress": len([m for m in milestones if m.status == "in_progress"]),
                "planned": len([m for m in milestones if m.status == "planned"])
            },
            "recommendations": self._get_succession_recommendations(members, transfers)
        }

    def _get_succession_recommendations(self, members: List[FamilyMember], transfers: List[AssetTransferPlan]) -> List[str]:
        """Generate succession planning recommendations"""
        recommendations = []

        if not members:
            recommendations.append("Define family members and their roles in the succession plan")

        if not transfers:
            recommendations.append("Create asset transfer plans for major farm assets")

        total_ownership = sum(m.ownership_pct for m in members)
        if total_ownership > 100:
            recommendations.append(f"Review ownership allocations - currently totals {total_ownership}%")
        elif total_ownership < 100:
            recommendations.append(f"Allocate remaining {100 - total_ownership}% ownership")

        operators = [m for m in members if m.role == SuccessorRole.PRIMARY_OPERATOR]
        if not operators:
            recommendations.append("Identify primary operator successor")

        return recommendations if recommendations else ["Succession plan is well-structured"]

    # =========================================================================
    # BENCHMARKING DASHBOARD
    # =========================================================================

    def record_benchmark_data(
        self,
        year: int,
        crop: str,
        field_id: str,
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Record benchmark data for a field/year"""
        results = []

        for metric_name, value in metrics.items():
            try:
                metric = BenchmarkMetric(metric_name)
            except ValueError:
                continue

            benchmark_id = self._next_id("benchmark")

            # Get regional benchmarks
            regional = REGIONAL_BENCHMARKS.get(crop, {}).get(metric, value)

            # Calculate percentile (simplified)
            if regional > 0:
                pct_of_regional = value / regional * 100
                if pct_of_regional >= 110:
                    percentile = 90
                elif pct_of_regional >= 100:
                    percentile = 75
                elif pct_of_regional >= 90:
                    percentile = 50
                else:
                    percentile = 25
            else:
                percentile = 50

            record = BenchmarkRecord(
                id=benchmark_id,
                year=year,
                metric=metric,
                crop=crop,
                field_id=field_id,
                actual_value=value,
                farm_average=value,  # Would aggregate from all fields
                regional_average=regional,
                top_quartile=regional * 1.15,  # Estimated
                percentile_rank=percentile
            )

            self.benchmarks[benchmark_id] = record

            results.append({
                "metric": metric_name,
                "actual": value,
                "regional_avg": regional,
                "percentile": percentile,
                "vs_regional": f"{round((value - regional) / regional * 100, 1):+}%" if regional > 0 else "N/A"
            })

        return {
            "year": year,
            "crop": crop,
            "field_id": field_id,
            "metrics_recorded": len(results),
            "results": results
        }

    def compare_year_over_year(
        self,
        crop: str,
        metric: str,
        years: List[int] = None
    ) -> Dict[str, Any]:
        """Compare performance year over year"""
        try:
            bmetric = BenchmarkMetric(metric)
        except ValueError:
            return {"error": f"Invalid metric: {metric}"}

        if years is None:
            years = list(range(date.today().year - 4, date.today().year + 1))

        comparisons = []
        previous_value = None

        for year in sorted(years):
            year_records = [
                b for b in self.benchmarks.values()
                if b.year == year and b.crop == crop and b.metric == bmetric
            ]

            if year_records:
                avg_value = statistics.mean([r.actual_value for r in year_records])
                regional = year_records[0].regional_average

                change = None
                if previous_value:
                    change = (avg_value - previous_value) / previous_value * 100

                comparisons.append({
                    "year": year,
                    "value": round(avg_value, 2),
                    "regional_avg": regional,
                    "vs_regional": f"{round((avg_value - regional) / regional * 100, 1):+}%" if regional else "N/A",
                    "yoy_change": f"{round(change, 1):+}%" if change else "N/A"
                })

                previous_value = avg_value

        return {
            "crop": crop,
            "metric": metric,
            "years_compared": len(comparisons),
            "trend": self._calculate_trend(comparisons),
            "comparisons": comparisons
        }

    def _calculate_trend(self, comparisons: List[Dict[str, Any]]) -> str:
        """Calculate trend from comparisons"""
        if len(comparisons) < 3:
            return "insufficient_data"

        values = [c["value"] for c in comparisons]
        recent = statistics.mean(values[-2:])
        earlier = statistics.mean(values[:-2])

        if recent > earlier * 1.05:
            return "improving"
        elif recent < earlier * 0.95:
            return "declining"
        else:
            return "stable"

    def get_benchmark_summary(self, crop: str = None, year: int = None) -> Dict[str, Any]:
        """Get benchmark summary dashboard"""
        if year is None:
            year = date.today().year

        records = list(self.benchmarks.values())
        if crop:
            records = [r for r in records if r.crop == crop]
        if year:
            records = [r for r in records if r.year == year]

        if not records:
            return {
                "year": year,
                "crop": crop,
                "message": "No benchmark data available",
                "regional_benchmarks": REGIONAL_BENCHMARKS.get(crop, {}) if crop else REGIONAL_BENCHMARKS
            }

        summary = {}
        for record in records:
            metric_name = record.metric.value
            if metric_name not in summary:
                summary[metric_name] = {
                    "values": [],
                    "regional": record.regional_average
                }
            summary[metric_name]["values"].append(record.actual_value)

        results = []
        for metric_name, data in summary.items():
            avg = statistics.mean(data["values"])
            regional = data["regional"]
            results.append({
                "metric": metric_name,
                "your_average": round(avg, 2),
                "regional_average": regional,
                "percentile": self._calculate_percentile(avg, regional),
                "status": "above_average" if avg > regional else "below_average" if avg < regional else "average"
            })

        return {
            "year": year,
            "crop": crop or "all",
            "metrics_count": len(results),
            "results": results,
            "overall_performance": self._rate_overall_performance(results)
        }

    def _calculate_percentile(self, value: float, regional: float) -> int:
        """Calculate percentile rank"""
        if regional <= 0:
            return 50
        ratio = value / regional
        if ratio >= 1.2:
            return 95
        elif ratio >= 1.1:
            return 85
        elif ratio >= 1.0:
            return 70
        elif ratio >= 0.9:
            return 50
        elif ratio >= 0.8:
            return 30
        else:
            return 15

    def _rate_overall_performance(self, results: List[Dict[str, Any]]) -> str:
        """Rate overall performance"""
        if not results:
            return "No data"

        above = len([r for r in results if r["status"] == "above_average"])
        total = len(results)

        if above >= total * 0.75:
            return "Excellent"
        elif above >= total * 0.5:
            return "Good"
        elif above >= total * 0.25:
            return "Average"
        else:
            return "Needs Improvement"

    # =========================================================================
    # DOCUMENT VAULT
    # =========================================================================

    def add_document(
        self,
        name: str,
        category: str,
        file_path: str,
        document_date: date,
        year: int = None,
        tags: List[str] = None,
        description: str = "",
        expiration_date: date = None,
        related_entity: str = ""
    ) -> Dict[str, Any]:
        """Add a document to the vault"""
        try:
            dcat = DocumentCategory(category)
        except ValueError:
            return {"error": f"Invalid category: {category}"}

        doc_id = self._next_id("document")

        # Determine file type from path
        file_type = file_path.split(".")[-1].lower() if "." in file_path else "unknown"

        document = Document(
            id=doc_id,
            name=name,
            category=dcat,
            file_path=file_path,
            file_type=file_type,
            upload_date=date.today(),
            document_date=document_date,
            year=year or document_date.year,
            tags=tags or [],
            description=description,
            expiration_date=expiration_date,
            related_entity=related_entity
        )

        self.documents[doc_id] = document

        return {
            "id": doc_id,
            "name": name,
            "category": category,
            "file_type": file_type,
            "document_date": document_date.isoformat(),
            "expires": expiration_date.isoformat() if expiration_date else None,
            "message": f"Document '{name}' added to vault"
        }

    def search_documents(
        self,
        category: str = None,
        year: int = None,
        tags: List[str] = None,
        search_text: str = None
    ) -> Dict[str, Any]:
        """Search documents in vault"""
        results = []

        for doc in self.documents.values():
            if category and doc.category.value != category:
                continue
            if year and doc.year != year:
                continue
            if tags and not any(t in doc.tags for t in tags):
                continue
            if search_text and search_text.lower() not in doc.name.lower() and search_text.lower() not in doc.description.lower():
                continue

            results.append({
                "id": doc.id,
                "name": doc.name,
                "category": doc.category.value,
                "date": doc.document_date.isoformat(),
                "year": doc.year,
                "file_type": doc.file_type,
                "tags": doc.tags,
                "expires": doc.expiration_date.isoformat() if doc.expiration_date else None
            })

        results.sort(key=lambda x: x["date"], reverse=True)

        return {
            "search_criteria": {
                "category": category,
                "year": year,
                "tags": tags,
                "text": search_text
            },
            "results_count": len(results),
            "documents": results
        }

    def get_expiring_documents(self, days_ahead: int = 90) -> Dict[str, Any]:
        """Get documents expiring soon"""
        cutoff = date.today() + timedelta(days=days_ahead)
        expiring = []

        for doc in self.documents.values():
            if doc.expiration_date and doc.expiration_date <= cutoff:
                days_until = (doc.expiration_date - date.today()).days
                expiring.append({
                    "id": doc.id,
                    "name": doc.name,
                    "category": doc.category.value,
                    "expires": doc.expiration_date.isoformat(),
                    "days_until": days_until,
                    "status": "expired" if days_until < 0 else "critical" if days_until < 30 else "warning"
                })

        expiring.sort(key=lambda x: x["days_until"])

        return {
            "as_of": date.today().isoformat(),
            "days_ahead": days_ahead,
            "expiring_count": len(expiring),
            "expired": len([e for e in expiring if e["status"] == "expired"]),
            "critical": len([e for e in expiring if e["status"] == "critical"]),
            "documents": expiring
        }

    def get_document_categories(self) -> Dict[str, Any]:
        """Get available document categories"""
        return {
            "categories": [
                {"id": c.value, "name": c.value.replace("_", " ").title()}
                for c in DocumentCategory
            ]
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_farm_business_service: Optional[FarmBusinessService] = None


def get_farm_business_service() -> FarmBusinessService:
    """Get or create the farm business service singleton"""
    global _farm_business_service
    if _farm_business_service is None:
        _farm_business_service = FarmBusinessService()
    return _farm_business_service
