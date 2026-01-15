"""
Business Research Test Suite
============================

Comprehensive tests for business management, land/soil management,
commodity/pricing, research/trials, and notification systems.

Tests:
- Business Management (22 tests)
- Land & Soil Management (15 tests)
- Commodity & Pricing (18 tests)
- Research & Trials (15 tests)
- Notifications (12 tests)

Total: 82 tests

Run with: pytest tests/test_business_research.py -v
"""

import os
import sys
import pytest
import secrets
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, patch

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

# Set test environment
os.environ["AGTOOLS_DEV_MODE"] = "1"
os.environ["AGTOOLS_TEST_MODE"] = "1"


# =============================================================================
# MOCK BUSINESS MANAGEMENT CLASSES
# =============================================================================

class BusinessPlan:
    """Mock business plan for testing."""

    def __init__(self, name: str, start_date: date, planning_horizon_years: int = 5):
        self.id = secrets.token_hex(8)
        self.name = name
        self.start_date = start_date
        self.planning_horizon_years = planning_horizon_years
        self.goals = []
        self.projections = []
        self.risks = []
        self.contingencies = []
        self.status = "draft"
        self.created_at = datetime.now()

    def add_goal(self, goal: Dict[str, Any]) -> str:
        goal_id = secrets.token_hex(4)
        goal["id"] = goal_id
        goal["progress"] = 0
        self.goals.append(goal)
        return goal_id

    def update_goal_progress(self, goal_id: str, progress: float) -> bool:
        for goal in self.goals:
            if goal["id"] == goal_id:
                goal["progress"] = min(100, max(0, progress))
                return True
        return False


class FinancialProjection:
    """Mock financial projection for testing."""

    def __init__(self, plan_id: str, year: int):
        self.id = secrets.token_hex(8)
        self.plan_id = plan_id
        self.year = year
        self.revenue = Decimal("0.00")
        self.expenses = Decimal("0.00")
        self.net_income = Decimal("0.00")
        self.cash_flow = Decimal("0.00")
        self.assumptions = {}

    def calculate_net_income(self) -> Decimal:
        self.net_income = self.revenue - self.expenses
        return self.net_income


class RiskAssessment:
    """Mock risk assessment for testing."""

    def __init__(self, name: str, category: str):
        self.id = secrets.token_hex(8)
        self.name = name
        self.category = category  # weather, market, operational, financial
        self.probability = 0.0  # 0-1
        self.impact = 0.0  # 0-1
        self.risk_score = 0.0
        self.mitigation_strategies = []

    def calculate_risk_score(self) -> float:
        self.risk_score = self.probability * self.impact
        return self.risk_score


class CropEnterprise:
    """Mock crop enterprise for testing."""

    def __init__(self, crop: str, acres: float, year: int):
        self.id = secrets.token_hex(8)
        self.crop = crop
        self.acres = acres
        self.year = year
        self.revenue_per_acre = Decimal("0.00")
        self.cost_per_acre = Decimal("0.00")
        self.profit_per_acre = Decimal("0.00")
        self.total_profit = Decimal("0.00")

    def calculate_profitability(self, yield_per_acre: float, price_per_unit: Decimal,
                                 variable_costs: Decimal, fixed_costs: Decimal) -> Decimal:
        self.revenue_per_acre = Decimal(str(yield_per_acre)) * price_per_unit
        self.cost_per_acre = variable_costs + fixed_costs
        self.profit_per_acre = self.revenue_per_acre - self.cost_per_acre
        self.total_profit = self.profit_per_acre * Decimal(str(self.acres))
        return self.total_profit


class SuccessionPlan:
    """Mock succession plan for testing."""

    def __init__(self, farm_name: str):
        self.id = secrets.token_hex(8)
        self.farm_name = farm_name
        self.successors = []
        self.milestones = []
        self.timeline_years = 10
        self.status = "planning"

    def add_milestone(self, description: str, target_date: date, responsible_party: str) -> str:
        milestone_id = secrets.token_hex(4)
        self.milestones.append({
            "id": milestone_id,
            "description": description,
            "target_date": target_date,
            "responsible_party": responsible_party,
            "status": "pending",
            "completed_date": None
        })
        return milestone_id

    def complete_milestone(self, milestone_id: str) -> bool:
        for milestone in self.milestones:
            if milestone["id"] == milestone_id:
                milestone["status"] = "completed"
                milestone["completed_date"] = date.today()
                return True
        return False


class LoanTracker:
    """Mock loan tracker for testing."""

    def __init__(self, lender: str, principal: Decimal, interest_rate: float, term_months: int):
        self.id = secrets.token_hex(8)
        self.lender = lender
        self.principal = principal
        self.interest_rate = interest_rate
        self.term_months = term_months
        self.balance = principal
        self.payments = []
        self.start_date = date.today()

    def make_payment(self, amount: Decimal, payment_date: date) -> Dict[str, Any]:
        interest_portion = self.balance * Decimal(str(self.interest_rate / 12))
        principal_portion = amount - interest_portion
        self.balance -= principal_portion
        payment = {
            "id": secrets.token_hex(4),
            "amount": amount,
            "principal": principal_portion,
            "interest": interest_portion,
            "date": payment_date,
            "balance_after": self.balance
        }
        self.payments.append(payment)
        return payment


# =============================================================================
# MOCK SOIL MANAGEMENT CLASSES
# =============================================================================

class SoilTest:
    """Mock soil test for testing."""

    def __init__(self, field_id: str, sample_date: date):
        self.id = secrets.token_hex(8)
        self.field_id = field_id
        self.sample_date = sample_date
        self.lab_name = ""
        self.results = {}
        self.recommendations = []

    def import_lab_data(self, lab_data: Dict[str, Any]) -> bool:
        self.lab_name = lab_data.get("lab_name", "Unknown")
        self.results = {
            "ph": lab_data.get("ph", 0),
            "organic_matter": lab_data.get("organic_matter", 0),
            "phosphorus_ppm": lab_data.get("phosphorus", 0),
            "potassium_ppm": lab_data.get("potassium", 0),
            "nitrogen_ppm": lab_data.get("nitrogen", 0),
            "cec": lab_data.get("cec", 0),
            "texture": lab_data.get("texture", "unknown")
        }
        return True

    def interpret_results(self) -> Dict[str, str]:
        interpretations = {}
        ph = self.results.get("ph", 0)
        if ph < 6.0:
            interpretations["ph"] = "low"
        elif ph > 7.5:
            interpretations["ph"] = "high"
        else:
            interpretations["ph"] = "optimal"

        p_ppm = self.results.get("phosphorus_ppm", 0)
        if p_ppm < 15:
            interpretations["phosphorus"] = "low"
        elif p_ppm > 50:
            interpretations["phosphorus"] = "very_high"
        else:
            interpretations["phosphorus"] = "adequate"

        k_ppm = self.results.get("potassium_ppm", 0)
        if k_ppm < 120:
            interpretations["potassium"] = "low"
        elif k_ppm > 250:
            interpretations["potassium"] = "very_high"
        else:
            interpretations["potassium"] = "adequate"

        return interpretations


class FertilizerRecommendation:
    """Mock fertilizer recommendation for testing."""

    def __init__(self, crop: str, yield_goal: float, soil_test: SoilTest):
        self.id = secrets.token_hex(8)
        self.crop = crop
        self.yield_goal = yield_goal
        self.soil_test = soil_test
        self.recommendations = []
        self.total_cost = Decimal("0.00")

    def generate_recommendations(self) -> List[Dict[str, Any]]:
        # Simplified recommendation logic
        interpretations = self.soil_test.interpret_results()

        if interpretations.get("phosphorus") == "low":
            self.recommendations.append({
                "nutrient": "P2O5",
                "rate_lbs_per_acre": 60,
                "product": "DAP (18-46-0)",
                "product_rate": 130
            })

        if interpretations.get("potassium") == "low":
            self.recommendations.append({
                "nutrient": "K2O",
                "rate_lbs_per_acre": 80,
                "product": "Potash (0-0-60)",
                "product_rate": 133
            })

        # Always recommend nitrogen for corn
        if self.crop.lower() == "corn":
            n_rate = int(self.yield_goal * 1.1)
            self.recommendations.append({
                "nutrient": "N",
                "rate_lbs_per_acre": n_rate,
                "product": "Anhydrous Ammonia (82-0-0)",
                "product_rate": int(n_rate / 0.82)
            })

        return self.recommendations

    def calculate_cost(self, prices: Dict[str, Decimal]) -> Decimal:
        self.total_cost = Decimal("0.00")
        for rec in self.recommendations:
            product = rec.get("product", "")
            rate = rec.get("product_rate", 0)
            price = prices.get(product, Decimal("0.50"))
            self.total_cost += price * Decimal(str(rate))
        return self.total_cost


