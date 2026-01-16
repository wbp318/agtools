"""
GenFin 1099 Tracking & Reporting Service
Complete 1099 management for vendor payments

Features:
- Track 1099-eligible vendors
- Payment tracking by box type
- 1099-NEC and 1099-MISC generation
- E-filing preparation
- Recipient copy generation
- IRS submission tracking

GenFin v6.3.0
"""

import sqlite3
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal


# ============================================================================
# ENUMS
# ============================================================================

class Form1099Type(str, Enum):
    NEC = "1099-NEC"  # Non-employee compensation
    MISC = "1099-MISC"  # Miscellaneous income
    INT = "1099-INT"  # Interest income
    DIV = "1099-DIV"  # Dividends


class Form1099Status(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    FILED = "filed"
    CORRECTED = "corrected"
    VOIDED = "voided"


class VendorType1099(str, Enum):
    INDIVIDUAL = "individual"
    SOLE_PROPRIETOR = "sole_proprietor"
    PARTNERSHIP = "partnership"
    CORPORATION = "corporation"
    LLC = "llc"
    OTHER = "other"


# ============================================================================
# 1099 BOX DEFINITIONS
# ============================================================================

# 1099-NEC Boxes
NEC_BOXES = {
    1: "Nonemployee compensation",
    4: "Federal income tax withheld"
}

# 1099-MISC Boxes
MISC_BOXES = {
    1: "Rents",
    2: "Royalties",
    3: "Other income",
    4: "Federal income tax withheld",
    5: "Fishing boat proceeds",
    6: "Medical and health care payments",
    7: "Payer made direct sales totaling $5,000 or more",
    8: "Substitute payments in lieu of dividends or interest",
    9: "Crop insurance proceeds",
    10: "Gross proceeds paid to an attorney",
    11: "Fish purchased for resale",
    12: "Section 409A deferrals",
    14: "Excess golden parachute payments",
}

# IRS Threshold for 1099 reporting
IRS_THRESHOLD = 600.00


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class Vendor1099Info(BaseModel):
    """1099 information for a vendor"""
    vendor_id: str
    vendor_name: str
    tax_id: Optional[str] = None
    tax_id_type: str = "EIN"  # EIN or SSN
    vendor_type: VendorType1099 = VendorType1099.INDIVIDUAL
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    is_1099_eligible: bool = True


class Form1099Create(BaseModel):
    """Create a 1099 form"""
    vendor_id: str
    tax_year: int
    form_type: Form1099Type = Form1099Type.NEC
    box_amounts: Dict[int, float] = Field(default_factory=dict)


class Form1099Response(BaseModel):
    """1099 form response"""
    id: int
    vendor_id: str
    vendor_name: str
    tax_id_masked: str  # XXX-XX-1234
    tax_year: int
    form_type: str
    box_amounts: Dict[int, float]
    total_amount: float
    federal_withheld: float
    status: str
    filed_date: Optional[date]
    confirmation_number: Optional[str]
    created_at: datetime


class Filing1099Summary(BaseModel):
    """1099 filing summary"""
    tax_year: int
    total_forms: int
    total_amount: float
    total_withheld: float
    forms_by_type: Dict[str, int]
    status_breakdown: Dict[str, int]


# ============================================================================
# 1099 SERVICE
# ============================================================================

class GenFin1099Service:
    """Service for 1099 tracking and generation"""

    def __init__(self, db_path: str = "agtools.db"):
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize 1099 tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1099 Forms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genfin_1099_forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER DEFAULT 1,
                vendor_id VARCHAR(50) NOT NULL,
                vendor_name VARCHAR(200) NOT NULL,
                tax_id VARCHAR(20),
                tax_id_type VARCHAR(10) DEFAULT 'EIN',
                vendor_type VARCHAR(50) DEFAULT 'individual',
                address_line1 VARCHAR(200),
                address_line2 VARCHAR(200),
                city VARCHAR(100),
                state VARCHAR(2),
                zip_code VARCHAR(20),
                tax_year INTEGER NOT NULL,
                form_type VARCHAR(20) DEFAULT '1099-NEC',
                box_amounts TEXT,
                total_amount DECIMAL(15,2) DEFAULT 0,
                federal_withheld DECIMAL(15,2) DEFAULT 0,
                state_withheld DECIMAL(15,2) DEFAULT 0,
                state_id VARCHAR(20),
                status VARCHAR(20) DEFAULT 'draft',
                filed_date DATE,
                confirmation_number VARCHAR(50),
                corrected_form_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 1099 Payment tracking (links payments to 1099 boxes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genfin_1099_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id VARCHAR(50) NOT NULL,
                payment_id VARCHAR(50),
                payment_date DATE NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                form_type VARCHAR(20) DEFAULT '1099-NEC',
                box_number INTEGER DEFAULT 1,
                description TEXT,
                tax_year INTEGER NOT NULL,
                included_in_form_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (included_in_form_id) REFERENCES genfin_1099_forms(id)
            )
        """)

        # Filing batches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genfin_1099_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER DEFAULT 1,
                tax_year INTEGER NOT NULL,
                form_type VARCHAR(20),
                form_count INTEGER DEFAULT 0,
                total_amount DECIMAL(15,2) DEFAULT 0,
                submission_type VARCHAR(20) DEFAULT 'electronic',
                filed_date DATE,
                confirmation_number VARCHAR(50),
                status VARCHAR(20) DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # ========================================================================
    # PAYMENT TRACKING
    # ========================================================================

    def record_1099_payment(
        self,
        vendor_id: str,
        amount: float,
        payment_date: date,
        form_type: Form1099Type = Form1099Type.NEC,
        box_number: int = 1,
        payment_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tuple[Optional[int], Optional[str]]:
        """Record a payment that should be included on a 1099"""
        conn = self._get_connection()
        cursor = conn.cursor()

        tax_year = payment_date.year

        try:
            cursor.execute("""
                INSERT INTO genfin_1099_payments (
                    vendor_id, payment_id, payment_date, amount, form_type,
                    box_number, description, tax_year
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vendor_id, payment_id, payment_date.isoformat(), amount,
                form_type.value, box_number, description, tax_year
            ))

            payment_record_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return payment_record_id, None

        except Exception as e:
            conn.close()
            return None, str(e)

    def get_vendor_1099_payments(
        self,
        vendor_id: str,
        tax_year: int
    ) -> List[Dict]:
        """Get all 1099 payments for a vendor in a tax year"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM genfin_1099_payments
            WHERE vendor_id = ? AND tax_year = ?
            ORDER BY payment_date
        """, (vendor_id, tax_year))

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row["id"],
            "payment_id": row["payment_id"],
            "payment_date": row["payment_date"],
            "amount": float(row["amount"]),
            "form_type": row["form_type"],
            "box_number": row["box_number"],
            "description": row["description"]
        } for row in rows]

    # ========================================================================
    # 1099 FORM GENERATION
    # ========================================================================

    def generate_1099_forms(
        self,
        tax_year: int,
        entity_id: int = 1,
        vendor_ids: Optional[List[str]] = None
    ) -> Tuple[List[int], Optional[str]]:
        """Generate 1099 forms from payment records"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get all vendors with payments meeting threshold
        query = """
            SELECT vendor_id, form_type, SUM(amount) as total
            FROM genfin_1099_payments
            WHERE tax_year = ?
        """
        params = [tax_year]

        if vendor_ids:
            placeholders = ",".join("?" * len(vendor_ids))
            query += f" AND vendor_id IN ({placeholders})"
            params.extend(vendor_ids)

        query += " GROUP BY vendor_id, form_type HAVING total >= ?"
        params.append(IRS_THRESHOLD)

        cursor.execute(query, params)
        vendor_totals = cursor.fetchall()

        form_ids = []

        for vt in vendor_totals:
            vendor_id = vt["vendor_id"]
            form_type = vt["form_type"]

            # Get box-level breakdown
            cursor.execute("""
                SELECT box_number, SUM(amount) as box_total
                FROM genfin_1099_payments
                WHERE vendor_id = ? AND tax_year = ? AND form_type = ?
                GROUP BY box_number
            """, (vendor_id, tax_year, form_type))

            box_amounts = {}
            for box_row in cursor.fetchall():
                box_amounts[box_row["box_number"]] = float(box_row["box_total"])

            # Check if form already exists
            cursor.execute("""
                SELECT id FROM genfin_1099_forms
                WHERE vendor_id = ? AND tax_year = ? AND form_type = ?
                AND status NOT IN ('voided', 'corrected')
            """, (vendor_id, tax_year, form_type))

            existing = cursor.fetchone()

            if existing:
                # Update existing form
                import json
                cursor.execute("""
                    UPDATE genfin_1099_forms SET
                        box_amounts = ?,
                        total_amount = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    json.dumps(box_amounts),
                    float(vt["total"]),
                    datetime.now().isoformat(),
                    existing["id"]
                ))
                form_ids.append(existing["id"])
            else:
                # Create new form
                # Try to get vendor info from payables service
                vendor_name = vendor_id  # Default to vendor_id
                tax_id = None
                address = {}

                import json
                cursor.execute("""
                    INSERT INTO genfin_1099_forms (
                        entity_id, vendor_id, vendor_name, tax_year, form_type,
                        box_amounts, total_amount, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'draft')
                """, (
                    entity_id, vendor_id, vendor_name, tax_year, form_type,
                    json.dumps(box_amounts), float(vt["total"])
                ))

                form_ids.append(cursor.lastrowid)

        conn.commit()
        conn.close()

        return form_ids, None

    def get_1099_form(self, form_id: int) -> Optional[Form1099Response]:
        """Get a 1099 form by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM genfin_1099_forms WHERE id = ?", (form_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_form(row)

    def list_1099_forms(
        self,
        tax_year: int,
        entity_id: int = 1,
        form_type: Optional[Form1099Type] = None,
        status: Optional[Form1099Status] = None
    ) -> List[Form1099Response]:
        """List 1099 forms"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM genfin_1099_forms WHERE tax_year = ? AND entity_id = ?"
        params = [tax_year, entity_id]

        if form_type:
            query += " AND form_type = ?"
            params.append(form_type.value)

        if status:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY vendor_name"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_form(row) for row in rows]

    def update_1099_form(
        self,
        form_id: int,
        vendor_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        address_line1: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        box_amounts: Optional[Dict[int, float]] = None
    ) -> Tuple[Optional[Form1099Response], Optional[str]]:
        """Update a 1099 form"""
        conn = self._get_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if vendor_name:
            updates.append("vendor_name = ?")
            params.append(vendor_name)
        if tax_id:
            updates.append("tax_id = ?")
            params.append(tax_id)
        if address_line1:
            updates.append("address_line1 = ?")
            params.append(address_line1)
        if city:
            updates.append("city = ?")
            params.append(city)
        if state:
            updates.append("state = ?")
            params.append(state)
        if zip_code:
            updates.append("zip_code = ?")
            params.append(zip_code)
        if box_amounts:
            import json
            updates.append("box_amounts = ?")
            params.append(json.dumps(box_amounts))
            total = sum(v for k, v in box_amounts.items() if k != 4)  # Box 4 is withholding
            updates.append("total_amount = ?")
            params.append(total)
            if 4 in box_amounts:
                updates.append("federal_withheld = ?")
                params.append(box_amounts[4])

        if not updates:
            conn.close()
            return None, "No fields to update"

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(form_id)

        try:
            cursor.execute(f"""
                UPDATE genfin_1099_forms SET {", ".join(updates)} WHERE id = ?
            """, params)

            conn.commit()
            conn.close()

            return self.get_1099_form(form_id), None

        except Exception as e:
            conn.close()
            return None, str(e)

    def mark_form_ready(self, form_id: int) -> Tuple[bool, Optional[str]]:
        """Mark a 1099 form as ready for filing"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify form has required info
        cursor.execute("SELECT * FROM genfin_1099_forms WHERE id = ?", (form_id,))
        form = cursor.fetchone()

        if not form:
            conn.close()
            return False, "Form not found"

        if not form["tax_id"]:
            conn.close()
            return False, "Tax ID is required"

        if not form["vendor_name"]:
            conn.close()
            return False, "Vendor name is required"

        cursor.execute("""
            UPDATE genfin_1099_forms SET status = 'ready', updated_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), form_id))

        conn.commit()
        conn.close()

        return True, None

    def file_forms(
        self,
        form_ids: List[int],
        confirmation_number: str
    ) -> Tuple[bool, Optional[str]]:
        """Mark forms as filed with IRS"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            placeholders = ",".join("?" * len(form_ids))
            cursor.execute(f"""
                UPDATE genfin_1099_forms SET
                    status = 'filed',
                    filed_date = ?,
                    confirmation_number = ?,
                    updated_at = ?
                WHERE id IN ({placeholders})
            """, [date.today().isoformat(), confirmation_number,
                  datetime.now().isoformat()] + form_ids)

            conn.commit()
            conn.close()

            return True, None

        except Exception as e:
            conn.close()
            return False, str(e)

    def _row_to_form(self, row: sqlite3.Row) -> Form1099Response:
        """Convert row to Form1099Response"""
        import json

        box_amounts = {}
        if row["box_amounts"]:
            try:
                box_amounts = {int(k): v for k, v in json.loads(row["box_amounts"]).items()}
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                # Invalid JSON or data format, use empty dict
                pass

        # Mask tax ID
        tax_id = row["tax_id"] or ""
        if len(tax_id) >= 4:
            tax_id_masked = f"XXX-XX-{tax_id[-4:]}"
        else:
            tax_id_masked = "Not provided"

        return Form1099Response(
            id=row["id"],
            vendor_id=row["vendor_id"],
            vendor_name=row["vendor_name"],
            tax_id_masked=tax_id_masked,
            tax_year=row["tax_year"],
            form_type=row["form_type"],
            box_amounts=box_amounts,
            total_amount=float(row["total_amount"] or 0),
            federal_withheld=float(row["federal_withheld"] or 0),
            status=row["status"],
            filed_date=date.fromisoformat(row["filed_date"]) if row["filed_date"] else None,
            confirmation_number=row["confirmation_number"],
            created_at=row["created_at"]
        )

    # ========================================================================
    # REPORTS
    # ========================================================================

    def get_1099_summary(self, tax_year: int, entity_id: int = 1) -> Dict:
        """Get summary of 1099 forms for a tax year"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Form counts by type
        cursor.execute("""
            SELECT form_type, COUNT(*) as count, SUM(total_amount) as total
            FROM genfin_1099_forms
            WHERE tax_year = ? AND entity_id = ? AND status != 'voided'
            GROUP BY form_type
        """, (tax_year, entity_id))

        forms_by_type = {}
        total_amount = 0
        total_forms = 0

        for row in cursor.fetchall():
            forms_by_type[row["form_type"]] = {
                "count": row["count"],
                "total": float(row["total"] or 0)
            }
            total_forms += row["count"]
            total_amount += float(row["total"] or 0)

        # Status breakdown
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM genfin_1099_forms
            WHERE tax_year = ? AND entity_id = ?
            GROUP BY status
        """, (tax_year, entity_id))

        status_breakdown = {row["status"]: row["count"] for row in cursor.fetchall()}

        # Total withheld
        cursor.execute("""
            SELECT SUM(federal_withheld) as total
            FROM genfin_1099_forms
            WHERE tax_year = ? AND entity_id = ? AND status != 'voided'
        """, (tax_year, entity_id))

        total_withheld = float(cursor.fetchone()["total"] or 0)

        conn.close()

        return {
            "tax_year": tax_year,
            "entity_id": entity_id,
            "total_forms": total_forms,
            "total_amount": total_amount,
            "total_withheld": total_withheld,
            "forms_by_type": forms_by_type,
            "status_breakdown": status_breakdown,
            "irs_deadline": f"{tax_year + 1}-01-31",  # January 31 following tax year
            "recipient_deadline": f"{tax_year + 1}-01-31"
        }

    def get_vendors_needing_1099(self, tax_year: int, entity_id: int = 1) -> List[Dict]:
        """Get vendors who need 1099s but don't have forms yet"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Vendors with payments over threshold but no form
        cursor.execute("""
            SELECT p.vendor_id, SUM(p.amount) as total
            FROM genfin_1099_payments p
            LEFT JOIN genfin_1099_forms f ON p.vendor_id = f.vendor_id
                AND p.tax_year = f.tax_year AND f.status != 'voided'
            WHERE p.tax_year = ? AND f.id IS NULL
            GROUP BY p.vendor_id
            HAVING total >= ?
        """, (tax_year, IRS_THRESHOLD))

        vendors = []
        for row in cursor.fetchall():
            vendors.append({
                "vendor_id": row["vendor_id"],
                "total_payments": float(row["total"]),
                "needs_form": True
            })

        conn.close()

        return vendors

    def get_vendors_missing_info(self, tax_year: int, entity_id: int = 1) -> List[Dict]:
        """Get 1099 forms missing required information"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM genfin_1099_forms
            WHERE tax_year = ? AND entity_id = ?
            AND status = 'draft'
            AND (tax_id IS NULL OR tax_id = '' OR vendor_name IS NULL)
        """, (tax_year, entity_id))

        forms = []
        for row in cursor.fetchall():
            missing = []
            if not row["tax_id"]:
                missing.append("Tax ID")
            if not row["vendor_name"]:
                missing.append("Vendor name")
            if not row["address_line1"]:
                missing.append("Address")

            forms.append({
                "form_id": row["id"],
                "vendor_id": row["vendor_id"],
                "vendor_name": row["vendor_name"] or "Unknown",
                "total_amount": float(row["total_amount"] or 0),
                "missing_fields": missing
            })

        conn.close()

        return forms

    # ========================================================================
    # SERVICE SUMMARY
    # ========================================================================

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        conn = self._get_connection()
        cursor = conn.cursor()

        current_year = date.today().year

        cursor.execute("""
            SELECT COUNT(*) FROM genfin_1099_forms WHERE tax_year = ?
        """, (current_year,))
        current_year_forms = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM genfin_1099_forms WHERE status = 'filed'
        """)
        total_filed = cursor.fetchone()[0]

        conn.close()

        return {
            "service": "GenFin 1099 Tracking",
            "version": "6.3.0",
            "current_year_forms": current_year_forms,
            "total_filed_forms": total_filed,
            "irs_threshold": IRS_THRESHOLD,
            "supported_forms": ["1099-NEC", "1099-MISC"],
            "features": [
                "1099 payment tracking",
                "Automatic form generation",
                "1099-NEC and 1099-MISC support",
                "Missing info detection",
                "Filing status tracking",
                "IRS threshold monitoring"
            ]
        }


# ============================================================================
# SINGLETON
# ============================================================================

_1099_service: Optional[GenFin1099Service] = None


def get_1099_service(db_path: str = "agtools.db") -> GenFin1099Service:
    """Get or create 1099 service singleton"""
    global _1099_service
    if _1099_service is None:
        _1099_service = GenFin1099Service(db_path)
    return _1099_service
