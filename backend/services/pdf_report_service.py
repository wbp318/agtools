"""
PDF Report Generation Service
Generates professional PDF reports for scouting, spray recommendations, costs, etc.
"""

import io
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
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


class ReportType(str, Enum):
    SCOUTING = "scouting"
    SPRAY_RECOMMENDATION = "spray_recommendation"
    FIELD_OPERATIONS = "field_operations"
    COST_PER_ACRE = "cost_per_acre"
    PROFITABILITY = "profitability"
    EQUIPMENT_STATUS = "equipment_status"
    INVENTORY_STATUS = "inventory_status"


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


# Singleton instance
_pdf_service: Optional[PDFReportService] = None


def get_pdf_report_service() -> PDFReportService:
    """Get singleton PDF report service instance"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFReportService()
    return _pdf_service