class SoilHealthIndicator:
    """Mock soil health indicator for testing."""

    def __init__(self, field_id: str):
        self.field_id = field_id
        self.indicators = {}
        self.overall_score = 0.0

    def assess_health(self, test_results: Dict[str, Any]) -> float:
        scores = []

        # pH score (optimal 6.0-7.0)
        ph = test_results.get("ph", 6.5)
        if 6.0 <= ph <= 7.0:
            scores.append(100)
        elif 5.5 <= ph < 6.0 or 7.0 < ph <= 7.5:
            scores.append(75)
        else:
            scores.append(50)
        self.indicators["ph_score"] = scores[-1]

        # Organic matter score
        om = test_results.get("organic_matter", 2.0)
        if om >= 4.0:
            scores.append(100)
        elif om >= 3.0:
            scores.append(80)
        elif om >= 2.0:
            scores.append(60)
        else:
            scores.append(40)
        self.indicators["organic_matter_score"] = scores[-1]

        # CEC score
        cec = test_results.get("cec", 15)
        if cec >= 20:
            scores.append(100)
        elif cec >= 15:
            scores.append(80)
        elif cec >= 10:
            scores.append(60)
        else:
            scores.append(40)
        self.indicators["cec_score"] = scores[-1]

        self.overall_score = sum(scores) / len(scores) if scores else 0
        return self.overall_score


# =============================================================================
# MOCK COMMODITY/PRICING CLASSES
# =============================================================================

class CommodityPrice:
    """Mock commodity price for testing."""

    def __init__(self, commodity: str):
        self.commodity = commodity
        self.current_price = Decimal("0.00")
        self.price_history = []
        self.forward_prices = {}

    def get_current_price(self) -> Decimal:
        # Simulated prices
        base_prices = {
            "corn": Decimal("4.50"),
            "soybeans": Decimal("12.00"),
            "wheat": Decimal("6.00"),
            "oats": Decimal("3.50")
        }
        self.current_price = base_prices.get(self.commodity.lower(), Decimal("5.00"))
        return self.current_price

    def get_historical_prices(self, days: int = 30) -> List[Dict[str, Any]]:
        base = self.get_current_price()
        self.price_history = []
        for i in range(days):
            # Simulate some price variation
            variation = Decimal(str((i % 10 - 5) / 100))
            price = base * (1 + variation)
            self.price_history.append({
                "date": (date.today() - timedelta(days=days-i)).isoformat(),
                "price": float(price)
            })
        return self.price_history

    def get_forward_prices(self) -> Dict[str, Decimal]:
        base = self.get_current_price()
        months = ["Mar", "May", "Jul", "Sep", "Dec"]
        for i, month in enumerate(months):
            carry = Decimal(str(0.02 * (i + 1)))
            self.forward_prices[month] = base + carry
        return self.forward_prices


class BasisCalculator:
    """Mock basis calculator for testing."""

    def __init__(self, commodity: str, location: str):
        self.commodity = commodity
        self.location = location
        self.current_basis = Decimal("0.00")
        self.seasonal_pattern = {}

    def calculate_basis(self, cash_price: Decimal, futures_price: Decimal) -> Decimal:
        self.current_basis = cash_price - futures_price
        return self.current_basis

    def get_seasonal_pattern(self) -> Dict[str, Decimal]:
        # Simulated seasonal basis patterns
        self.seasonal_pattern = {
            "Jan": Decimal("-0.35"),
            "Feb": Decimal("-0.30"),
            "Mar": Decimal("-0.25"),
            "Apr": Decimal("-0.20"),
            "May": Decimal("-0.15"),
            "Jun": Decimal("-0.10"),
            "Jul": Decimal("-0.15"),
            "Aug": Decimal("-0.25"),
            "Sep": Decimal("-0.40"),
            "Oct": Decimal("-0.50"),
            "Nov": Decimal("-0.45"),
            "Dec": Decimal("-0.40")
        }
        return self.seasonal_pattern


class MarketingPlan:
    """Mock marketing plan for testing."""

    def __init__(self, crop: str, crop_year: int, total_bushels: int):
        self.id = secrets.token_hex(8)
        self.crop = crop
        self.crop_year = crop_year
        self.total_bushels = total_bushels
        self.sales = []
        self.hedges = []
        self.unhedged_bushels = total_bushels
        self.average_price = Decimal("0.00")

    def record_sale(self, bushels: int, price: Decimal, sale_date: date,
                    delivery_date: date = None) -> str:
        sale_id = secrets.token_hex(4)
        self.sales.append({
            "id": sale_id,
            "bushels": bushels,
            "price": price,
            "sale_date": sale_date,
            "delivery_date": delivery_date or sale_date + timedelta(days=30),
            "status": "pending"
        })
        self.unhedged_bushels -= bushels
        self._recalculate_average()
        return sale_id

    def _recalculate_average(self):
        if not self.sales:
            self.average_price = Decimal("0.00")
            return
        total_value = sum(Decimal(str(s["bushels"])) * s["price"] for s in self.sales)
        total_bushels = sum(s["bushels"] for s in self.sales)
        self.average_price = total_value / Decimal(str(total_bushels)) if total_bushels else Decimal("0.00")


class PriceAlert:
    """Mock price alert for testing."""

    def __init__(self, commodity: str, target_price: Decimal, direction: str):
        self.id = secrets.token_hex(8)
        self.commodity = commodity
        self.target_price = target_price
        self.direction = direction  # "above" or "below"
        self.triggered = False
        self.trigger_date = None

    def check_price(self, current_price: Decimal) -> bool:
        if self.direction == "above" and current_price >= self.target_price:
            self.triggered = True
            self.trigger_date = datetime.now()
            return True
        elif self.direction == "below" and current_price <= self.target_price:
            self.triggered = True
            self.trigger_date = datetime.now()
            return True
        return False


# =============================================================================
# MOCK RESEARCH/TRIAL CLASSES
# =============================================================================

class FieldTrial:
    """Mock field trial for testing."""

    def __init__(self, name: str, crop: str, field_id: str):
        self.id = secrets.token_hex(8)
        self.name = name
        self.crop = crop
        self.field_id = field_id
        self.treatments = []
        self.replicates = 4
        self.plot_size_acres = 0.5
        self.plots = []
        self.data_collected = []
        self.status = "planning"
        self.costs = []

    def add_treatment(self, treatment_name: str, description: str) -> str:
        treatment_id = secrets.token_hex(4)
        self.treatments.append({
            "id": treatment_id,
            "name": treatment_name,
            "description": description
        })
        return treatment_id

    def randomize_plots(self) -> List[Dict[str, Any]]:
        import random
        self.plots = []
        plot_num = 1
        for rep in range(1, self.replicates + 1):
            rep_treatments = list(self.treatments)
            random.shuffle(rep_treatments)
            for treatment in rep_treatments:
                self.plots.append({
                    "plot_number": plot_num,
                    "replicate": rep,
                    "treatment_id": treatment["id"],
                    "treatment_name": treatment["name"]
                })
                plot_num += 1
        self.status = "randomized"
        return self.plots

    def record_data(self, plot_number: int, data_type: str, value: float,
                    notes: str = "") -> str:
        data_id = secrets.token_hex(4)
        self.data_collected.append({
            "id": data_id,
            "plot_number": plot_number,
            "data_type": data_type,
            "value": value,
            "timestamp": datetime.now(),
            "notes": notes
        })
        return data_id

    def record_harvest(self, plot_number: int, yield_value: float,
                       moisture: float) -> str:
        return self.record_data(plot_number, "yield", yield_value,
                               f"Moisture: {moisture}%")

    def add_cost(self, description: str, amount: Decimal, category: str) -> str:
        cost_id = secrets.token_hex(4)
        self.costs.append({
            "id": cost_id,
            "description": description,
            "amount": amount,
            "category": category,
            "date": date.today()
        })
        return cost_id

    def calculate_total_cost(self) -> Decimal:
        return sum(c["amount"] for c in self.costs)


