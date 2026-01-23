"""
Community & Economic Impact Service
Track and quantify community, economic, and social impacts for grant applications.

Features:
- Local economic multiplier calculations
- Job creation/support tracking
- Local food system analytics
- Rural development metrics
- Educational outreach tracking
- Beginning farmer support
- Social impact measurement
- Community partnerships
- Economic ripple effects
"""

from datetime import datetime, date
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class ImpactCategory(str, Enum):
    ECONOMIC = "economic"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    FOOD_ACCESS = "food_access"
    ENVIRONMENTAL = "environmental"
    COMMUNITY = "community"
    HEALTH = "health"


class OutreachType(str, Enum):
    FIELD_DAY = "field_day"
    WORKSHOP = "workshop"
    PRESENTATION = "presentation"
    FARM_TOUR = "farm_tour"
    PUBLICATION = "publication"
    MEDIA = "media"
    MENTORING = "mentoring"
    PARTNERSHIP = "partnership"


class LocalMarketChannel(str, Enum):
    FARMERS_MARKET = "farmers_market"
    CSA = "csa"
    FARM_STAND = "farm_stand"
    RESTAURANT = "restaurant"
    GROCERY_LOCAL = "grocery_local"
    SCHOOL = "school"
    HOSPITAL = "hospital"
    FOOD_HUB = "food_hub"
    DIRECT_TO_CONSUMER = "direct_to_consumer"


class PartnerType(str, Enum):
    UNIVERSITY = "university"
    EXTENSION = "extension"
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government"
    PRODUCER_GROUP = "producer_group"
    BUYER = "buyer"
    SUPPLIER = "supplier"
    FINANCIAL = "financial"


# Economic multipliers by sector (IMPLAN-based averages)
ECONOMIC_MULTIPLIERS = {
    "crop_production": {
        "output": 1.64,      # $1 in crop sales generates $1.64 in regional output
        "employment": 12.3,   # Jobs per $1M output
        "labor_income": 0.28  # $0.28 in wages per $1 output
    },
    "livestock": {
        "output": 1.72,
        "employment": 8.1,
        "labor_income": 0.22
    },
    "value_added": {
        "output": 2.05,
        "employment": 15.4,
        "labor_income": 0.35
    },
    "local_food": {
        "output": 1.85,
        "employment": 18.2,
        "labor_income": 0.42
    },
    "agritourism": {
        "output": 1.92,
        "employment": 22.1,
        "labor_income": 0.48
    }
}

# Local food system metrics
LOCAL_FOOD_METRICS = {
    "food_miles_reduction": {
        "description": "Average miles saved vs conventional supply chain",
        "conventional_avg_miles": 1500,
        "local_avg_miles": 50
    },
    "food_dollar_retained": {
        "description": "Percent of food dollar staying in local economy",
        "conventional": 0.15,  # 15% stays local
        "direct_market": 0.65,  # 65% stays local
        "local_retail": 0.45   # 45% stays local
    },
    "freshness_advantage": {
        "description": "Days fresher than conventional",
        "conventional_days": 7,
        "local_days": 1
    }
}


@dataclass
class Employee:
    """Farm employee record"""
    employee_id: str
    name: str
    role: str
    employment_type: str  # full-time, part-time, seasonal
    hourly_rate: float
    hours_per_week: float
    start_date: date
    end_date: Optional[date] = None
    local_resident: bool = True
    benefits_provided: List[str] = field(default_factory=list)


@dataclass
class LocalSale:
    """Local market sale record"""
    sale_id: str
    sale_date: date
    market_channel: LocalMarketChannel
    buyer_name: str
    buyer_location: str
    product: str
    quantity: float
    unit: str
    total_value: float
    miles_to_buyer: float


@dataclass
class OutreachEvent:
    """Educational outreach event"""
    event_id: str
    event_date: date
    event_type: OutreachType
    title: str
    description: str
    attendees: int
    target_audience: str
    topics_covered: List[str]
    partner_organizations: List[str] = field(default_factory=list)
    feedback_score: float = 0  # 1-5 scale
    follow_up_actions: List[str] = field(default_factory=list)


