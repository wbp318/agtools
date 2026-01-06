"""
PDF Report Generation Service
Generates professional PDF reports for scouting, spray recommendations, costs, etc.
"""

from __future__ import annotations  # Enable postponed evaluation of annotations

import io
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Define placeholder types for type hints when reportlab not installed
    Table = None
    Paragraph = None
    Spacer = None
    SimpleDocTemplate = None
    TableStyle = None
    PageBreak = None
    Image = None
    HRFlowable = None


class ReportType(str, Enum):
    SCOUTING = "scouting"
    SPRAY_RECOMMENDATION = "spray_recommendation"
    FIELD_OPERATIONS = "field_operations"
    COST_PER_ACRE = "cost_per_acre"
    PROFITABILITY = "profitability"
    EQUIPMENT_STATUS = "equipment_status"
    INVENTORY_STATUS = "inventory_status"
    # v4.3.0 - Professional Report Suite
    ANNUAL_PERFORMANCE = "annual_performance"
    LENDER_PACKAGE = "lender_package"
    SPRAY_RECORDS = "spray_records"
    LABOR_SUMMARY = "labor_summary"
    MAINTENANCE_LOG = "maintenance_log"
    FIELD_HISTORY = "field_history"
    GRAIN_MARKETING = "grain_marketing"
    TAX_SUMMARY = "tax_summary"
    CASH_FLOW = "cash_flow"
    SUCCESSION_PLAN = "succession_plan"


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    title: str
    subtitle: Optional[str] = None
    farm_name: Optional[str] = None
    prepared_by: Optional[str] = None
    logo_path: Optional[str] = None
    include_footer: bool = True
    landscape_mode: bool = False