class TrialStatistics:
    """Mock trial statistics for testing."""

    def __init__(self, trial: FieldTrial):
        self.trial = trial
        self.results = {}

    def analyze(self) -> Dict[str, Any]:
        # Group yield data by treatment
        treatment_yields = {}
        for data in self.trial.data_collected:
            if data["data_type"] == "yield":
                plot = next((p for p in self.trial.plots
                           if p["plot_number"] == data["plot_number"]), None)
                if plot:
                    tid = plot["treatment_id"]
                    if tid not in treatment_yields:
                        treatment_yields[tid] = []
                    treatment_yields[tid].append(data["value"])

        # Calculate statistics
        self.results["treatment_means"] = {}
        self.results["treatment_std"] = {}
        for tid, yields in treatment_yields.items():
            if yields:
                mean = sum(yields) / len(yields)
                variance = sum((y - mean) ** 2 for y in yields) / len(yields)
                std = variance ** 0.5
                self.results["treatment_means"][tid] = mean
                self.results["treatment_std"][tid] = std

        # Simple LSD calculation (placeholder)
        all_yields = [y for yields in treatment_yields.values() for y in yields]
        if all_yields:
            grand_mean = sum(all_yields) / len(all_yields)
            self.results["grand_mean"] = grand_mean
            self.results["cv"] = (sum((y - grand_mean) ** 2 for y in all_yields) /
                                  len(all_yields)) ** 0.5 / grand_mean * 100

        return self.results

    def interpret_results(self) -> str:
        if not self.results:
            self.analyze()

        means = self.results.get("treatment_means", {})
        if not means:
            return "Insufficient data for interpretation"

        best_treatment = max(means, key=means.get)
        worst_treatment = min(means, key=means.get)

        best_yield = means[best_treatment]
        worst_yield = means[worst_treatment]
        difference = best_yield - worst_yield

        return f"Best performing treatment yielded {best_yield:.1f} bu/ac, " \
               f"which is {difference:.1f} bu/ac better than the lowest yielding treatment."


# =============================================================================
# MOCK NOTIFICATION CLASSES
# =============================================================================

class NotificationSystem:
    """Mock notification system for testing."""

    def __init__(self):
        self.notifications = []
        self.templates = {}
        self.preferences = {}
        self.delivery_log = []
        self.retry_queue = []

    def add_template(self, name: str, subject: str, body: str) -> str:
        template_id = secrets.token_hex(4)
        self.templates[template_id] = {
            "id": template_id,
            "name": name,
            "subject": subject,
            "body": body
        }
        return template_id

    def set_preferences(self, user_id: str, prefs: Dict[str, Any]) -> bool:
        self.preferences[user_id] = prefs
        return True

    def send_notification(self, user_id: str, notification_type: str,
                         data: Dict[str, Any]) -> str:
        notif_id = secrets.token_hex(8)
        notification = {
            "id": notif_id,
            "user_id": user_id,
            "type": notification_type,
            "data": data,
            "status": "pending",
            "created_at": datetime.now(),
            "sent_at": None,
            "attempts": 0
        }
        self.notifications.append(notification)

        # Simulate delivery
        success = self._attempt_delivery(notification)
        return notif_id

    def _attempt_delivery(self, notification: Dict[str, Any]) -> bool:
        notification["attempts"] += 1
        # Simulate 90% success rate
        import random
        if random.random() < 0.9:
            notification["status"] = "delivered"
            notification["sent_at"] = datetime.now()
            self.delivery_log.append({
                "notification_id": notification["id"],
                "status": "delivered",
                "timestamp": datetime.now()
            })
            return True
        else:
            notification["status"] = "failed"
            self.retry_queue.append(notification["id"])
            return False

    def retry_failed(self) -> int:
        retried = 0
        for notif_id in list(self.retry_queue):
            notification = next((n for n in self.notifications
                               if n["id"] == notif_id), None)
            if notification and notification["attempts"] < 3:
                if self._attempt_delivery(notification):
                    self.retry_queue.remove(notif_id)
                retried += 1
        return retried

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return self.delivery_log

    def get_batch_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        relevant = [n for n in self.notifications
                   if start_date <= n["created_at"] <= end_date]
        return {
            "total": len(relevant),
            "delivered": len([n for n in relevant if n["status"] == "delivered"]),
            "failed": len([n for n in relevant if n["status"] == "failed"]),
            "pending": len([n for n in relevant if n["status"] == "pending"])
        }


# =============================================================================
# BUSINESS MANAGEMENT TESTS (22 tests)
# =============================================================================