@dataclass
class Partnership:
    """Community partnership record"""
    partnership_id: str
    partner_name: str
    partner_type: PartnerType
    contact_person: str
    start_date: date
    description: str
    activities: List[str]
    value_contributed: float
    value_received: float
    active: bool = True


@dataclass
class BeginningFarmerSupport:
    """Support provided to beginning farmers"""
    support_id: str
    farmer_name: str
    start_date: date
    support_type: str  # mentoring, training, land access, equipment sharing
    hours_provided: float
    topics_covered: List[str]
    outcomes: str = ""


class CommunityImpactService:
    """
    Community and economic impact tracking service.
    Essential for grant applications requiring community benefit documentation.
    """

    def __init__(self):
        self.employees: List[Employee] = []
        self.local_sales: List[LocalSale] = []
        self.outreach_events: List[OutreachEvent] = []
        self.partnerships: List[Partnership] = []
        self.beginning_farmer_support: List[BeginningFarmerSupport] = []

    # =========================================================================
    # EMPLOYMENT & ECONOMIC IMPACT
    # =========================================================================

    def add_employee(self, employee: Employee) -> Dict:
        """Add employee record"""
        self.employees.append(employee)

        annual_wages = employee.hourly_rate * employee.hours_per_week * 52

        return {
            "success": True,
            "employee_id": employee.employee_id,
            "role": employee.role,
            "employment_type": employee.employment_type,
            "estimated_annual_wages": round(annual_wages, 2),
            "message": "Employee added to impact tracking"
        }

    def calculate_employment_impact(self) -> Dict:
        """Calculate farm's employment and economic impact"""

        if not self.employees:
            return {
                "total_employees": 0,
                "message": "No employees recorded"
            }

        # Count by type
        full_time = [e for e in self.employees if e.employment_type == "full-time" and e.end_date is None]
        part_time = [e for e in self.employees if e.employment_type == "part-time" and e.end_date is None]
        seasonal = [e for e in self.employees if e.employment_type == "seasonal"]

        # Calculate FTE (Full-Time Equivalent)
        fte = len(full_time)
        fte += sum(e.hours_per_week / 40 for e in part_time)
        fte += sum(e.hours_per_week / 40 * 0.5 for e in seasonal)  # Assume half-year

        # Calculate total wages
        total_annual_wages = sum(
            e.hourly_rate * e.hours_per_week * 52
            for e in self.employees
            if e.end_date is None
        )

        # Calculate benefits value (estimate)
        benefits_value = 0
        for e in self.employees:
            if "health_insurance" in e.benefits_provided:
                benefits_value += 8000
            if "retirement" in e.benefits_provided:
                benefits_value += e.hourly_rate * e.hours_per_week * 52 * 0.03
            if "paid_leave" in e.benefits_provided:
                benefits_value += e.hourly_rate * 80  # 2 weeks

        # Local residents
        local_employees = len([e for e in self.employees if e.local_resident and e.end_date is None])

        # Economic ripple effect
        multiplier = ECONOMIC_MULTIPLIERS["crop_production"]
        total_compensation = total_annual_wages + benefits_value
        economic_output = total_compensation / multiplier["labor_income"] if multiplier["labor_income"] > 0 else 0
        regional_impact = economic_output * multiplier["output"]

        return {
            "employment_summary": {
                "full_time": len(full_time),
                "part_time": len(part_time),
                "seasonal": len(seasonal),
                "total_employees": len([e for e in self.employees if e.end_date is None]),
                "full_time_equivalent": round(fte, 1),
                "local_residents": local_employees,
                "local_hire_percent": round(local_employees / len(self.employees) * 100, 0) if self.employees else 0
            },
            "compensation": {
                "total_annual_wages": round(total_annual_wages, 0),
                "estimated_benefits_value": round(benefits_value, 0),
                "total_compensation": round(total_compensation, 0),
                "average_hourly_wage": round(
                    sum(e.hourly_rate for e in self.employees if e.end_date is None) /
                    len([e for e in self.employees if e.end_date is None]), 2
                ) if self.employees else 0
            },
            "economic_impact": {
                "direct_impact": round(total_compensation, 0),
                "indirect_indirect_impact": round(regional_impact - economic_output, 0),
                "total_regional_impact": round(regional_impact, 0),
                "output_multiplier_used": multiplier["output"]
            },
            "grant_metrics": {
                "jobs_created_supported": round(fte, 1),
                "local_wages_paid": round(total_annual_wages * (local_employees / len(self.employees)), 0) if self.employees else 0,
                "regional_economic_contribution": round(regional_impact, 0)
            }
        }

    def calculate_economic_multiplier_impact(
        self,
        annual_revenue: float,
        sector: str = "crop_production"
    ) -> Dict:
        """
        Calculate regional economic impact using economic multipliers.
        Essential for grant applications requiring economic impact analysis.
        """

        multiplier = ECONOMIC_MULTIPLIERS.get(sector, ECONOMIC_MULTIPLIERS["crop_production"])

        # Calculate impacts
        total_output = annual_revenue * multiplier["output"]
        jobs_supported = (annual_revenue / 1000000) * multiplier["employment"]
        labor_income = annual_revenue * multiplier["labor_income"]

        return {
            "direct_output": round(annual_revenue, 0),
            "sector": sector,
            "multipliers_used": multiplier,
            "regional_impacts": {
                "total_economic_output": round(total_output, 0),
                "indirect_induced_output": round(total_output - annual_revenue, 0),
                "jobs_supported_region": round(jobs_supported, 1),
                "labor_income_generated": round(labor_income, 0)
            },
            "impact_ratios": {
                "output_multiplier": f"{multiplier['output']}x",
                "jobs_per_million": multiplier["employment"],
                "labor_income_ratio": f"{multiplier['labor_income'] * 100:.0f}%"
            },
            "grant_language": {
                "summary": f"This farm operation generates an estimated ${round(total_output, 0):,} in total "
                          f"regional economic output annually, supporting approximately {round(jobs_supported, 1)} "
                          f"jobs and ${round(labor_income, 0):,} in labor income throughout the local economy."
            }
        }

    # =========================================================================
    # LOCAL FOOD SYSTEM
    # =========================================================================

    def record_local_sale(self, sale: LocalSale) -> Dict:
        """Record a sale to local market"""
        self.local_sales.append(sale)

        return {
            "success": True,
            "sale_id": sale.sale_id,
            "channel": sale.market_channel.value,
            "value": sale.total_value,
            "food_miles": sale.miles_to_buyer,
            "message": "Local sale recorded"
        }

    def calculate_local_food_impact(self, year: Optional[int] = None) -> Dict:
        """Calculate local food system impact"""

        sales = self.local_sales
        if year:
            sales = [s for s in sales if s.sale_date.year == year]

        if not sales:
            return {
                "total_local_sales": 0,
                "message": "No local sales recorded"
            }

        total_value = sum(s.total_value for s in sales)
        total_miles = sum(s.miles_to_buyer * s.quantity for s in sales)  # Weight by quantity
        avg_miles = total_miles / sum(s.quantity for s in sales) if sales else 0

        # By channel
        by_channel = {}
        for sale in sales:
            channel = sale.market_channel.value
            if channel not in by_channel:
                by_channel[channel] = {"sales": 0, "value": 0}
            by_channel[channel]["sales"] += 1
            by_channel[channel]["value"] += sale.total_value

        # Food miles saved
        conventional_miles = LOCAL_FOOD_METRICS["food_miles_reduction"]["conventional_avg_miles"]
        miles_saved = (conventional_miles - avg_miles) * sum(s.quantity for s in sales)

        # Local dollar retention
        direct_sales_value = sum(
            s.total_value for s in sales
            if s.market_channel in [LocalMarketChannel.FARMERS_MARKET,
                                   LocalMarketChannel.CSA,
                                   LocalMarketChannel.FARM_STAND,
                                   LocalMarketChannel.DIRECT_TO_CONSUMER]
        )
        local_retail_value = total_value - direct_sales_value

        local_dollars_retained = (
            direct_sales_value * LOCAL_FOOD_METRICS["food_dollar_retained"]["direct_market"] +
            local_retail_value * LOCAL_FOOD_METRICS["food_dollar_retained"]["local_retail"]
        )

        # Unique local buyers
        unique_buyers = len(set(s.buyer_name for s in sales))

        return {
            "period": year if year else "All Time",
            "sales_summary": {
                "total_transactions": len(sales),
                "total_value": round(total_value, 0),
                "unique_buyers": unique_buyers,
                "by_channel": by_channel
            },
            "food_miles": {
                "average_miles_to_buyer": round(avg_miles, 1),
                "conventional_comparison": conventional_miles,
                "total_miles_saved": round(miles_saved, 0),
                "carbon_equivalent_lbs": round(miles_saved * 0.9, 0)  # ~0.9 lbs CO2/mile
            },
            "local_economy": {
                "local_dollars_retained": round(local_dollars_retained, 0),
                "retention_rate": round(local_dollars_retained / total_value * 100, 0) if total_value > 0 else 0,
                "conventional_retention": f"{LOCAL_FOOD_METRICS['food_dollar_retained']['conventional'] * 100:.0f}%",
                "local_advantage": f"+{round((local_dollars_retained / total_value - LOCAL_FOOD_METRICS['food_dollar_retained']['conventional']) * 100, 0)}%"
                    if total_value > 0 else "N/A"
            },
            "freshness": {
                "typical_harvest_to_sale_days": LOCAL_FOOD_METRICS["freshness_advantage"]["local_days"],
                "conventional_days": LOCAL_FOOD_METRICS["freshness_advantage"]["conventional_days"],
                "freshness_advantage": f"{LOCAL_FOOD_METRICS['freshness_advantage']['conventional_days'] - LOCAL_FOOD_METRICS['freshness_advantage']['local_days']} days fresher"
            },
            "grant_metrics": {
                "local_sales_value": round(total_value, 0),
                "local_economic_retention": round(local_dollars_retained, 0),
                "food_miles_saved": round(miles_saved, 0),
                "local_buyers_served": unique_buyers
            }
        }

    # =========================================================================
    # EDUCATIONAL OUTREACH
    # =========================================================================

    def record_outreach_event(self, event: OutreachEvent) -> Dict:
        """Record educational outreach event"""
        self.outreach_events.append(event)

        return {
            "success": True,
            "event_id": event.event_id,
            "type": event.event_type.value,
            "attendees": event.attendees,
            "message": "Outreach event recorded"
        }

    def calculate_outreach_impact(self, year: Optional[int] = None) -> Dict:
        """Calculate educational outreach impact"""

        events = self.outreach_events
        if year:
            events = [e for e in events if e.event_date.year == year]

        if not events:
            return {
                "total_events": 0,
                "message": "No outreach events recorded"
            }

        total_attendees = sum(e.attendees for e in events)

        # By type
        by_type = {}
        for event in events:
            et = event.event_type.value
            if et not in by_type:
                by_type[et] = {"events": 0, "attendees": 0}
            by_type[et]["events"] += 1
            by_type[et]["attendees"] += event.attendees

        # Topics covered
        all_topics = []
        for event in events:
            all_topics.extend(event.topics_covered)
        topic_frequency = {}
        for topic in all_topics:
            topic_frequency[topic] = topic_frequency.get(topic, 0) + 1

        # Partner involvement
        all_partners = []
        for event in events:
            all_partners.extend(event.partner_organizations)
        unique_partners = list(set(all_partners))

        # Average feedback
        feedback_events = [e for e in events if e.feedback_score > 0]
        avg_feedback = sum(e.feedback_score for e in feedback_events) / len(feedback_events) if feedback_events else 0

        # Knowledge transfer value (estimated $50/attendee/hour average industry value)
        avg_event_hours = 2  # Assumed average
        knowledge_transfer_value = total_attendees * avg_event_hours * 50

        return {
            "period": year if year else "All Time",
            "summary": {
                "total_events": len(events),
                "total_attendees": total_attendees,
                "unique_partners_engaged": len(unique_partners),
                "average_event_size": round(total_attendees / len(events), 1) if events else 0
            },
            "by_event_type": by_type,
            "topics_covered": dict(sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)[:10]),
            "partner_organizations": unique_partners,
            "quality_metrics": {
                "average_feedback_score": round(avg_feedback, 2),
                "feedback_scale": "1-5",
                "events_with_feedback": len(feedback_events)
            },
            "impact_valuation": {
                "estimated_knowledge_transfer_value": round(knowledge_transfer_value, 0),
                "methodology": "Industry standard $50/attendee-hour"
            },
            "grant_metrics": {
                "people_reached": total_attendees,
                "events_hosted": len(events),
                "partnerships_leveraged": len(unique_partners),
                "educational_value": round(knowledge_transfer_value, 0)
            }
        }

    # =========================================================================
    # PARTNERSHIPS
    # =========================================================================

    def add_partnership(self, partnership: Partnership) -> Dict:
        """Add community partnership"""
        self.partnerships.append(partnership)

        return {
            "success": True,
            "partnership_id": partnership.partnership_id,
            "partner": partnership.partner_name,
            "type": partnership.partner_type.value,
            "message": "Partnership recorded"
        }

    def get_partnership_summary(self) -> Dict:
        """Get partnership summary"""

        active = [p for p in self.partnerships if p.active]

        if not self.partnerships:
            return {
                "total_partnerships": 0,
                "message": "No partnerships recorded"
            }

        by_type = {}
        for p in active:
            pt = p.partner_type.value
            if pt not in by_type:
                by_type[pt] = []
            by_type[pt].append(p.partner_name)

        total_value_contributed = sum(p.value_contributed for p in active)
        total_value_received = sum(p.value_received for p in active)

        return {
            "active_partnerships": len(active),
            "total_partnerships": len(self.partnerships),
            "by_partner_type": {k: {"count": len(v), "partners": v} for k, v in by_type.items()},
            "value_exchange": {
                "value_contributed_to_partners": round(total_value_contributed, 0),
                "value_received_from_partners": round(total_value_received, 0),
                "net_partnership_value": round(total_value_received - total_value_contributed, 0)
            },
            "partnership_activities": list(set(
                activity
                for p in active
                for activity in p.activities
            )),
            "grant_metrics": {
                "active_partnerships": len(active),
                "partnership_types": len(by_type),
                "leveraged_resources": round(total_value_received, 0)
            }
        }

    # =========================================================================
    # BEGINNING FARMER SUPPORT
    # =========================================================================

    def record_beginning_farmer_support(self, support: BeginningFarmerSupport) -> Dict:
        """Record support provided to beginning farmer"""
        self.beginning_farmer_support.append(support)

        return {
            "success": True,
            "support_id": support.support_id,
            "farmer": support.farmer_name,
            "type": support.support_type,
            "hours": support.hours_provided,
            "message": "Beginning farmer support recorded"
        }

    def get_beginning_farmer_impact(self) -> Dict:
        """Get beginning farmer support impact"""

        if not self.beginning_farmer_support:
            return {
                "farmers_supported": 0,
                "message": "No beginning farmer support recorded"
            }

        total_hours = sum(s.hours_provided for s in self.beginning_farmer_support)
        unique_farmers = len(set(s.farmer_name for s in self.beginning_farmer_support))

        by_type = {}
        for s in self.beginning_farmer_support:
            if s.support_type not in by_type:
                by_type[s.support_type] = {"farmers": 0, "hours": 0}
            by_type[s.support_type]["farmers"] += 1
            by_type[s.support_type]["hours"] += s.hours_provided

        # Topics covered
        all_topics = []
        for s in self.beginning_farmer_support:
            all_topics.extend(s.topics_covered)

        # Value calculation (mentoring valued at $75/hour industry standard)
        mentoring_value = total_hours * 75

        return {
            "summary": {
                "unique_farmers_supported": unique_farmers,
                "total_support_hours": round(total_hours, 1),
                "support_sessions": len(self.beginning_farmer_support)
            },
            "by_support_type": by_type,
            "topics_covered": list(set(all_topics)),
            "impact_valuation": {
                "estimated_mentoring_value": round(mentoring_value, 0),
                "value_per_farmer": round(mentoring_value / unique_farmers, 0) if unique_farmers > 0 else 0
            },
            "outcomes": [s.outcomes for s in self.beginning_farmer_support if s.outcomes],
            "grant_metrics": {
                "beginning_farmers_mentored": unique_farmers,
                "mentoring_hours_provided": round(total_hours, 1),
                "estimated_value_provided": round(mentoring_value, 0)
            }
        }

    # =========================================================================
    # COMPREHENSIVE IMPACT ASSESSMENT
    # =========================================================================

    def calculate_comprehensive_impact(
        self,
        annual_revenue: float,
        year: Optional[int] = None
    ) -> Dict:
        """
        Calculate comprehensive community and economic impact.
        Essential for grant applications.
        """

        employment = self.calculate_employment_impact()
        economic = self.calculate_economic_multiplier_impact(annual_revenue)
        local_food = self.calculate_local_food_impact(year)
        outreach = self.calculate_outreach_impact(year)
        partnerships = self.get_partnership_summary()
        beginning_farmer = self.get_beginning_farmer_impact()

        # Aggregate impact scores
        impact_scores = {
            "economic": min(100, (economic.get("regional_impacts", {}).get("total_economic_output", 0) / annual_revenue - 1) * 100) if annual_revenue > 0 else 0,
            "employment": min(100, employment.get("employment_summary", {}).get("full_time_equivalent", 0) * 20),
            "local_food": min(100, local_food.get("local_economy", {}).get("retention_rate", 0)),
            "education": min(100, outreach.get("summary", {}).get("total_attendees", 0) / 10),
            "partnerships": min(100, partnerships.get("active_partnerships", 0) * 20),
            "beginning_farmer": min(100, beginning_farmer.get("summary", {}).get("unique_farmers_supported", 0) * 25)
        }

        overall_impact_score = sum(impact_scores.values()) / len(impact_scores)

        return {
            "assessment_date": datetime.now().isoformat(),
            "year": year if year else "Current",
            "annual_revenue": round(annual_revenue, 0),
            "impact_categories": {
                "economic_impact": {
                    "score": round(impact_scores["economic"], 0),
                    "highlights": [
                        f"Total regional economic output: ${economic.get('regional_impacts', {}).get('total_economic_output', 0):,}",
                        f"Jobs supported: {economic.get('regional_impacts', {}).get('jobs_supported_region', 0):.1f}",
                        f"Labor income generated: ${economic.get('regional_impacts', {}).get('labor_income_generated', 0):,}"
                    ]
                },
                "employment_impact": {
                    "score": round(impact_scores["employment"], 0),
                    "highlights": [
                        f"FTE employees: {employment.get('employment_summary', {}).get('full_time_equivalent', 0):.1f}",
                        f"Total wages: ${employment.get('compensation', {}).get('total_annual_wages', 0):,}",
                        f"Local hire rate: {employment.get('employment_summary', {}).get('local_hire_percent', 0):.0f}%"
                    ]
                },
                "local_food_impact": {
                    "score": round(impact_scores["local_food"], 0),
                    "highlights": [
                        f"Local sales value: ${local_food.get('sales_summary', {}).get('total_value', 0):,}",
                        f"Local dollar retention: {local_food.get('local_economy', {}).get('retention_rate', 0):.0f}%",
                        f"Food miles saved: {local_food.get('food_miles', {}).get('total_miles_saved', 0):,}"
                    ]
                },
                "education_impact": {
                    "score": round(impact_scores["education"], 0),
                    "highlights": [
                        f"People reached: {outreach.get('summary', {}).get('total_attendees', 0):,}",
                        f"Events hosted: {outreach.get('summary', {}).get('total_events', 0)}",
                        f"Educational value: ${outreach.get('impact_valuation', {}).get('estimated_knowledge_transfer_value', 0):,}"
                    ]
                },
                "partnership_impact": {
                    "score": round(impact_scores["partnerships"], 0),
                    "highlights": [
                        f"Active partnerships: {partnerships.get('active_partnerships', 0)}",
                        f"Resources leveraged: ${partnerships.get('value_exchange', {}).get('value_received_from_partners', 0):,}"
                    ]
                },
                "beginning_farmer_impact": {
                    "score": round(impact_scores["beginning_farmer"], 0),
                    "highlights": [
                        f"Beginning farmers supported: {beginning_farmer.get('summary', {}).get('unique_farmers_supported', 0)}",
                        f"Mentoring hours: {beginning_farmer.get('summary', {}).get('total_support_hours', 0):.0f}",
                        f"Estimated value: ${beginning_farmer.get('impact_valuation', {}).get('estimated_mentoring_value', 0):,}"
                    ]
                }
            },
            "overall_impact_score": round(overall_impact_score, 0),
            "impact_grade": (
                "A" if overall_impact_score >= 80 else
                "B" if overall_impact_score >= 60 else
                "C" if overall_impact_score >= 40 else
                "D" if overall_impact_score >= 20 else "F"
            ),
            "summary_statistics": {
                "total_economic_output": economic.get("regional_impacts", {}).get("total_economic_output", 0),
                "jobs_supported": economic.get("regional_impacts", {}).get("jobs_supported_region", 0),
                "people_educated": outreach.get("summary", {}).get("total_attendees", 0),
                "local_food_sales": local_food.get("sales_summary", {}).get("total_value", 0),
                "beginning_farmers_helped": beginning_farmer.get("summary", {}).get("unique_farmers_supported", 0),
                "partnerships_active": partnerships.get("active_partnerships", 0)
            }
        }

    # =========================================================================
    # GRANT REPORTING
    # =========================================================================

    def generate_community_impact_grant_report(
        self,
        annual_revenue: float,
        grant_program: str,
        year: Optional[int] = None
    ) -> Dict:
        """Generate comprehensive community impact report for grants"""

        comprehensive = self.calculate_comprehensive_impact(annual_revenue, year)

        return {
            "report_title": "Community & Economic Impact Report",
            "grant_program": grant_program,
            "generated_date": datetime.now().isoformat(),
            "executive_summary": {
                "overall_impact_score": comprehensive.get("overall_impact_score", 0),
                "impact_grade": comprehensive.get("impact_grade", "N/A"),
                "total_economic_output": comprehensive.get("summary_statistics", {}).get("total_economic_output", 0),
                "jobs_supported": comprehensive.get("summary_statistics", {}).get("jobs_supported", 0),
                "people_reached": comprehensive.get("summary_statistics", {}).get("people_educated", 0)
            },
            "detailed_impacts": comprehensive.get("impact_categories", {}),
            "key_metrics_for_grant": {
                "economic": {
                    "regional_economic_multiplier": ECONOMIC_MULTIPLIERS["crop_production"]["output"],
                    "jobs_per_million_revenue": ECONOMIC_MULTIPLIERS["crop_production"]["employment"],
                    "total_regional_impact": comprehensive.get("summary_statistics", {}).get("total_economic_output", 0)
                },
                "local_food": {
                    "local_sales_value": comprehensive.get("summary_statistics", {}).get("local_food_sales", 0),
                    "food_dollar_retention_advantage": "50% more than conventional"
                },
                "education": {
                    "total_people_reached": comprehensive.get("summary_statistics", {}).get("people_educated", 0),
                    "educational_value_delivered": self.calculate_outreach_impact(year).get("impact_valuation", {}).get("estimated_knowledge_transfer_value", 0)
                },
                "beginning_farmers": {
                    "farmers_mentored": comprehensive.get("summary_statistics", {}).get("beginning_farmers_helped", 0),
                    "mentoring_value": self.get_beginning_farmer_impact().get("impact_valuation", {}).get("estimated_mentoring_value", 0)
                }
            },
            "grant_compliance_documentation": {
                "employment_records": len(self.employees) > 0,
                "local_sales_tracked": len(self.local_sales) > 0,
                "outreach_documented": len(self.outreach_events) > 0,
                "partnerships_active": len([p for p in self.partnerships if p.active]) > 0,
                "beginning_farmer_support": len(self.beginning_farmer_support) > 0
            },
            "improvement_recommendations": self._get_impact_recommendations(comprehensive)
        }

    def _get_impact_recommendations(self, comprehensive: Dict) -> List[str]:
        """Generate recommendations for improving community impact"""
        recommendations = []

        categories = comprehensive.get("impact_categories", {})

        for category, data in categories.items():
            score = data.get("score", 0)
            if score < 50:
                if category == "local_food_impact":
                    recommendations.append("Increase direct-to-consumer and local market sales")
                elif category == "education_impact":
                    recommendations.append("Host field days or workshops to share knowledge")
                elif category == "partnership_impact":
                    recommendations.append("Develop partnerships with extension, universities, or producer groups")
                elif category == "beginning_farmer_impact":
                    recommendations.append("Consider mentoring beginning farmers in your area")

        if not recommendations:
            recommendations.append("Strong community impact - document for grant applications")

        return recommendations[:4]


# Create singleton instance
community_impact_service = CommunityImpactService()