class PDFReportService:
    """Service for generating professional PDF reports"""

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")

        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a5f2a')  # Farm green
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.gray
        ))

        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor('#2d5a3d')
        ))

        # Field label
        self.styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.gray
        ))

        # Field value
        self.styles.add(ParagraphStyle(
            name='FieldValue',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=4
        ))

        # Warning/Alert style
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#c0392b'),
            backColor=colors.HexColor('#fdecea'),
            borderPadding=8
        ))

        # Success style
        self.styles.add(ParagraphStyle(
            name='Success',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#27ae60'),
            backColor=colors.HexColor('#eafaf1'),
            borderPadding=8
        ))

    def _create_header(self, config: ReportConfig) -> List:
        """Create report header elements"""
        elements = []

        # Logo if provided
        if config.logo_path and os.path.exists(config.logo_path):
            logo = Image(config.logo_path, width=1.5*inch, height=1.5*inch)
            elements.append(logo)
            elements.append(Spacer(1, 12))

        # Title
        elements.append(Paragraph(config.title, self.styles['ReportTitle']))

        # Subtitle
        if config.subtitle:
            elements.append(Paragraph(config.subtitle, self.styles['ReportSubtitle']))

        # Farm name and date
        meta_data = []
        if config.farm_name:
            meta_data.append(f"<b>Farm:</b> {config.farm_name}")
        meta_data.append(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}")
        if config.prepared_by:
            meta_data.append(f"<b>Prepared by:</b> {config.prepared_by}")

        for item in meta_data:
            elements.append(Paragraph(item, self.styles['Normal']))

        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1a5f2a')))
        elements.append(Spacer(1, 20))

        return elements

    def _create_table(self, data: List[List], col_widths: Optional[List] = None,
                      header_row: bool = True) -> Table:
        """Create a styled table"""
        table = Table(data, colWidths=col_widths)

        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f2a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]

        table.setStyle(TableStyle(style_commands))
        return table

    def _create_footer(self, canvas, doc):
        """Add footer to each page"""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)

        # Page number
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(doc.pagesize[0] - 0.5*inch, 0.5*inch, text)

        # Generated by
        canvas.drawString(0.5*inch, 0.5*inch, f"Generated by AgTools | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        canvas.restoreState()

    def generate_scouting_report(
        self,
        field_name: str,
        crop: str,
        growth_stage: str,
        observations: List[Dict],
        recommendations: List[str],
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate a scouting report PDF"""
        if config is None:
            config = ReportConfig(
                title="Field Scouting Report",
                subtitle=f"{field_name} - {crop.title()}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Field info section
        elements.append(Paragraph("Field Information", self.styles['SectionHeader']))
        field_data = [
            ["Field Name", field_name],
            ["Crop", crop.title()],
            ["Growth Stage", growth_stage],
            ["Scout Date", datetime.now().strftime('%B %d, %Y')],
        ]
        elements.append(self._create_table(field_data, col_widths=[2*inch, 4*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Observations section
        elements.append(Paragraph("Observations", self.styles['SectionHeader']))
        if observations:
            obs_data = [["Type", "Finding", "Severity", "Location"]]
            for obs in observations:
                obs_data.append([
                    obs.get('type', 'General'),
                    obs.get('finding', ''),
                    obs.get('severity', 'Low'),
                    obs.get('location', 'Field-wide')
                ])
            elements.append(self._create_table(obs_data))
        else:
            elements.append(Paragraph("No significant observations recorded.", self.styles['Normal']))
        elements.append(Spacer(1, 20))

        # Recommendations section
        elements.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                elements.append(Paragraph(f"{i}. {rec}", self.styles['Normal']))
                elements.append(Spacer(1, 4))
        else:
            elements.append(Paragraph("No action required at this time.", self.styles['Success']))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_spray_recommendation(
        self,
        field_name: str,
        crop: str,
        target_pest: str,
        products: List[Dict],
        economics: Dict,
        weather_window: Optional[Dict] = None,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate a spray recommendation report PDF"""
        if config is None:
            config = ReportConfig(
                title="Spray Recommendation",
                subtitle=f"{target_pest} Control - {field_name}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Target info
        elements.append(Paragraph("Treatment Target", self.styles['SectionHeader']))
        target_data = [
            ["Field", field_name],
            ["Crop", crop.title()],
            ["Target Pest/Disease", target_pest],
        ]
        elements.append(self._create_table(target_data, col_widths=[2*inch, 4*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Product recommendations
        elements.append(Paragraph("Recommended Products", self.styles['SectionHeader']))
        if products:
            prod_data = [["Product", "Rate", "Cost/Acre", "MOA Group", "PHI (days)"]]
            for prod in products:
                prod_data.append([
                    prod.get('name', ''),
                    prod.get('rate', ''),
                    f"${prod.get('cost_per_acre', 0):.2f}",
                    prod.get('moa_group', 'N/A'),
                    str(prod.get('phi_days', 'N/A'))
                ])
            elements.append(self._create_table(prod_data))
        elements.append(Spacer(1, 20))

        # Economic analysis
        elements.append(Paragraph("Economic Analysis", self.styles['SectionHeader']))
        econ_data = [
            ["Treatment Cost", f"${economics.get('treatment_cost', 0):.2f}"],
            ["Expected Yield Loss (untreated)", f"{economics.get('yield_loss_bu', 0):.1f} bu/acre"],
            ["Value of Saved Yield", f"${economics.get('saved_value', 0):.2f}"],
            ["Net Benefit", f"${economics.get('net_benefit', 0):.2f}"],
            ["ROI", f"{economics.get('roi_percent', 0):.0f}%"],
        ]
        elements.append(self._create_table(econ_data, col_widths=[3*inch, 3*inch], header_row=False))

        # Recommendation
        if economics.get('net_benefit', 0) > 0:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(
                f"RECOMMENDATION: Treatment is economically justified with ${economics.get('net_benefit', 0):.2f}/acre net benefit.",
                self.styles['Success']
            ))
        else:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(
                "RECOMMENDATION: Treatment may not be economically justified. Consider monitoring.",
                self.styles['Warning']
            ))

        # Weather window if provided
        if weather_window:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Spray Window", self.styles['SectionHeader']))
            weather_data = [
                ["Optimal Time", weather_window.get('optimal_time', 'TBD')],
                ["Temperature", f"{weather_window.get('temp_f', 'N/A')}°F"],
                ["Wind", f"{weather_window.get('wind_mph', 'N/A')} mph"],
                ["Rain Forecast", weather_window.get('rain_forecast', 'None expected')],
            ]
            elements.append(self._create_table(weather_data, col_widths=[2*inch, 4*inch], header_row=False))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_cost_per_acre_report(
        self,
        crop_year: int,
        fields: List[Dict],
        summary: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate a cost per acre report PDF"""
        if config is None:
            config = ReportConfig(
                title="Cost Per Acre Report",
                subtitle=f"Crop Year {crop_year}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Summary section
        elements.append(Paragraph("Summary", self.styles['SectionHeader']))
        summary_data = [
            ["Total Fields", str(summary.get('total_fields', 0))],
            ["Total Acres", f"{summary.get('total_acres', 0):,.1f}"],
            ["Total Expenses", f"${summary.get('total_cost', 0):,.2f}"],
            ["Average Cost/Acre", f"${summary.get('avg_cost_per_acre', 0):,.2f}"],
        ]
        elements.append(self._create_table(summary_data, col_widths=[2.5*inch, 2.5*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Field breakdown
        elements.append(Paragraph("Cost by Field", self.styles['SectionHeader']))
        if fields:
            field_data = [["Field", "Acres", "Crop", "Total Cost", "Cost/Acre"]]
            for field in fields:
                field_data.append([
                    field.get('name', ''),
                    f"{field.get('acres', 0):,.1f}",
                    field.get('crop', ''),
                    f"${field.get('total_cost', 0):,.2f}",
                    f"${field.get('cost_per_acre', 0):,.2f}"
                ])
            elements.append(self._create_table(field_data))
        elements.append(Spacer(1, 20))

        # Category breakdown if available
        if summary.get('by_category'):
            elements.append(Paragraph("Cost by Category", self.styles['SectionHeader']))
            cat_data = [["Category", "Total", "% of Total"]]
            total = summary.get('total_cost', 1)
            for cat, amount in summary['by_category'].items():
                pct = (amount / total * 100) if total > 0 else 0
                cat_data.append([cat.title(), f"${amount:,.2f}", f"{pct:.1f}%"])
            elements.append(self._create_table(cat_data))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_profitability_report(
        self,
        crop_year: int,
        fields: List[Dict],
        summary: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate a profitability analysis report PDF"""
        if config is None:
            config = ReportConfig(
                title="Profitability Analysis",
                subtitle=f"Crop Year {crop_year}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Overall summary
        elements.append(Paragraph("Profitability Summary", self.styles['SectionHeader']))
        summary_data = [
            ["Total Revenue", f"${summary.get('total_revenue', 0):,.2f}"],
            ["Total Expenses", f"${summary.get('total_expenses', 0):,.2f}"],
            ["Net Profit", f"${summary.get('net_profit', 0):,.2f}"],
            ["Profit/Acre", f"${summary.get('profit_per_acre', 0):,.2f}"],
            ["Break-Even Yield", f"{summary.get('breakeven_yield', 0):,.1f} bu/acre"],
            ["Break-Even Price", f"${summary.get('breakeven_price', 0):,.2f}/bu"],
        ]
        elements.append(self._create_table(summary_data, col_widths=[2.5*inch, 2.5*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Field profitability
        elements.append(Paragraph("Profitability by Field", self.styles['SectionHeader']))
        if fields:
            field_data = [["Field", "Acres", "Revenue", "Expenses", "Profit", "$/Acre"]]
            for field in fields:
                profit = field.get('revenue', 0) - field.get('expenses', 0)
                profit_per_acre = profit / field.get('acres', 1) if field.get('acres', 0) > 0 else 0
                field_data.append([
                    field.get('name', ''),
                    f"{field.get('acres', 0):,.1f}",
                    f"${field.get('revenue', 0):,.2f}",
                    f"${field.get('expenses', 0):,.2f}",
                    f"${profit:,.2f}",
                    f"${profit_per_acre:,.2f}"
                ])
            elements.append(self._create_table(field_data))

        # Profitability status
        net_profit = summary.get('net_profit', 0)
        elements.append(Spacer(1, 20))
        if net_profit > 0:
            elements.append(Paragraph(
                f"PROFITABLE: Net profit of ${net_profit:,.2f} for the crop year.",
                self.styles['Success']
            ))
        else:
            elements.append(Paragraph(
                f"LOSS: Net loss of ${abs(net_profit):,.2f} for the crop year.",
                self.styles['Warning']
            ))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_equipment_status_report(
        self,
        equipment_list: List[Dict],
        maintenance_alerts: List[Dict],
        summary: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate equipment status report PDF"""
        if config is None:
            config = ReportConfig(
                title="Equipment Status Report",
                subtitle=f"As of {datetime.now().strftime('%B %d, %Y')}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Fleet summary
        elements.append(Paragraph("Fleet Summary", self.styles['SectionHeader']))
        summary_data = [
            ["Total Equipment", str(summary.get('total_count', 0))],
            ["Fleet Value", f"${summary.get('total_value', 0):,.2f}"],
            ["Total Hours", f"{summary.get('total_hours', 0):,.0f}"],
            ["In Maintenance", str(summary.get('in_maintenance', 0))],
        ]
        elements.append(self._create_table(summary_data, col_widths=[2*inch, 4*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Maintenance alerts
        if maintenance_alerts:
            elements.append(Paragraph("Maintenance Alerts", self.styles['SectionHeader']))
            alert_data = [["Equipment", "Type", "Due", "Status"]]
            for alert in maintenance_alerts:
                alert_data.append([
                    alert.get('equipment_name', ''),
                    alert.get('maintenance_type', ''),
                    alert.get('due_date', 'N/A'),
                    alert.get('status', 'Due')
                ])
            elements.append(self._create_table(alert_data))
            elements.append(Spacer(1, 20))

        # Equipment list
        elements.append(Paragraph("Equipment Inventory", self.styles['SectionHeader']))
        if equipment_list:
            equip_data = [["Name", "Type", "Year", "Hours", "Status"]]
            for equip in equipment_list:
                equip_data.append([
                    equip.get('name', ''),
                    equip.get('equipment_type', ''),
                    str(equip.get('year', 'N/A')),
                    f"{equip.get('current_hours', 0):,.0f}",
                    equip.get('status', 'available').title()
                ])
            elements.append(self._create_table(equip_data))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_inventory_status_report(
        self,
        inventory_items: List[Dict],
        low_stock_alerts: List[Dict],
        expiring_soon: List[Dict],
        summary: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate inventory status report PDF"""
        if config is None:
            config = ReportConfig(
                title="Inventory Status Report",
                subtitle=f"As of {datetime.now().strftime('%B %d, %Y')}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Summary
        elements.append(Paragraph("Inventory Summary", self.styles['SectionHeader']))
        summary_data = [
            ["Total Items", str(summary.get('total_items', 0))],
            ["Total Value", f"${summary.get('total_value', 0):,.2f}"],
            ["Low Stock Items", str(summary.get('low_stock_count', 0))],
            ["Expiring Soon", str(summary.get('expiring_count', 0))],
        ]
        elements.append(self._create_table(summary_data, col_widths=[2*inch, 4*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Low stock alerts
        if low_stock_alerts:
            elements.append(Paragraph("Low Stock Alerts", self.styles['SectionHeader']))
            low_data = [["Item", "Category", "Current Qty", "Reorder Point"]]
            for item in low_stock_alerts:
                low_data.append([
                    item.get('name', ''),
                    item.get('category', ''),
                    f"{item.get('quantity', 0)} {item.get('unit', '')}",
                    f"{item.get('reorder_point', 0)} {item.get('unit', '')}"
                ])
            elements.append(self._create_table(low_data))
            elements.append(Spacer(1, 20))

        # Expiring soon
        if expiring_soon:
            elements.append(Paragraph("Expiring Soon", self.styles['SectionHeader']))
            exp_data = [["Item", "Category", "Quantity", "Expiration Date"]]
            for item in expiring_soon:
                exp_data.append([
                    item.get('name', ''),
                    item.get('category', ''),
                    f"{item.get('quantity', 0)} {item.get('unit', '')}",
                    item.get('expiration_date', 'N/A')
                ])
            elements.append(self._create_table(exp_data))
            elements.append(Spacer(1, 20))

        # Full inventory by category
        elements.append(Paragraph("Inventory by Category", self.styles['SectionHeader']))
        if inventory_items:
            inv_data = [["Item", "Category", "Quantity", "Unit Cost", "Total Value"]]
            for item in inventory_items[:20]:  # Limit to 20 items
                total = item.get('quantity', 0) * item.get('cost_per_unit', 0)
                inv_data.append([
                    item.get('name', ''),
                    item.get('category', ''),
                    f"{item.get('quantity', 0)} {item.get('unit', '')}",
                    f"${item.get('cost_per_unit', 0):.2f}",
                    f"${total:,.2f}"
                ])
            elements.append(self._create_table(inv_data))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    # =========================================================================
    # v4.3.0 - PROFESSIONAL REPORT SUITE
    # =========================================================================

    def generate_annual_performance_report(
        self,
        crop_year: int,
        farm_summary: Dict,
        field_performance: List[Dict],
        cost_breakdown: Dict,
        yield_data: Dict,
        comparison: Optional[Dict] = None,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate comprehensive annual farm performance report PDF"""
        if config is None:
            config = ReportConfig(
                title="Annual Farm Performance Report",
                subtitle=f"Crop Year {crop_year}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Executive Summary
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        exec_data = [
            ["Total Acres Farmed", f"{farm_summary.get('total_acres', 0):,.1f}"],
            ["Total Gross Revenue", f"${farm_summary.get('gross_revenue', 0):,.2f}"],
            ["Total Operating Expenses", f"${farm_summary.get('total_expenses', 0):,.2f}"],
            ["Net Farm Income", f"${farm_summary.get('net_income', 0):,.2f}"],
            ["Return on Assets", f"{farm_summary.get('roa_percent', 0):.1f}%"],
        ]
        elements.append(self._create_table(exec_data, col_widths=[3*inch, 3*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Production Summary by Crop
        elements.append(Paragraph("Production Summary", self.styles['SectionHeader']))
        if yield_data.get('by_crop'):
            crop_data = [["Crop", "Acres", "Total Bushels", "Avg Yield", "Revenue"]]
            for crop_info in yield_data['by_crop']:
                crop_data.append([
                    crop_info.get('crop', '').title(),
                    f"{crop_info.get('acres', 0):,.1f}",
                    f"{crop_info.get('total_bushels', 0):,.0f}",
                    f"{crop_info.get('avg_yield', 0):,.1f} bu/ac",
                    f"${crop_info.get('revenue', 0):,.2f}"
                ])
            elements.append(self._create_table(crop_data))
        elements.append(Spacer(1, 20))

        # Cost Breakdown
        elements.append(Paragraph("Cost Analysis", self.styles['SectionHeader']))
        if cost_breakdown:
            cost_data = [["Category", "Amount", "$/Acre", "% of Total"]]
            total = farm_summary.get('total_expenses', 1)
            for cat, amount in cost_breakdown.items():
                per_acre = amount / farm_summary.get('total_acres', 1)
                pct = (amount / total * 100) if total > 0 else 0
                cost_data.append([
                    cat.replace('_', ' ').title(),
                    f"${amount:,.2f}",
                    f"${per_acre:,.2f}",
                    f"{pct:.1f}%"
                ])
            elements.append(self._create_table(cost_data))
        elements.append(Spacer(1, 20))

        # Field Performance Table
        elements.append(Paragraph("Field Performance", self.styles['SectionHeader']))
        if field_performance:
            field_data = [["Field", "Crop", "Acres", "Yield", "Revenue", "Cost", "Profit/Ac"]]
            for field in field_performance:
                profit_per_acre = (field.get('revenue', 0) - field.get('cost', 0)) / field.get('acres', 1)
                field_data.append([
                    field.get('name', '')[:15],
                    field.get('crop', '').title(),
                    f"{field.get('acres', 0):,.0f}",
                    f"{field.get('yield_per_acre', 0):,.1f}",
                    f"${field.get('revenue', 0):,.0f}",
                    f"${field.get('cost', 0):,.0f}",
                    f"${profit_per_acre:,.0f}"
                ])
            elements.append(self._create_table(field_data))

        # Year-over-Year Comparison (if available)
        if comparison:
            elements.append(PageBreak())
            elements.append(Paragraph("Year-over-Year Comparison", self.styles['SectionHeader']))
            comp_data = [["Metric", f"{crop_year - 1}", f"{crop_year}", "Change"]]
            for metric, values in comparison.items():
                change = values.get('current', 0) - values.get('previous', 0)
                change_str = f"+{change:,.0f}" if change >= 0 else f"{change:,.0f}"
                comp_data.append([
                    metric.replace('_', ' ').title(),
                    f"{values.get('previous', 0):,.0f}",
                    f"{values.get('current', 0):,.0f}",
                    change_str
                ])
            elements.append(self._create_table(comp_data))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_lender_package_report(
        self,
        farm_info: Dict,
        income_history: List[Dict],
        balance_sheet: Dict,
        cash_flow_projection: List[Dict],
        collateral: List[Dict],
        loan_request: Optional[Dict] = None,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate lender-ready financial package PDF"""
        if config is None:
            config = ReportConfig(
                title="Farm Financial Package",
                subtitle="Confidential - For Lender Review"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Executive Summary
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        exec_text = f"""
        This financial package presents the operating history and financial position of
        {farm_info.get('farm_name', 'the farm operation')}. The operation includes
        {farm_info.get('total_acres', 0):,.0f} acres of cropland producing primarily
        {farm_info.get('primary_crops', 'row crops')}. Current year projected revenue
        is ${farm_info.get('projected_revenue', 0):,.0f}.
        """
        elements.append(Paragraph(exec_text, self.styles['Normal']))
        elements.append(Spacer(1, 20))

        # Farm Overview
        elements.append(Paragraph("Farm Overview", self.styles['SectionHeader']))
        overview_data = [
            ["Farm Name", farm_info.get('farm_name', '')],
            ["Operator(s)", farm_info.get('operators', '')],
            ["Years in Operation", str(farm_info.get('years_operating', ''))],
            ["Total Acres", f"{farm_info.get('total_acres', 0):,.0f}"],
            ["Owned Acres", f"{farm_info.get('owned_acres', 0):,.0f}"],
            ["Leased Acres", f"{farm_info.get('leased_acres', 0):,.0f}"],
            ["Primary Crops", farm_info.get('primary_crops', '')],
            ["County/State", farm_info.get('location', '')],
        ]
        elements.append(self._create_table(overview_data, col_widths=[2.5*inch, 4*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # 3-Year Income History
        elements.append(Paragraph("Income History (3 Years)", self.styles['SectionHeader']))
        if income_history:
            income_data = [["Year", "Gross Revenue", "Operating Expenses", "Net Income", "Debt Service"]]
            for year in income_history:
                income_data.append([
                    str(year.get('year', '')),
                    f"${year.get('gross_revenue', 0):,.0f}",
                    f"${year.get('operating_expenses', 0):,.0f}",
                    f"${year.get('net_income', 0):,.0f}",
                    f"${year.get('debt_service', 0):,.0f}"
                ])
            elements.append(self._create_table(income_data))
        elements.append(Spacer(1, 20))

        # Balance Sheet Summary
        elements.append(Paragraph("Balance Sheet Summary", self.styles['SectionHeader']))
        bs_data = [
            ["ASSETS", ""],
            ["Current Assets (Cash, Inventory, Receivables)", f"${balance_sheet.get('current_assets', 0):,.0f}"],
            ["Intermediate Assets (Equipment, Vehicles)", f"${balance_sheet.get('intermediate_assets', 0):,.0f}"],
            ["Long-Term Assets (Land, Buildings)", f"${balance_sheet.get('long_term_assets', 0):,.0f}"],
            ["Total Assets", f"${balance_sheet.get('total_assets', 0):,.0f}"],
            ["", ""],
            ["LIABILITIES", ""],
            ["Current Liabilities (Operating Notes, Accounts Payable)", f"${balance_sheet.get('current_liabilities', 0):,.0f}"],
            ["Intermediate Liabilities (Equipment Loans)", f"${balance_sheet.get('intermediate_liabilities', 0):,.0f}"],
            ["Long-Term Liabilities (Real Estate Mortgages)", f"${balance_sheet.get('long_term_liabilities', 0):,.0f}"],
            ["Total Liabilities", f"${balance_sheet.get('total_liabilities', 0):,.0f}"],
            ["", ""],
            ["NET WORTH", f"${balance_sheet.get('net_worth', 0):,.0f}"],
            ["Debt-to-Asset Ratio", f"{balance_sheet.get('debt_to_asset', 0):.1%}"],
        ]
        elements.append(self._create_table(bs_data, col_widths=[4*inch, 2.5*inch], header_row=False))

        # Cash Flow Projection
        elements.append(PageBreak())
        elements.append(Paragraph("12-Month Cash Flow Projection", self.styles['SectionHeader']))
        if cash_flow_projection:
            cf_data = [["Month", "Income", "Expenses", "Loan Pmts", "Net Cash", "Balance"]]
            for month in cash_flow_projection[:12]:
                cf_data.append([
                    month.get('month', ''),
                    f"${month.get('income', 0):,.0f}",
                    f"${month.get('expenses', 0):,.0f}",
                    f"${month.get('loan_payments', 0):,.0f}",
                    f"${month.get('net_cash', 0):,.0f}",
                    f"${month.get('ending_balance', 0):,.0f}"
                ])
            elements.append(self._create_table(cf_data))
        elements.append(Spacer(1, 20))

        # Collateral Listing
        elements.append(Paragraph("Collateral Available", self.styles['SectionHeader']))
        if collateral:
            coll_data = [["Description", "Type", "Est. Value", "Current Liens"]]
            for item in collateral:
                coll_data.append([
                    item.get('description', ''),
                    item.get('type', ''),
                    f"${item.get('value', 0):,.0f}",
                    f"${item.get('liens', 0):,.0f}"
                ])
            elements.append(self._create_table(coll_data))
        elements.append(Spacer(1, 20))

        # Loan Request (if applicable)
        if loan_request:
            elements.append(Paragraph("Loan Request", self.styles['SectionHeader']))
            loan_data = [
                ["Loan Amount Requested", f"${loan_request.get('amount', 0):,.0f}"],
                ["Purpose", loan_request.get('purpose', '')],
                ["Proposed Term", loan_request.get('term', '')],
                ["Proposed Collateral", loan_request.get('collateral', '')],
            ]
            elements.append(self._create_table(loan_data, col_widths=[2.5*inch, 4*inch], header_row=False))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_spray_records_report(
        self,
        applications: List[Dict],
        date_range: Dict,
        applicator_info: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate spray application records for compliance PDF"""
        if config is None:
            start = date_range.get('start', '')
            end = date_range.get('end', '')
            config = ReportConfig(
                title="Pesticide Application Records",
                subtitle=f"{start} to {end}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Applicator Information
        elements.append(Paragraph("Applicator Information", self.styles['SectionHeader']))
        app_data = [
            ["Applicator Name", applicator_info.get('name', '')],
            ["License Number", applicator_info.get('license_number', '')],
            ["License Type", applicator_info.get('license_type', '')],
            ["Expiration Date", applicator_info.get('expiration_date', '')],
            ["Company", applicator_info.get('company', '')],
        ]
        elements.append(self._create_table(app_data, col_widths=[2*inch, 3*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Application Records
        elements.append(Paragraph("Application Records", self.styles['SectionHeader']))
        if applications:
            app_records = [["Date", "Field", "Crop", "Product", "EPA Reg#", "Rate", "Acres", "Weather", "PHI"]]
            for app in applications:
                weather_str = f"{app.get('temp_f', '')}°F, {app.get('wind_mph', '')}mph"
                app_records.append([
                    app.get('date', ''),
                    app.get('field_name', '')[:12],
                    app.get('crop', ''),
                    app.get('product_name', '')[:15],
                    app.get('epa_reg_number', ''),
                    f"{app.get('rate', '')} {app.get('rate_unit', '')}",
                    f"{app.get('acres', 0):,.1f}",
                    weather_str,
                    f"{app.get('phi_days', 'N/A')}"
                ])
            elements.append(self._create_table(app_records))
        else:
            elements.append(Paragraph("No applications recorded for this period.", self.styles['Normal']))
        elements.append(Spacer(1, 20))

        # Compliance Statement
        elements.append(Paragraph("Compliance Certification", self.styles['SectionHeader']))
        cert_text = """
        I certify that the above pesticide applications were made in accordance with
        the product label, EPA regulations, and applicable state laws. All restricted
        entry intervals (REI) and pre-harvest intervals (PHI) were observed.
        """
        elements.append(Paragraph(cert_text, self.styles['Normal']))
        elements.append(Spacer(1, 30))

        # Signature lines
        sig_data = [
            ["_" * 40, "_" * 20],
            ["Applicator Signature", "Date"],
        ]
        elements.append(self._create_table(sig_data, col_widths=[4*inch, 2*inch], header_row=False))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_labor_summary_report(
        self,
        date_range: Dict,
        employees: List[Dict],
        hours_by_task: Dict,
        hours_by_field: Dict,
        payroll_summary: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate labor summary report PDF"""
        if config is None:
            start = date_range.get('start', '')
            end = date_range.get('end', '')
            config = ReportConfig(
                title="Labor Summary Report",
                subtitle=f"{start} to {end}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Payroll Summary
        elements.append(Paragraph("Payroll Summary", self.styles['SectionHeader']))
        pay_data = [
            ["Total Regular Hours", f"{payroll_summary.get('regular_hours', 0):,.1f}"],
            ["Total Overtime Hours", f"{payroll_summary.get('overtime_hours', 0):,.1f}"],
            ["Total Hours", f"{payroll_summary.get('total_hours', 0):,.1f}"],
            ["Regular Pay", f"${payroll_summary.get('regular_pay', 0):,.2f}"],
            ["Overtime Pay", f"${payroll_summary.get('overtime_pay', 0):,.2f}"],
            ["Total Labor Cost", f"${payroll_summary.get('total_pay', 0):,.2f}"],
        ]
        elements.append(self._create_table(pay_data, col_widths=[3*inch, 3*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Hours by Employee
        elements.append(Paragraph("Hours by Employee", self.styles['SectionHeader']))
        if employees:
            emp_data = [["Employee", "Regular Hrs", "OT Hrs", "Total Hrs", "Pay Rate", "Total Pay"]]
            for emp in employees:
                emp_data.append([
                    emp.get('name', ''),
                    f"{emp.get('regular_hours', 0):,.1f}",
                    f"{emp.get('overtime_hours', 0):,.1f}",
                    f"{emp.get('total_hours', 0):,.1f}",
                    f"${emp.get('pay_rate', 0):,.2f}/hr",
                    f"${emp.get('total_pay', 0):,.2f}"
                ])
            elements.append(self._create_table(emp_data))
        elements.append(Spacer(1, 20))

        # Hours by Task Type
        elements.append(Paragraph("Hours by Task Type", self.styles['SectionHeader']))
        if hours_by_task:
            task_data = [["Task Type", "Hours", "% of Total"]]
            total_hours = payroll_summary.get('total_hours', 1)
            for task, hours in hours_by_task.items():
                pct = (hours / total_hours * 100) if total_hours > 0 else 0
                task_data.append([
                    task.replace('_', ' ').title(),
                    f"{hours:,.1f}",
                    f"{pct:.1f}%"
                ])
            elements.append(self._create_table(task_data))
        elements.append(Spacer(1, 20))

        # Hours by Field
        elements.append(Paragraph("Hours by Field", self.styles['SectionHeader']))
        if hours_by_field:
            field_data = [["Field", "Hours", "Labor Cost"]]
            avg_rate = payroll_summary.get('total_pay', 0) / payroll_summary.get('total_hours', 1)
            for field, hours in hours_by_field.items():
                field_data.append([
                    field,
                    f"{hours:,.1f}",
                    f"${hours * avg_rate:,.2f}"
                ])
            elements.append(self._create_table(field_data))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_maintenance_log_report(
        self,
        equipment_name: str,
        equipment_info: Dict,
        maintenance_history: List[Dict],
        upcoming_maintenance: List[Dict],
        cost_summary: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate equipment maintenance log report PDF"""
        if config is None:
            config = ReportConfig(
                title="Equipment Maintenance Log",
                subtitle=equipment_name
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Equipment Information
        elements.append(Paragraph("Equipment Information", self.styles['SectionHeader']))
        equip_data = [
            ["Name", equipment_info.get('name', '')],
            ["Type", equipment_info.get('type', '')],
            ["Make/Model", f"{equipment_info.get('make', '')} {equipment_info.get('model', '')}"],
            ["Year", str(equipment_info.get('year', ''))],
            ["Serial Number", equipment_info.get('serial_number', '')],
            ["Current Hours", f"{equipment_info.get('current_hours', 0):,.0f}"],
            ["Purchase Date", equipment_info.get('purchase_date', '')],
            ["Purchase Price", f"${equipment_info.get('purchase_price', 0):,.0f}"],
        ]
        elements.append(self._create_table(equip_data, col_widths=[2*inch, 4*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Maintenance Cost Summary
        elements.append(Paragraph("Maintenance Cost Summary", self.styles['SectionHeader']))
        cost_data = [
            ["YTD Maintenance Cost", f"${cost_summary.get('ytd_cost', 0):,.2f}"],
            ["Lifetime Maintenance Cost", f"${cost_summary.get('lifetime_cost', 0):,.2f}"],
            ["Cost per Hour", f"${cost_summary.get('cost_per_hour', 0):,.2f}"],
            ["Total Services Performed", str(cost_summary.get('total_services', 0))],
        ]
        elements.append(self._create_table(cost_data, col_widths=[3*inch, 3*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Upcoming Maintenance
        if upcoming_maintenance:
            elements.append(Paragraph("Upcoming Maintenance", self.styles['SectionHeader']))
            upcoming_data = [["Service Type", "Due Date/Hours", "Est. Cost", "Priority"]]
            for maint in upcoming_maintenance:
                upcoming_data.append([
                    maint.get('type', ''),
                    maint.get('due', ''),
                    f"${maint.get('estimated_cost', 0):,.2f}",
                    maint.get('priority', 'Normal')
                ])
            elements.append(self._create_table(upcoming_data))
            elements.append(Spacer(1, 20))

        # Maintenance History
        elements.append(Paragraph("Maintenance History", self.styles['SectionHeader']))
        if maintenance_history:
            hist_data = [["Date", "Service Type", "Hours", "Description", "Parts", "Cost"]]
            for record in maintenance_history:
                hist_data.append([
                    record.get('date', ''),
                    record.get('type', ''),
                    f"{record.get('hours', 0):,.0f}",
                    record.get('description', '')[:30],
                    record.get('parts', '')[:20],
                    f"${record.get('cost', 0):,.2f}"
                ])
            elements.append(self._create_table(hist_data))
        else:
            elements.append(Paragraph("No maintenance records found.", self.styles['Normal']))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_field_history_report(
        self,
        field_info: Dict,
        operations_history: List[Dict],
        input_summary: Dict,
        yield_history: List[Dict],
        cost_summary: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate field operations history report PDF"""
        if config is None:
            config = ReportConfig(
                title="Field Operations History",
                subtitle=field_info.get('name', '')
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Field Information
        elements.append(Paragraph("Field Information", self.styles['SectionHeader']))
        field_data = [
            ["Field Name", field_info.get('name', '')],
            ["Farm", field_info.get('farm_name', '')],
            ["Total Acres", f"{field_info.get('acres', 0):,.1f}"],
            ["Soil Type", field_info.get('soil_type', '')],
            ["Irrigation", field_info.get('irrigation', 'None')],
            ["Current Crop", field_info.get('current_crop', '').title()],
        ]
        elements.append(self._create_table(field_data, col_widths=[2*inch, 4*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Yield History
        elements.append(Paragraph("Yield History", self.styles['SectionHeader']))
        if yield_history:
            yield_data = [["Year", "Crop", "Yield/Acre", "Total Bushels", "Price", "Revenue"]]
            for record in yield_history:
                yield_data.append([
                    str(record.get('year', '')),
                    record.get('crop', '').title(),
                    f"{record.get('yield_per_acre', 0):,.1f}",
                    f"{record.get('total_bushels', 0):,.0f}",
                    f"${record.get('price', 0):,.2f}",
                    f"${record.get('revenue', 0):,.0f}"
                ])
            elements.append(self._create_table(yield_data))
        elements.append(Spacer(1, 20))

        # Input Summary
        elements.append(Paragraph("Input Summary (Current Year)", self.styles['SectionHeader']))
        if input_summary:
            input_data = [["Input Type", "Product", "Rate", "Total Applied", "Cost"]]
            for input_type, details in input_summary.items():
                if isinstance(details, dict):
                    input_data.append([
                        input_type.replace('_', ' ').title(),
                        details.get('product', ''),
                        details.get('rate', ''),
                        details.get('total_applied', ''),
                        f"${details.get('cost', 0):,.2f}"
                    ])
            elements.append(self._create_table(input_data))
        elements.append(Spacer(1, 20))

        # Cost Summary
        elements.append(Paragraph("Cost Summary", self.styles['SectionHeader']))
        cost_data = [
            ["Total Input Costs", f"${cost_summary.get('input_costs', 0):,.2f}"],
            ["Application Costs", f"${cost_summary.get('application_costs', 0):,.2f}"],
            ["Total Cost/Acre", f"${cost_summary.get('cost_per_acre', 0):,.2f}"],
            ["Cumulative Investment", f"${cost_summary.get('cumulative_cost', 0):,.2f}"],
        ]
        elements.append(self._create_table(cost_data, col_widths=[3*inch, 3*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Operations Log
        elements.append(Paragraph("Operations Log", self.styles['SectionHeader']))
        if operations_history:
            ops_data = [["Date", "Operation", "Product", "Rate", "Acres", "Cost"]]
            for op in operations_history[:25]:  # Limit to 25 most recent
                ops_data.append([
                    op.get('date', ''),
                    op.get('operation_type', '').title(),
                    op.get('product', '')[:20],
                    op.get('rate', ''),
                    f"{op.get('acres', 0):,.1f}",
                    f"${op.get('cost', 0):,.2f}"
                ])
            elements.append(self._create_table(ops_data))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_grain_marketing_report(
        self,
        crop_year: int,
        inventory_summary: Dict,
        bins: List[Dict],
        sales_history: List[Dict],
        price_analysis: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate grain marketing report PDF"""
        if config is None:
            config = ReportConfig(
                title="Grain Marketing Report",
                subtitle=f"Crop Year {crop_year}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Inventory Summary
        elements.append(Paragraph("Current Inventory", self.styles['SectionHeader']))
        inv_data = [
            ["Total Bushels in Storage", f"{inventory_summary.get('total_bushels', 0):,.0f}"],
            ["Estimated Value", f"${inventory_summary.get('total_value', 0):,.2f}"],
            ["Average Moisture", f"{inventory_summary.get('avg_moisture', 0):.1f}%"],
            ["Storage Capacity Used", f"{inventory_summary.get('capacity_used_pct', 0):.1f}%"],
        ]
        elements.append(self._create_table(inv_data, col_widths=[3*inch, 3*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Inventory by Bin
        elements.append(Paragraph("Inventory by Location", self.styles['SectionHeader']))
        if bins:
            bin_data = [["Bin/Location", "Grain", "Bushels", "Moisture", "Test Weight", "Value"]]
            for bin_info in bins:
                bin_data.append([
                    bin_info.get('name', ''),
                    bin_info.get('grain_type', '').title(),
                    f"{bin_info.get('bushels', 0):,.0f}",
                    f"{bin_info.get('moisture', 0):.1f}%",
                    f"{bin_info.get('test_weight', 0):.1f}",
                    f"${bin_info.get('value', 0):,.0f}"
                ])
            elements.append(self._create_table(bin_data))
        elements.append(Spacer(1, 20))

        # Sales History
        elements.append(Paragraph("Sales History", self.styles['SectionHeader']))
        if sales_history:
            sales_data = [["Date", "Buyer", "Grain", "Bushels", "Price", "Basis", "Total"]]
            for sale in sales_history:
                sales_data.append([
                    sale.get('date', ''),
                    sale.get('buyer', '')[:15],
                    sale.get('grain_type', '').title(),
                    f"{sale.get('bushels', 0):,.0f}",
                    f"${sale.get('price', 0):,.2f}",
                    f"{sale.get('basis', 0):+.2f}",
                    f"${sale.get('total', 0):,.0f}"
                ])
            elements.append(self._create_table(sales_data))
        elements.append(Spacer(1, 20))

        # Price Analysis
        elements.append(Paragraph("Price Analysis", self.styles['SectionHeader']))
        price_data = [
            ["Average Sale Price", f"${price_analysis.get('avg_price', 0):,.2f}/bu"],
            ["Highest Sale Price", f"${price_analysis.get('high_price', 0):,.2f}/bu"],
            ["Lowest Sale Price", f"${price_analysis.get('low_price', 0):,.2f}/bu"],
            ["Average Basis", f"{price_analysis.get('avg_basis', 0):+.2f}"],
            ["Total Bushels Sold", f"{price_analysis.get('total_sold', 0):,.0f}"],
            ["Total Revenue", f"${price_analysis.get('total_revenue', 0):,.2f}"],
            ["Bushels Remaining", f"{price_analysis.get('remaining', 0):,.0f}"],
        ]
        elements.append(self._create_table(price_data, col_widths=[3*inch, 3*inch], header_row=False))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_tax_summary_report(
        self,
        tax_year: int,
        depreciation_schedule: List[Dict],
        expense_summary: Dict,
        section_179: Dict,
        tax_projection: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate tax planning summary report PDF"""
        if config is None:
            config = ReportConfig(
                title="Tax Planning Summary",
                subtitle=f"Tax Year {tax_year}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Tax Projection Summary
        elements.append(Paragraph("Tax Projection Summary", self.styles['SectionHeader']))
        tax_data = [
            ["Gross Farm Income", f"${tax_projection.get('gross_income', 0):,.2f}"],
            ["Total Deductible Expenses", f"${tax_projection.get('total_expenses', 0):,.2f}"],
            ["Depreciation Deduction", f"${tax_projection.get('depreciation', 0):,.2f}"],
            ["Section 179 Deduction", f"${tax_projection.get('section_179', 0):,.2f}"],
            ["Net Farm Income", f"${tax_projection.get('net_income', 0):,.2f}"],
            ["Estimated Self-Employment Tax", f"${tax_projection.get('se_tax', 0):,.2f}"],
            ["Estimated Income Tax", f"${tax_projection.get('income_tax', 0):,.2f}"],
            ["Total Estimated Tax", f"${tax_projection.get('total_tax', 0):,.2f}"],
        ]
        elements.append(self._create_table(tax_data, col_widths=[3.5*inch, 2.5*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Expense Summary by Category
        elements.append(Paragraph("Deductible Expenses by Category", self.styles['SectionHeader']))
        if expense_summary:
            exp_data = [["Category", "Amount", "% of Total"]]
            total = tax_projection.get('total_expenses', 1)
            for cat, amount in expense_summary.items():
                pct = (amount / total * 100) if total > 0 else 0
                exp_data.append([
                    cat.replace('_', ' ').title(),
                    f"${amount:,.2f}",
                    f"{pct:.1f}%"
                ])
            elements.append(self._create_table(exp_data))
        elements.append(Spacer(1, 20))

        # Section 179 Summary
        elements.append(Paragraph("Section 179 Deduction", self.styles['SectionHeader']))
        s179_data = [
            ["Available Limit", f"${section_179.get('limit', 1160000):,.0f}"],
            ["Amount Elected", f"${section_179.get('elected', 0):,.2f}"],
            ["Remaining Available", f"${section_179.get('remaining', 0):,.2f}"],
        ]
        elements.append(self._create_table(s179_data, col_widths=[3*inch, 3*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Depreciation Schedule
        elements.append(Paragraph("Depreciation Schedule", self.styles['SectionHeader']))
        if depreciation_schedule:
            dep_data = [["Asset", "Method", "Basis", f"{tax_year} Depr.", "Book Value"]]
            for asset in depreciation_schedule:
                dep_data.append([
                    asset.get('name', '')[:25],
                    asset.get('method', ''),
                    f"${asset.get('basis', 0):,.0f}",
                    f"${asset.get('current_depreciation', 0):,.0f}",
                    f"${asset.get('book_value', 0):,.0f}"
                ])
            elements.append(self._create_table(dep_data))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_cash_flow_report(
        self,
        date_range: Dict,
        monthly_data: List[Dict],
        loan_summary: List[Dict],
        summary: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate cash flow report PDF"""
        if config is None:
            start = date_range.get('start', '')
            end = date_range.get('end', '')
            config = ReportConfig(
                title="Cash Flow Report",
                subtitle=f"{start} to {end}"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Cash Flow Summary
        elements.append(Paragraph("Cash Flow Summary", self.styles['SectionHeader']))
        sum_data = [
            ["Beginning Cash Balance", f"${summary.get('beginning_balance', 0):,.2f}"],
            ["Total Cash Inflows", f"${summary.get('total_inflows', 0):,.2f}"],
            ["Total Cash Outflows", f"${summary.get('total_outflows', 0):,.2f}"],
            ["Net Cash Flow", f"${summary.get('net_cash_flow', 0):,.2f}"],
            ["Ending Cash Balance", f"${summary.get('ending_balance', 0):,.2f}"],
        ]
        elements.append(self._create_table(sum_data, col_widths=[3*inch, 3*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Monthly Cash Flow
        elements.append(Paragraph("Monthly Cash Flow", self.styles['SectionHeader']))
        if monthly_data:
            month_data = [["Month", "Inflows", "Operating", "Loan Pmts", "Other", "Net", "Balance"]]
            for month in monthly_data:
                month_data.append([
                    month.get('month', ''),
                    f"${month.get('inflows', 0):,.0f}",
                    f"${month.get('operating', 0):,.0f}",
                    f"${month.get('loan_payments', 0):,.0f}",
                    f"${month.get('other', 0):,.0f}",
                    f"${month.get('net', 0):,.0f}",
                    f"${month.get('balance', 0):,.0f}"
                ])
            elements.append(self._create_table(month_data))
        elements.append(Spacer(1, 20))

        # Loan Payment Schedule
        elements.append(Paragraph("Loan Payment Schedule", self.styles['SectionHeader']))
        if loan_summary:
            loan_data = [["Lender", "Loan Type", "Balance", "Payment", "Next Due", "Annual Total"]]
            for loan in loan_summary:
                loan_data.append([
                    loan.get('lender', ''),
                    loan.get('type', ''),
                    f"${loan.get('balance', 0):,.0f}",
                    f"${loan.get('payment', 0):,.0f}",
                    loan.get('next_due', ''),
                    f"${loan.get('annual_total', 0):,.0f}"
                ])
            elements.append(self._create_table(loan_data))

        # Working Capital Position
        elements.append(Spacer(1, 20))
        if summary.get('ending_balance', 0) < 0:
            elements.append(Paragraph(
                f"WARNING: Projected negative cash position of ${abs(summary.get('ending_balance', 0)):,.0f}. "
                "Review financing options.",
                self.styles['Warning']
            ))
        else:
            elements.append(Paragraph(
                f"Cash position is healthy with ${summary.get('ending_balance', 0):,.0f} projected ending balance.",
                self.styles['Success']
            ))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_succession_plan_report(
        self,
        family_members: List[Dict],
        ownership_structure: Dict,
        transfer_plans: List[Dict],
        milestones: List[Dict],
        summary: Dict,
        config: Optional[ReportConfig] = None
    ) -> bytes:
        """Generate succession planning report PDF"""
        if config is None:
            config = ReportConfig(
                title="Farm Succession Plan",
                subtitle="Confidential Planning Document"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.75*inch
        )

        elements = self._create_header(config)

        # Plan Summary
        elements.append(Paragraph("Succession Plan Summary", self.styles['SectionHeader']))
        sum_data = [
            ["Total Farm Assets", f"${summary.get('total_assets', 0):,.0f}"],
            ["Family Members Involved", str(summary.get('family_count', 0))],
            ["Planned Transfers", str(summary.get('transfer_count', 0))],
            ["Target Completion", summary.get('target_date', 'TBD')],
            ["Plan Status", summary.get('status', 'In Progress')],
        ]
        elements.append(self._create_table(sum_data, col_widths=[3*inch, 3*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Current Ownership Structure
        elements.append(Paragraph("Current Ownership Structure", self.styles['SectionHeader']))
        own_data = [
            ["Entity/Structure", ownership_structure.get('entity_type', '')],
            ["Primary Owner(s)", ownership_structure.get('primary_owners', '')],
            ["Ownership %", f"{ownership_structure.get('primary_pct', 0):.0f}%"],
            ["Management", ownership_structure.get('management', '')],
        ]
        elements.append(self._create_table(own_data, col_widths=[2.5*inch, 4*inch], header_row=False))
        elements.append(Spacer(1, 20))

        # Family Members
        elements.append(Paragraph("Family Members", self.styles['SectionHeader']))
        if family_members:
            fam_data = [["Name", "Role", "Age", "Ownership %", "Involvement"]]
            for member in family_members:
                fam_data.append([
                    member.get('name', ''),
                    member.get('role', ''),
                    str(member.get('age', '')),
                    f"{member.get('ownership_pct', 0):.0f}%",
                    member.get('involvement', '')
                ])
            elements.append(self._create_table(fam_data))
        elements.append(Spacer(1, 20))

        # Planned Asset Transfers
        elements.append(Paragraph("Planned Asset Transfers", self.styles['SectionHeader']))
        if transfer_plans:
            transfer_data = [["Asset", "From", "To", "Method", "Value", "Target Date"]]
            for transfer in transfer_plans:
                transfer_data.append([
                    transfer.get('asset', '')[:20],
                    transfer.get('from', ''),
                    transfer.get('to', ''),
                    transfer.get('method', ''),
                    f"${transfer.get('value', 0):,.0f}",
                    transfer.get('target_date', '')
                ])
            elements.append(self._create_table(transfer_data))
        elements.append(Spacer(1, 20))

        # Milestones
        elements.append(Paragraph("Succession Milestones", self.styles['SectionHeader']))
        if milestones:
            mile_data = [["Milestone", "Category", "Target Date", "Status", "Assigned To"]]
            for mile in milestones:
                mile_data.append([
                    mile.get('title', '')[:30],
                    mile.get('category', ''),
                    mile.get('target_date', ''),
                    mile.get('status', ''),
                    mile.get('assigned_to', '')
                ])
            elements.append(self._create_table(mile_data))

        # Important Notes
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Important Notes", self.styles['SectionHeader']))
        notes_text = """
        This succession plan is a working document and should be reviewed regularly with
        legal, tax, and financial advisors. Asset valuations are estimates and should be
        verified before any transfers. Tax implications vary based on transfer method
        and current tax law.
        """
        elements.append(Paragraph(notes_text, self.styles['Normal']))

        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        buffer.seek(0)
        return buffer.getvalue()


# Singleton instance
_pdf_service: Optional[PDFReportService] = None


def get_pdf_report_service() -> PDFReportService:
    """Get singleton PDF report service instance"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFReportService()
    return _pdf_service