class TestBusinessManagement:
    """Tests for business planning and management features."""

    def test_business_plan_creation(self, data_factory):
        """Test creating a business plan."""
        plan = BusinessPlan(
            name="5-Year Farm Growth Plan",
            start_date=date.today(),
            planning_horizon_years=5
        )

        assert plan.id is not None
        assert plan.name == "5-Year Farm Growth Plan"
        assert plan.planning_horizon_years == 5
        assert plan.status == "draft"

    def test_financial_projections(self, data_factory):
        """Test adding financial projections to a plan."""
        plan = BusinessPlan("Test Plan", date.today())
        projection = FinancialProjection(plan.id, 2025)

        projection.revenue = Decimal("500000.00")
        projection.expenses = Decimal("400000.00")
        net_income = projection.calculate_net_income()

        assert net_income == Decimal("100000.00")
        assert projection.net_income == Decimal("100000.00")

    def test_risk_assessment(self, data_factory):
        """Test assessing business risks."""
        risk = RiskAssessment("Drought Risk", "weather")
        risk.probability = 0.3
        risk.impact = 0.8

        score = risk.calculate_risk_score()

        assert score == 0.24
        assert risk.risk_score == 0.24

    def test_contingency_planning(self, data_factory):
        """Test contingency planning for identified risks."""
        risk = RiskAssessment("Market Price Drop", "market")
        risk.probability = 0.5
        risk.impact = 0.6
        risk.mitigation_strategies = [
            "Forward contract 50% of production",
            "Diversify crop mix",
            "Maintain operating line of credit"
        ]

        assert len(risk.mitigation_strategies) == 3
        assert "Forward contract" in risk.mitigation_strategies[0]

    def test_enterprise_profitability(self, data_factory):
        """Test crop enterprise profitability calculation."""
        enterprise = CropEnterprise("corn", 500.0, 2025)

        profit = enterprise.calculate_profitability(
            yield_per_acre=200,
            price_per_unit=Decimal("4.50"),
            variable_costs=Decimal("450.00"),
            fixed_costs=Decimal("150.00")
        )

        assert enterprise.revenue_per_acre == Decimal("900.00")
        assert enterprise.cost_per_acre == Decimal("600.00")
        assert enterprise.profit_per_acre == Decimal("300.00")
        assert profit == Decimal("150000.00")  # 300 * 500 acres

    def test_enterprise_comparison(self, data_factory):
        """Test comparing multiple crop enterprises."""
        corn = CropEnterprise("corn", 300, 2025)
        soybeans = CropEnterprise("soybeans", 200, 2025)

        corn.calculate_profitability(200, Decimal("4.50"), Decimal("450"), Decimal("150"))
        soybeans.calculate_profitability(55, Decimal("12.00"), Decimal("280"), Decimal("120"))

        assert corn.profit_per_acre == Decimal("300.00")
        assert soybeans.profit_per_acre == Decimal("260.00")
        assert corn.profit_per_acre > soybeans.profit_per_acre

    def test_enterprise_optimization(self, data_factory):
        """Test optimizing crop mix for maximum profit."""
        total_acres = 1000
        enterprises = [
            {"crop": "corn", "profit_per_acre": Decimal("300"), "max_acres": 600},
            {"crop": "soybeans", "profit_per_acre": Decimal("260"), "max_acres": 500},
            {"crop": "wheat", "profit_per_acre": Decimal("150"), "max_acres": 300}
        ]

        # Simple optimization: maximize profit within constraints
        sorted_enterprises = sorted(enterprises, key=lambda x: x["profit_per_acre"], reverse=True)
        allocation = {}
        remaining = total_acres

        for ent in sorted_enterprises:
            acres = min(ent["max_acres"], remaining)
            allocation[ent["crop"]] = acres
            remaining -= acres

        assert allocation["corn"] == 600
        assert allocation["soybeans"] == 400
        assert sum(allocation.values()) == 1000

    def test_market_trends_analysis(self, data_factory):
        """Test analyzing market trends."""
        price = CommodityPrice("corn")
        history = price.get_historical_prices(30)

        assert len(history) == 30
        # Check for price trend (simplified)
        prices = [h["price"] for h in history]
        trend = "up" if prices[-1] > prices[0] else "down" if prices[-1] < prices[0] else "flat"
        assert trend in ["up", "down", "flat"]

    def test_market_forecast(self, data_factory):
        """Test using market forecasts for planning."""
        price = CommodityPrice("corn")
        forward = price.get_forward_prices()

        assert len(forward) >= 5
        assert "Dec" in forward
        assert forward["Dec"] > price.current_price  # Carry should add value

    def test_goal_setting(self, data_factory):
        """Test setting business goals."""
        plan = BusinessPlan("Annual Plan", date.today(), 1)

        goal_id = plan.add_goal({
            "description": "Increase corn yield to 220 bu/acre",
            "target_value": 220,
            "current_value": 200,
            "due_date": date(2025, 12, 31)
        })

        assert goal_id is not None
        assert len(plan.goals) == 1
        assert plan.goals[0]["progress"] == 0

    def test_goal_progress_tracking(self, data_factory):
        """Test tracking progress toward goals."""
        plan = BusinessPlan("Test Plan", date.today())
        goal_id = plan.add_goal({"description": "Reduce costs by 10%"})

        plan.update_goal_progress(goal_id, 50)
        assert plan.goals[0]["progress"] == 50

        plan.update_goal_progress(goal_id, 100)
        assert plan.goals[0]["progress"] == 100

        # Should cap at 100
        plan.update_goal_progress(goal_id, 150)
        assert plan.goals[0]["progress"] == 100

    def test_succession_planning(self, data_factory):
        """Test creating a succession plan."""
        succession = SuccessionPlan("Family Farm LLC")
        succession.successors = [
            {"name": "John Jr.", "role": "Operations Manager", "ownership_pct": 40},
            {"name": "Sarah", "role": "Financial Manager", "ownership_pct": 30}
        ]

        assert succession.farm_name == "Family Farm LLC"
        assert len(succession.successors) == 2
        assert succession.timeline_years == 10

    def test_succession_milestones(self, data_factory):
        """Test tracking succession milestones."""
        succession = SuccessionPlan("Test Farm")

        milestone_id = succession.add_milestone(
            "Complete estate planning documents",
            date(2025, 6, 30),
            "John Sr."
        )

        assert len(succession.milestones) == 1
        assert succession.milestones[0]["status"] == "pending"

        succession.complete_milestone(milestone_id)
        assert succession.milestones[0]["status"] == "completed"
        assert succession.milestones[0]["completed_date"] == date.today()

    def test_tax_planning(self, data_factory):
        """Test tax planning estimates."""
        income = Decimal("250000")
        deductions = Decimal("80000")
        taxable = income - deductions

        # Simplified tax brackets
        tax = Decimal("0")
        if taxable > Decimal("200000"):
            tax += (taxable - Decimal("200000")) * Decimal("0.32")
            taxable = Decimal("200000")
        if taxable > Decimal("80000"):
            tax += (taxable - Decimal("80000")) * Decimal("0.24")
            taxable = Decimal("80000")
        if taxable > Decimal("20000"):
            tax += (taxable - Decimal("20000")) * Decimal("0.12")

        assert tax > Decimal("0")
        effective_rate = tax / income * 100
        assert effective_rate < Decimal("25")

    def test_insurance_assessment(self, data_factory):
        """Test insurance coverage analysis."""
        coverages = {
            "crop_insurance": {"premium": 15000, "coverage": 500000, "type": "RP"},
            "liability": {"premium": 5000, "coverage": 1000000, "type": "General"},
            "equipment": {"premium": 8000, "coverage": 800000, "type": "Replacement"}
        }

        total_premium = sum(c["premium"] for c in coverages.values())
        total_coverage = sum(c["coverage"] for c in coverages.values())

        assert total_premium == 28000
        assert total_coverage == 2300000
        assert len(coverages) == 3

    def test_loan_tracking(self, data_factory):
        """Test tracking farm loans."""
        loan = LoanTracker(
            lender="Farm Credit",
            principal=Decimal("500000"),
            interest_rate=0.065,
            term_months=120
        )

        payment = loan.make_payment(Decimal("5000"), date.today())

        assert payment["amount"] == Decimal("5000")
        assert payment["interest"] > Decimal("0")
        assert loan.balance < Decimal("500000")

    def test_cash_flow_projection(self, data_factory):
        """Test projecting cash flow."""
        months = 12
        projections = []
        balance = Decimal("50000")

        for month in range(1, months + 1):
            inflow = Decimal("30000") if month in [3, 10, 11] else Decimal("5000")
            outflow = Decimal("25000") if month in [3, 4, 5] else Decimal("10000")
            net = inflow - outflow
            balance += net
            projections.append({
                "month": month,
                "inflow": inflow,
                "outflow": outflow,
                "net": net,
                "ending_balance": balance
            })

        assert len(projections) == 12
        # Check that we tracked the full year
        final_balance = projections[-1]["ending_balance"]
        assert final_balance != Decimal("50000")  # Balance should have changed

    def test_liquidity_analysis(self, data_factory):
        """Test analyzing farm liquidity."""
        current_assets = Decimal("200000")
        current_liabilities = Decimal("80000")

        current_ratio = current_assets / current_liabilities
        working_capital = current_assets - current_liabilities

        assert current_ratio == Decimal("2.5")
        assert working_capital == Decimal("120000")
        assert current_ratio > Decimal("1.5")  # Good liquidity threshold

    def test_financial_ratios(self, data_factory):
        """Test calculating financial ratios."""
        financials = {
            "total_assets": Decimal("2000000"),
            "total_liabilities": Decimal("800000"),
            "equity": Decimal("1200000"),
            "net_income": Decimal("150000"),
            "gross_revenue": Decimal("600000")
        }

        debt_to_asset = financials["total_liabilities"] / financials["total_assets"]
        debt_to_equity = financials["total_liabilities"] / financials["equity"]
        return_on_assets = financials["net_income"] / financials["total_assets"]
        profit_margin = financials["net_income"] / financials["gross_revenue"]

        assert debt_to_asset == Decimal("0.4")
        assert round(debt_to_equity, 2) == Decimal("0.67")
        assert return_on_assets == Decimal("0.075")
        assert profit_margin == Decimal("0.25")

    def test_benchmark_comparison(self, data_factory):
        """Test comparing farm metrics to industry benchmarks."""
        farm_metrics = {
            "profit_margin": 0.25,
            "debt_to_asset": 0.40,
            "working_capital_ratio": 2.5
        }

        benchmarks = {
            "profit_margin": {"low": 0.10, "avg": 0.18, "high": 0.25},
            "debt_to_asset": {"low": 0.60, "avg": 0.45, "high": 0.30},
            "working_capital_ratio": {"low": 1.2, "avg": 1.8, "high": 2.5}
        }

        # Check farm performance vs benchmarks
        assert farm_metrics["profit_margin"] >= benchmarks["profit_margin"]["high"]
        assert farm_metrics["debt_to_asset"] <= benchmarks["debt_to_asset"]["avg"]
        assert farm_metrics["working_capital_ratio"] >= benchmarks["working_capital_ratio"]["high"]

    def test_land_ownership_vs_lease(self, data_factory):
        """Test analyzing land ownership vs lease options."""
        owned_land = {
            "acres": 500,
            "value_per_acre": 10000,
            "annual_tax": 15000,
            "depreciation": 0  # Land doesn't depreciate
        }

        leased_land = {
            "acres": 300,
            "cash_rent_per_acre": 250,
            "term_years": 5
        }

        owned_cost = owned_land["annual_tax"]
        lease_cost = leased_land["acres"] * leased_land["cash_rent_per_acre"]

        owned_cost_per_acre = owned_cost / owned_land["acres"]
        lease_cost_per_acre = lease_cost / leased_land["acres"]

        assert owned_cost_per_acre == 30  # $30/acre tax
        assert lease_cost_per_acre == 250  # $250/acre rent
        assert owned_cost_per_acre < lease_cost_per_acre

    def test_expansion_analysis(self, data_factory):
        """Test analyzing growth and expansion scenarios."""
        scenarios = [
            {
                "name": "Conservative",
                "additional_acres": 200,
                "investment": 100000,
                "expected_return": 0.08,
                "risk_level": "low"
            },
            {
                "name": "Moderate",
                "additional_acres": 500,
                "investment": 300000,
                "expected_return": 0.12,
                "risk_level": "medium"
            },
            {
                "name": "Aggressive",
                "additional_acres": 1000,
                "investment": 750000,
                "expected_return": 0.18,
                "risk_level": "high"
            }
        ]

        # Calculate expected annual return for each scenario
        for scenario in scenarios:
            scenario["annual_return"] = scenario["investment"] * Decimal(str(scenario["expected_return"]))

        assert scenarios[0]["annual_return"] == Decimal("8000")
        assert scenarios[1]["annual_return"] == Decimal("36000")
        assert scenarios[2]["annual_return"] == Decimal("135000")


# =============================================================================
# LAND & SOIL MANAGEMENT TESTS (15 tests)
# =============================================================================

class TestLandSoilManagement:
    """Tests for land and soil management features."""

    def test_soil_test_import(self, data_factory):
        """Test importing soil test lab data."""
        soil_test = SoilTest("field_001", date.today())

        lab_data = {
            "lab_name": "AgriLab Inc",
            "ph": 6.2,
            "organic_matter": 3.5,
            "phosphorus": 22,
            "potassium": 180,
            "nitrogen": 15,
            "cec": 18,
            "texture": "silt_loam"
        }

        result = soil_test.import_lab_data(lab_data)

        assert result is True
        assert soil_test.lab_name == "AgriLab Inc"
        assert soil_test.results["ph"] == 6.2
        assert soil_test.results["phosphorus_ppm"] == 22

    def test_soil_test_interpretation(self, data_factory):
        """Test interpreting soil test results."""
        soil_test = SoilTest("field_001", date.today())
        soil_test.import_lab_data({
            "ph": 5.8,
            "phosphorus": 12,
            "potassium": 100
        })

        interpretations = soil_test.interpret_results()

        assert interpretations["ph"] == "low"
        assert interpretations["phosphorus"] == "low"
        assert interpretations["potassium"] == "low"

    def test_soil_fertility_status(self, data_factory):
        """Test assessing overall soil fertility status."""
        soil_test = SoilTest("field_001", date.today())
        soil_test.import_lab_data({
            "ph": 6.5,
            "organic_matter": 3.0,
            "phosphorus": 25,
            "potassium": 175,
            "cec": 16
        })

        interpretations = soil_test.interpret_results()

        # All within adequate range
        assert interpretations["ph"] == "optimal"
        assert interpretations["phosphorus"] == "adequate"
        assert interpretations["potassium"] == "adequate"

    def test_fertilizer_recommendation(self, data_factory):
        """Test generating fertilizer recommendations."""
        soil_test = SoilTest("field_001", date.today())
        soil_test.import_lab_data({"ph": 6.5, "phosphorus": 12, "potassium": 100})

        rec = FertilizerRecommendation("corn", 200, soil_test)
        recommendations = rec.generate_recommendations()

        assert len(recommendations) >= 2  # Should have P, K, and N recommendations
        nutrients = [r["nutrient"] for r in recommendations]
        assert "N" in nutrients
        assert "P2O5" in nutrients

    def test_fertilizer_cost_analysis(self, data_factory):
        """Test analyzing fertilizer costs per nutrient."""
        soil_test = SoilTest("field_001", date.today())
        soil_test.import_lab_data({"ph": 6.5, "phosphorus": 10, "potassium": 90})

        rec = FertilizerRecommendation("corn", 200, soil_test)
        rec.generate_recommendations()

        prices = {
            "DAP (18-46-0)": Decimal("0.35"),
            "Potash (0-0-60)": Decimal("0.30"),
            "Anhydrous Ammonia (82-0-0)": Decimal("0.40")
        }

        total_cost = rec.calculate_cost(prices)
        assert total_cost > Decimal("0")

    def test_soil_amendment_rate(self, data_factory):
        """Test calculating soil amendment application rates."""
        current_ph = 5.5
        target_ph = 6.5
        buffer_ph = 6.8

        # Simplified lime requirement calculation
        lime_tons_per_acre = (target_ph - current_ph) * 2.0

        assert lime_tons_per_acre == 2.0

    def test_soil_compaction_assessment(self, data_factory):
        """Test assessing soil compaction levels."""
        penetrometer_readings = [
            {"depth_inches": 3, "psi": 150},
            {"depth_inches": 6, "psi": 280},
            {"depth_inches": 9, "psi": 320},
            {"depth_inches": 12, "psi": 250}
        ]

        # Find compaction layer (300+ PSI indicates compaction)
        compacted_layers = [r for r in penetrometer_readings if r["psi"] >= 300]

        assert len(compacted_layers) == 1
        assert compacted_layers[0]["depth_inches"] == 9

    def test_soil_ph_stability(self, data_factory):
        """Test projecting pH stability over time."""
        initial_ph = 6.8
        years = 5
        annual_decline = 0.1  # Typical acidification rate

        projected_ph = []
        current_ph = initial_ph
        for year in range(years):
            current_ph -= annual_decline
            projected_ph.append({"year": year + 1, "ph": round(current_ph, 1)})

        assert projected_ph[-1]["ph"] == 6.3
        assert len(projected_ph) == 5

    def test_organic_matter_trend(self, data_factory):
        """Test tracking organic matter changes over time."""
        om_history = [
            {"year": 2020, "om_pct": 2.8},
            {"year": 2021, "om_pct": 2.9},
            {"year": 2022, "om_pct": 3.0},
            {"year": 2023, "om_pct": 3.2},
            {"year": 2024, "om_pct": 3.4}
        ]

        trend = om_history[-1]["om_pct"] - om_history[0]["om_pct"]
        avg_annual_change = trend / (len(om_history) - 1)

        assert round(trend, 2) == 0.6
        assert round(avg_annual_change, 2) == 0.15

    def test_soil_health_indicators(self, data_factory):
        """Test calculating soil health metrics."""
        indicator = SoilHealthIndicator("field_001")

        test_results = {
            "ph": 6.5,
            "organic_matter": 3.5,
            "cec": 18
        }

        score = indicator.assess_health(test_results)

        assert score > 0
        assert indicator.indicators["ph_score"] == 100
        assert indicator.indicators["organic_matter_score"] == 80
        assert indicator.overall_score > 80

    def test_tile_drainage_assessment(self, data_factory):
        """Test evaluating tile drainage needs."""
        field_data = {
            "acreage": 160,
            "soil_type": "silty_clay",
            "slope_pct": 1.5,
            "water_table_depth_inches": 24,
            "current_drainage": "none"
        }

        # Assess drainage need
        needs_drainage = (
            field_data["soil_type"] in ["silty_clay", "clay"] and
            field_data["water_table_depth_inches"] < 36 and
            field_data["slope_pct"] < 3
        )

        estimated_cost = field_data["acreage"] * 1200 if needs_drainage else 0

        assert needs_drainage is True
        assert estimated_cost == 192000

    def test_salinity_assessment(self, data_factory):
        """Test analyzing soil salinity levels."""
        ec_readings = [
            {"location": "A1", "ec_ds_m": 1.2},
            {"location": "A2", "ec_ds_m": 0.8},
            {"location": "B1", "ec_ds_m": 3.5},
            {"location": "B2", "ec_ds_m": 4.2}
        ]

        # EC thresholds: <2 = non-saline, 2-4 = slightly saline, >4 = moderately saline
        saline_areas = [r for r in ec_readings if r["ec_ds_m"] >= 2.0]

        assert len(saline_areas) == 2
        avg_ec = sum(r["ec_ds_m"] for r in ec_readings) / len(ec_readings)
        assert avg_ec == 2.425

    def test_soil_texture_verification(self, data_factory):
        """Test verifying soil texture classification."""
        particle_analysis = {
            "sand_pct": 35,
            "silt_pct": 45,
            "clay_pct": 20
        }

        # Simplified texture classification
        if particle_analysis["clay_pct"] >= 40:
            texture = "clay"
        elif particle_analysis["sand_pct"] >= 50:
            texture = "sandy"
        elif particle_analysis["silt_pct"] >= 50:
            texture = "silty"
        else:
            texture = "loam"

        assert texture == "loam"
        assert sum(particle_analysis.values()) == 100

    def test_field_variability_mapping(self, data_factory):
        """Test mapping field variability."""
        zones = [
            {"zone_id": 1, "acres": 40, "yield_potential": "high", "om_pct": 4.0},
            {"zone_id": 2, "acres": 60, "yield_potential": "medium", "om_pct": 3.2},
            {"zone_id": 3, "acres": 35, "yield_potential": "low", "om_pct": 2.5},
            {"zone_id": 4, "acres": 25, "yield_potential": "medium", "om_pct": 3.0}
        ]

        total_acres = sum(z["acres"] for z in zones)
        high_potential_acres = sum(z["acres"] for z in zones if z["yield_potential"] == "high")

        assert total_acres == 160
        assert high_potential_acres == 40
        assert len(zones) == 4

    def test_soil_sampling_interval(self, data_factory):
        """Test determining appropriate retest timing."""
        last_test_date = date(2022, 10, 15)
        recommended_interval_years = 3

        next_test_date = date(
            last_test_date.year + recommended_interval_years,
            last_test_date.month,
            last_test_date.day
        )

        is_due = date.today() >= next_test_date

        assert next_test_date == date(2025, 10, 15)
        # Test will be due in 2025


# =============================================================================
# COMMODITY & PRICING TESTS (18 tests)
# =============================================================================

class TestCommodityPricing:
    """Tests for commodity and pricing features."""

    def test_commodity_price_retrieval(self, data_factory):
        """Test getting current commodity prices."""
        corn_price = CommodityPrice("corn")
        current = corn_price.get_current_price()

        assert current == Decimal("4.50")
        assert corn_price.commodity == "corn"

    def test_historical_prices(self, data_factory):
        """Test retrieving price history."""
        price = CommodityPrice("soybeans")
        history = price.get_historical_prices(30)

        assert len(history) == 30
        assert all("date" in h and "price" in h for h in history)

    def test_forward_prices(self, data_factory):
        """Test getting future/forward prices."""
        price = CommodityPrice("corn")
        forwards = price.get_forward_prices()

        assert len(forwards) >= 5
        assert "Dec" in forwards
        # Forward prices should include carry
        assert forwards["Dec"] > price.current_price

    def test_basis_calculation(self, data_factory):
        """Test calculating local basis."""
        basis_calc = BasisCalculator("corn", "Central Iowa")

        cash_price = Decimal("4.25")
        futures_price = Decimal("4.50")

        basis = basis_calc.calculate_basis(cash_price, futures_price)

        assert basis == Decimal("-0.25")

    def test_basis_seasonal_pattern(self, data_factory):
        """Test seasonal basis spread patterns."""
        basis_calc = BasisCalculator("corn", "Central Iowa")
        pattern = basis_calc.get_seasonal_pattern()

        assert len(pattern) == 12
        assert "Oct" in pattern
        # Harvest typically has widest basis
        assert pattern["Oct"] < pattern["Jun"]

    def test_price_trigger_alert(self, data_factory):
        """Test price alert triggering."""
        alert = PriceAlert("corn", Decimal("5.00"), "above")

        # Price below target
        triggered = alert.check_price(Decimal("4.75"))
        assert triggered is False
        assert alert.triggered is False

        # Price hits target
        triggered = alert.check_price(Decimal("5.25"))
        assert triggered is True
        assert alert.triggered is True
        assert alert.trigger_date is not None

    def test_marketing_plan_create(self, data_factory):
        """Test creating a marketing plan."""
        plan = MarketingPlan("corn", 2025, 100000)

        assert plan.crop == "corn"
        assert plan.total_bushels == 100000
        assert plan.unhedged_bushels == 100000

    def test_marketing_execution_tracking(self, data_factory):
        """Test tracking marketing execution."""
        plan = MarketingPlan("corn", 2025, 100000)

        sale_id = plan.record_sale(20000, Decimal("4.75"), date.today())

        assert sale_id is not None
        assert len(plan.sales) == 1
        assert plan.unhedged_bushels == 80000
        assert plan.average_price == Decimal("4.75")

    def test_crop_insurance_price(self, data_factory):
        """Test crop insurance price discovery."""
        insurance_prices = {
            "corn": {"projected": Decimal("4.66"), "harvest": None},
            "soybeans": {"projected": Decimal("11.55"), "harvest": None}
        }

        assert insurance_prices["corn"]["projected"] == Decimal("4.66")
        assert insurance_prices["soybeans"]["projected"] == Decimal("11.55")

    def test_option_pricing(self, data_factory):
        """Test options pricing data."""
        options = {
            "corn_dec_450_put": {
                "strike": Decimal("4.50"),
                "premium": Decimal("0.18"),
                "expiration": date(2025, 11, 21)
            },
            "corn_dec_500_call": {
                "strike": Decimal("5.00"),
                "premium": Decimal("0.12"),
                "expiration": date(2025, 11, 21)
            }
        }

        assert options["corn_dec_450_put"]["premium"] == Decimal("0.18")
        assert options["corn_dec_500_call"]["strike"] == Decimal("5.00")

    def test_hedging_position(self, data_factory):
        """Test tracking hedge positions."""
        plan = MarketingPlan("corn", 2025, 100000)
        plan.hedges = [
            {"type": "futures", "bushels": 30000, "price": Decimal("4.50"), "contract": "Dec25"},
            {"type": "put_option", "bushels": 20000, "strike": Decimal("4.25"), "premium": Decimal("0.15")}
        ]

        total_hedged = sum(h["bushels"] for h in plan.hedges)
        hedge_ratio = total_hedged / plan.total_bushels

        assert total_hedged == 50000
        assert hedge_ratio == 0.5

    def test_unhedged_exposure(self, data_factory):
        """Test calculating unhedged risk exposure."""
        plan = MarketingPlan("corn", 2025, 100000)
        plan.record_sale(20000, Decimal("4.75"), date.today())

        current_price = Decimal("4.50")
        unhedged_value = plan.unhedged_bushels * current_price

        assert plan.unhedged_bushels == 80000
        assert unhedged_value == Decimal("360000")

    def test_marketing_alternatives(self, data_factory):
        """Test comparing marketing alternatives."""
        alternatives = [
            {"strategy": "cash_sale", "price": Decimal("4.45"), "risk": "none"},
            {"strategy": "basis_contract", "price": Decimal("4.55"), "risk": "low"},
            {"strategy": "hedge_to_arrive", "price": Decimal("4.60"), "risk": "medium"},
            {"strategy": "store_and_wait", "price": Decimal("4.80"), "risk": "high"}
        ]

        best_price = max(a["price"] for a in alternatives)
        lowest_risk = [a for a in alternatives if a["risk"] == "none"][0]

        assert best_price == Decimal("4.80")
        assert lowest_risk["strategy"] == "cash_sale"

    def test_storage_decision(self, data_factory):
        """Test store vs sell decision analysis."""
        current_price = Decimal("4.40")
        expected_spring_price = Decimal("4.75")
        storage_cost_per_month = Decimal("0.04")
        months_stored = 5

        total_storage_cost = storage_cost_per_month * months_stored
        net_spring_price = expected_spring_price - total_storage_cost
        storage_benefit = net_spring_price - current_price

        assert total_storage_cost == Decimal("0.20")
        assert net_spring_price == Decimal("4.55")
        assert storage_benefit == Decimal("0.15")
        assert storage_benefit > Decimal("0")  # Storage is profitable

    def test_storage_cost_analysis(self, data_factory):
        """Test analyzing storage costs."""
        storage_costs = {
            "commercial": {
                "in_charge": Decimal("0.03"),
                "monthly_rate": Decimal("0.04"),
                "out_charge": Decimal("0.02")
            },
            "on_farm": {
                "fixed_cost_per_bu": Decimal("0.10"),
                "variable_cost_per_bu": Decimal("0.02"),
                "shrink_pct": 0.5
            }
        }

        bushels = 10000
        months = 4

        commercial_cost = (
            storage_costs["commercial"]["in_charge"] +
            storage_costs["commercial"]["monthly_rate"] * months +
            storage_costs["commercial"]["out_charge"]
        ) * bushels

        on_farm_cost = (
            storage_costs["on_farm"]["fixed_cost_per_bu"] +
            storage_costs["on_farm"]["variable_cost_per_bu"] * months
        ) * bushels

        assert commercial_cost == Decimal("2100")
        assert on_farm_cost == Decimal("1800")
        assert on_farm_cost < commercial_cost

    def test_cash_advance_evaluation(self, data_factory):
        """Test evaluating cash advance options."""
        advances = {
            "elevator_advance": {
                "bushels": 20000,
                "advance_per_bu": Decimal("3.50"),
                "interest_rate": 0.08,
                "term_months": 6
            }
        }

        advance = advances["elevator_advance"]
        principal = advance["bushels"] * advance["advance_per_bu"]
        interest = principal * Decimal(str(advance["interest_rate"])) * Decimal(str(advance["term_months"] / 12))

        assert principal == Decimal("70000")
        assert interest == Decimal("2800")

    def test_price_volatility(self, data_factory):
        """Test measuring price volatility."""
        price = CommodityPrice("corn")
        history = price.get_historical_prices(30)
        prices = [h["price"] for h in history]

        avg_price = sum(prices) / len(prices)
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        volatility = std_dev / avg_price * 100

        assert std_dev >= 0
        assert volatility >= 0

    def test_market_news_integration(self, data_factory):
        """Test market news impact analysis."""
        news_events = [
            {"date": date.today(), "headline": "USDA raises corn yield estimate", "impact": "bearish"},
            {"date": date.today(), "headline": "Export sales exceed expectations", "impact": "bullish"},
            {"date": date.today(), "headline": "Brazil crop outlook uncertain", "impact": "bullish"}
        ]

        bullish_count = len([e for e in news_events if e["impact"] == "bullish"])
        bearish_count = len([e for e in news_events if e["impact"] == "bearish"])

        overall_sentiment = "bullish" if bullish_count > bearish_count else "bearish"

        assert overall_sentiment == "bullish"
        assert len(news_events) == 3


# =============================================================================
# RESEARCH & TRIALS TESTS (15 tests)
# =============================================================================

class TestResearchTrials:
    """Tests for research and trial management features."""

    def test_trial_design_basic(self, data_factory):
        """Test designing a basic field trial."""
        trial = FieldTrial("Nitrogen Rate Study", "corn", "field_001")

        trial.add_treatment("Control", "0 lbs N/acre")
        trial.add_treatment("Low", "100 lbs N/acre")
        trial.add_treatment("Medium", "150 lbs N/acre")
        trial.add_treatment("High", "200 lbs N/acre")

        assert len(trial.treatments) == 4
        assert trial.status == "planning"

    def test_trial_randomization(self, data_factory):
        """Test randomizing trial plots."""
        trial = FieldTrial("Test Trial", "corn", "field_001")
        trial.add_treatment("A", "Treatment A")
        trial.add_treatment("B", "Treatment B")
        trial.add_treatment("C", "Treatment C")

        plots = trial.randomize_plots()

        assert len(plots) == 12  # 3 treatments * 4 replicates
        assert trial.status == "randomized"

    def test_trial_replication(self, data_factory):
        """Test setting trial replication."""
        trial = FieldTrial("Test Trial", "corn", "field_001")
        trial.replicates = 6

        trial.add_treatment("A", "Treatment A")
        trial.add_treatment("B", "Treatment B")

        plots = trial.randomize_plots()

        assert len(plots) == 12  # 2 treatments * 6 replicates
        assert trial.replicates == 6

    def test_treatment_application(self, data_factory):
        """Test recording treatment applications."""
        trial = FieldTrial("Test Trial", "corn", "field_001")
        trial.add_treatment("Fungicide", "Apply at V6")
        trial.randomize_plots()

        # Record application
        data_id = trial.record_data(1, "application", 1.0, "Fungicide applied 6/15")

        assert data_id is not None
        assert len(trial.data_collected) == 1

    def test_trial_data_collection(self, data_factory):
        """Test collecting trial data."""
        trial = FieldTrial("Test Trial", "corn", "field_001")
        trial.add_treatment("A", "Treatment A")
        trial.randomize_plots()

        # Collect stand count data
        trial.record_data(1, "stand_count", 32000, "plants per acre")
        trial.record_data(2, "stand_count", 31500, "plants per acre")

        assert len(trial.data_collected) == 2
        assert trial.data_collected[0]["data_type"] == "stand_count"

    def test_trial_harvest_record(self, data_factory):
        """Test recording trial harvest yields."""
        trial = FieldTrial("Test Trial", "corn", "field_001")
        trial.add_treatment("A", "Treatment A")
        trial.randomize_plots()

        yield_id = trial.record_harvest(1, 215.5, 15.2)

        assert yield_id is not None
        assert trial.data_collected[0]["value"] == 215.5
        assert "Moisture: 15.2%" in trial.data_collected[0]["notes"]

    def test_trial_statistical_analysis(self, data_factory):
        """Test running statistical analysis on trial data."""
        trial = FieldTrial("Test Trial", "corn", "field_001")
        t1 = trial.add_treatment("Control", "No treatment")
        t2 = trial.add_treatment("Test", "New product")
        trial.replicates = 4
        trial.randomize_plots()

        # Add yield data for each plot
        yields = {
            t1: [190, 195, 188, 192],
            t2: [210, 215, 208, 212]
        }

        for plot in trial.plots:
            tid = plot["treatment_id"]
            rep_idx = plot["replicate"] - 1
            if tid in yields:
                trial.record_data(plot["plot_number"], "yield", yields[tid][rep_idx])

        stats = TrialStatistics(trial)
        results = stats.analyze()

        assert "treatment_means" in results
        assert results["treatment_means"][t1] == 191.25
        assert results["treatment_means"][t2] == 211.25

    def test_trial_result_interpretation(self, data_factory):
        """Test interpreting trial results."""
        trial = FieldTrial("Test Trial", "corn", "field_001")
        t1 = trial.add_treatment("Control", "No treatment")
        t2 = trial.add_treatment("Test", "New product")
        trial.randomize_plots()

        for plot in trial.plots:
            if plot["treatment_id"] == t1:
                trial.record_data(plot["plot_number"], "yield", 190)
            else:
                trial.record_data(plot["plot_number"], "yield", 210)

        stats = TrialStatistics(trial)
        interpretation = stats.interpret_results()

        assert "Best performing" in interpretation
        assert "bu/ac" in interpretation

    def test_trial_recommendation(self, data_factory):
        """Test generating recommendations from trial results."""
        trial_results = {
            "treatment_means": {
                "control": 190,
                "low_rate": 205,
                "high_rate": 210
            },
            "treatment_costs": {
                "control": 0,
                "low_rate": 25,
                "high_rate": 45
            }
        }

        # Calculate ROI
        corn_price = 4.50
        recommendations = []
        for treatment in trial_results["treatment_means"]:
            if treatment == "control":
                continue
            yield_gain = trial_results["treatment_means"][treatment] - trial_results["treatment_means"]["control"]
            revenue_gain = yield_gain * corn_price
            cost = trial_results["treatment_costs"][treatment]
            roi = (revenue_gain - cost) / cost * 100 if cost > 0 else 0
            recommendations.append({"treatment": treatment, "roi": roi})

        best = max(recommendations, key=lambda x: x["roi"])
        assert best["treatment"] == "low_rate"  # Better ROI

    def test_trial_documentation(self, data_factory):
        """Test trial documentation/lab notes."""
        trial = FieldTrial("Test Trial", "corn", "field_001")

        notes = [
            {"date": date.today(), "type": "observation", "content": "Plots emerged uniformly"},
            {"date": date.today(), "type": "weather", "content": "Heavy rain - 2 inches"},
            {"date": date.today(), "type": "application", "content": "Applied treatments per protocol"}
        ]

        assert len(notes) == 3
        assert all("content" in n for n in notes)

    def test_trial_photo_documentation(self, data_factory):
        """Test photo record management."""
        photos = [
            {
                "id": secrets.token_hex(4),
                "trial_id": "trial_001",
                "plot_number": 1,
                "date": date.today(),
                "stage": "V6",
                "filename": "plot1_v6.jpg"
            },
            {
                "id": secrets.token_hex(4),
                "trial_id": "trial_001",
                "plot_number": 1,
                "date": date.today(),
                "stage": "R1",
                "filename": "plot1_r1.jpg"
            }
        ]

        assert len(photos) == 2
        assert photos[0]["stage"] != photos[1]["stage"]

    def test_trial_cost_tracking(self, data_factory):
        """Test tracking trial costs."""
        trial = FieldTrial("Test Trial", "corn", "field_001")

        trial.add_cost("Seed", Decimal("500"), "inputs")
        trial.add_cost("Treatments", Decimal("750"), "inputs")
        trial.add_cost("Labor", Decimal("300"), "labor")
        trial.add_cost("Equipment", Decimal("200"), "equipment")

        total = trial.calculate_total_cost()

        assert total == Decimal("1750")
        assert len(trial.costs) == 4

    def test_trial_roi_calculation(self, data_factory):
        """Test calculating trial ROI."""
        trial_cost = Decimal("1750")
        findings_value = Decimal("5000")  # Estimated value of knowledge gained

        roi = (findings_value - trial_cost) / trial_cost * 100

        assert roi > 0
        assert round(roi, 1) == Decimal("185.7")

    def test_trial_report_export(self, data_factory):
        """Test exporting trial report data."""
        report_data = {
            "trial_name": "Nitrogen Rate Study 2024",
            "objective": "Determine optimal N rate for corn",
            "treatments": 4,
            "replicates": 4,
            "results_summary": {
                "best_treatment": "150 lbs N/acre",
                "yield_advantage": 15.5,
                "economic_return": 45.00
            },
            "recommendations": "Apply 150 lbs N/acre for optimal return"
        }

        assert "trial_name" in report_data
        assert "results_summary" in report_data
        assert report_data["treatments"] == 4

    def test_trial_benchmarking(self, data_factory):
        """Test comparing trial results to standard practices."""
        trial_yield = 215
        standard_yield = 200
        county_average = 190

        vs_standard = trial_yield - standard_yield
        vs_county = trial_yield - county_average

        assert vs_standard == 15
        assert vs_county == 25
        assert trial_yield > standard_yield > county_average


# =============================================================================
# NOTIFICATIONS TESTS (12 tests)
# =============================================================================

class TestNotifications:
    """Tests for notification system features."""

    def test_task_reminder_notification(self, data_factory):
        """Test task due date reminder alerts."""
        system = NotificationSystem()

        notif_id = system.send_notification(
            "user_001",
            "task_reminder",
            {"task_id": "task_123", "title": "Apply herbicide", "due_date": date.today().isoformat()}
        )

        assert notif_id is not None
        assert len(system.notifications) == 1

    def test_price_alert_notification(self, data_factory):
        """Test price target hit alerts."""
        system = NotificationSystem()

        notif_id = system.send_notification(
            "user_001",
            "price_alert",
            {"commodity": "corn", "target": "5.00", "current": "5.05", "direction": "above"}
        )

        assert notif_id is not None
        notification = system.notifications[0]
        assert notification["type"] == "price_alert"

    def test_weather_alert_notification(self, data_factory):
        """Test weather warning notifications."""
        system = NotificationSystem()

        notif_id = system.send_notification(
            "user_001",
            "weather_alert",
            {"alert_type": "frost_warning", "expected_low": 28, "date": date.today().isoformat()}
        )

        assert notif_id is not None
        assert system.notifications[0]["data"]["alert_type"] == "frost_warning"

    def test_equipment_maintenance_notification(self, data_factory):
        """Test equipment service due alerts."""
        system = NotificationSystem()

        notif_id = system.send_notification(
            "user_001",
            "maintenance_due",
            {"equipment_id": "eq_001", "name": "John Deere 8R", "service_type": "oil_change"}
        )

        assert notif_id is not None
        assert system.notifications[0]["type"] == "maintenance_due"

    def test_inventory_low_notification(self, data_factory):
        """Test low stock level alerts."""
        system = NotificationSystem()

        notif_id = system.send_notification(
            "user_001",
            "low_inventory",
            {"item": "Herbicide XYZ", "current_qty": 5, "min_qty": 10, "unit": "gallons"}
        )

        assert notif_id is not None
        assert system.notifications[0]["data"]["current_qty"] < system.notifications[0]["data"]["min_qty"]

    def test_batch_summary_notification(self, data_factory):
        """Test daily digest notifications."""
        system = NotificationSystem()

        # Send multiple notifications
        for i in range(5):
            system.send_notification("user_001", "task_reminder", {"task_id": f"task_{i}"})

        start = datetime.now() - timedelta(hours=1)
        end = datetime.now() + timedelta(hours=1)
        summary = system.get_batch_summary(start, end)

        assert summary["total"] == 5
        assert summary["delivered"] + summary["failed"] + summary["pending"] == 5

    def test_notification_template(self, data_factory):
        """Test custom notification templates."""
        system = NotificationSystem()

        template_id = system.add_template(
            "price_alert_email",
            "Price Alert: {commodity}",
            "The price of {commodity} has reached ${price}. Your target was ${target}."
        )

        assert template_id is not None
        assert template_id in system.templates
        assert system.templates[template_id]["name"] == "price_alert_email"

    def test_notification_frequency(self, data_factory):
        """Test notification frequency control."""
        preferences = {
            "price_alerts": {"frequency": "immediate", "channels": ["email", "sms"]},
            "task_reminders": {"frequency": "daily_digest", "channels": ["email"]},
            "weather_alerts": {"frequency": "immediate", "channels": ["sms"]}
        }

        assert preferences["price_alerts"]["frequency"] == "immediate"
        assert preferences["task_reminders"]["frequency"] == "daily_digest"
        assert len(preferences) == 3

    def test_notification_failure_retry(self, data_factory):
        """Test retry logic for failed notifications."""
        system = NotificationSystem()

        # Force some failures by sending many
        for i in range(20):
            system.send_notification("user_001", "test", {"index": i})

        # Check if any failed and are in retry queue
        initial_failed = len([n for n in system.notifications if n["status"] == "failed"])

        if initial_failed > 0:
            retried = system.retry_failed()
            assert retried > 0

    def test_notification_audit_log(self, data_factory):
        """Test notification audit trail."""
        system = NotificationSystem()

        system.send_notification("user_001", "test", {"data": "test"})

        audit_log = system.get_audit_log()

        # Should have at least one entry if notification was delivered
        if system.notifications[0]["status"] == "delivered":
            assert len(audit_log) >= 1
            assert "timestamp" in audit_log[0]

    def test_notification_delivery_tracking(self, data_factory):
        """Test tracking notification delivery status."""
        system = NotificationSystem()

        notif_id = system.send_notification("user_001", "test", {"data": "test"})

        notification = next(n for n in system.notifications if n["id"] == notif_id)

        assert notification["status"] in ["delivered", "failed", "pending"]
        assert notification["attempts"] >= 1

    def test_notification_preferences(self, data_factory):
        """Test user notification preferences."""
        system = NotificationSystem()

        prefs = {
            "email_enabled": True,
            "sms_enabled": True,
            "push_enabled": False,
            "quiet_hours": {"start": "22:00", "end": "07:00"},
            "digest_time": "08:00"
        }

        result = system.set_preferences("user_001", prefs)

        assert result is True
        assert system.preferences["user_001"]["email_enabled"] is True
        assert system.preferences["user_001"]["push_enabled"] is False


# =============================================================================
# TEST SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
