"""
Receipt OCR Service - Invoice and Receipt Data Extraction
AgTools GenFin v6.7.15

Features:
- Multi-provider OCR (Tesseract local, Google Vision, AWS Textract)
- Intelligent receipt/invoice parsing
- Vendor name extraction
- Amount/total detection
- Date parsing
- Line item extraction
- Auto-populate bill/expense forms
"""

import os
import re
import io
import json
import sqlite3
import hashlib
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from PIL import Image
import httpx

# Try to import pytesseract for local OCR
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class OCRProvider(str, Enum):
    TESSERACT = "tesseract"
    GOOGLE_VISION = "google_vision"
    AWS_TEXTRACT = "aws_textract"
    MOCK = "mock"  # For testing


@dataclass
class ExtractedLineItem:
    """Extracted line item from receipt"""
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    confidence: float = 0.0


@dataclass
class ReceiptData:
    """Structured receipt/invoice data"""
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_phone: Optional[str] = None

    receipt_date: Optional[date] = None
    receipt_number: Optional[str] = None

    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None

    payment_method: Optional[str] = None

    line_items: List[ExtractedLineItem] = None

    raw_text: str = ""
    confidence: float = 0.0
    provider: str = ""
    processing_time_ms: int = 0

    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert Decimal to float for JSON
        for key in ['subtotal', 'tax_amount', 'total_amount']:
            if result[key] is not None:
                result[key] = float(result[key])
        # Convert date to string
        if result['receipt_date'] is not None:
            result['receipt_date'] = result['receipt_date'].isoformat()
        # Convert line items
        for item in result['line_items']:
            for k in ['unit_price', 'amount']:
                if item[k] is not None:
                    item[k] = float(item[k])
        return result


class ReceiptOCRService:
    """
    Receipt and Invoice OCR Service

    Extracts structured data from receipt/invoice images for
    automatic population of bills and expenses in GenFin.
    """

    # Common vendor indicators
    VENDOR_INDICATORS = [
        r'^([A-Z][A-Za-z\s&\'-]+(?:Inc|LLC|Co|Corp|Ltd|Store|Farm|Supply)?)\s*$',
        r'(?:welcome to|thank you for shopping at)\s+([A-Za-z\s&\'-]+)',
        r'^store[:\s#]*\d*\s*([A-Za-z\s&\'-]+)',
    ]

    # Amount patterns
    AMOUNT_PATTERNS = [
        r'(?:total|amount due|balance|grand total)[:\s]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'(?:subtotal|sub-total|sub total)[:\s]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
        r'(?:tax|sales tax|hst|gst|vat)[:\s]*\$?\s*(\d+[,.]?\d*\.?\d{0,2})',
    ]

    # Date patterns
    DATE_PATTERNS = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or MM-DD-YYYY
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',    # YYYY-MM-DD
        r'([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})',  # Month DD, YYYY
        r'(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})',    # DD Month YYYY
    ]

    # Line item patterns
    LINE_ITEM_PATTERNS = [
        r'(.+?)\s+(\d+)\s*[@xX]\s*\$?(\d+\.?\d*)\s+\$?(\d+\.?\d*)',  # desc qty @ price amount
        r'(.+?)\s+\$?(\d+\.?\d{2})\s*$',  # desc amount
        r'^(\d+)\s+(.+?)\s+\$?(\d+\.?\d{2})\s*$',  # qty desc amount
    ]

    def __init__(
        self,
        db_path: str = "agtools.db",
        google_api_key: Optional[str] = None,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        uploads_dir: str = "uploads/receipts"
    ):
        """
        Initialize Receipt OCR Service

        Args:
            db_path: Path to SQLite database
            google_api_key: Google Cloud Vision API key
            aws_access_key: AWS access key for Textract
            aws_secret_key: AWS secret key for Textract
            uploads_dir: Directory for storing receipt images
        """
        self.db_path = db_path
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_VISION_API_KEY", "")
        self.aws_access_key = aws_access_key or os.environ.get("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_key = aws_secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY", "")

        self.uploads_dir = Path(uploads_dir)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Initialize database tables for receipt storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipt_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_hash TEXT UNIQUE NOT NULL,
                file_path TEXT NOT NULL,
                vendor_name TEXT,
                receipt_date DATE,
                total_amount REAL,
                tax_amount REAL,
                subtotal REAL,
                receipt_number TEXT,
                raw_text TEXT,
                extracted_data TEXT,
                provider TEXT,
                confidence REAL,
                processing_time_ms INTEGER,
                linked_bill_id INTEGER,
                linked_expense_id INTEGER,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (linked_bill_id) REFERENCES bills(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipt_line_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL,
                unit_price REAL,
                amount REAL,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (receipt_id) REFERENCES receipt_scans(id)
            )
        """)

        conn.commit()
        conn.close()

    def _hash_image(self, image_bytes: bytes) -> str:
        """Generate hash for image deduplication"""
        return hashlib.sha256(image_bytes).hexdigest()[:16]

    def _preprocess_image(self, image_bytes: bytes) -> Image.Image:
        """Preprocess image for better OCR results"""
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize if too large (max 4000px on longest side)
        max_size = 4000
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    async def extract_receipt_data(
        self,
        image_bytes: bytes,
        user_id: Optional[int] = None,
        save_image: bool = True,
        preferred_provider: Optional[OCRProvider] = None
    ) -> ReceiptData:
        """
        Extract structured data from a receipt/invoice image

        Args:
            image_bytes: Raw image bytes
            user_id: User ID for tracking
            save_image: Whether to save the image
            preferred_provider: Preferred OCR provider

        Returns:
            ReceiptData with extracted information
        """
        import time
        start_time = time.time()

        image_hash = self._hash_image(image_bytes)
        image = self._preprocess_image(image_bytes)

        # Try providers in order of preference
        raw_text = ""
        provider_used = OCRProvider.MOCK

        providers_to_try = []
        if preferred_provider:
            providers_to_try.append(preferred_provider)

        # Add fallback providers
        if TESSERACT_AVAILABLE:
            providers_to_try.append(OCRProvider.TESSERACT)
        if self.google_api_key:
            providers_to_try.append(OCRProvider.GOOGLE_VISION)

        for provider in providers_to_try:
            try:
                if provider == OCRProvider.TESSERACT:
                    raw_text = await self._ocr_tesseract(image)
                elif provider == OCRProvider.GOOGLE_VISION:
                    raw_text = await self._ocr_google_vision(image_bytes)

                if raw_text.strip():
                    provider_used = provider
                    break
            except Exception as e:
                print(f"OCR provider {provider} failed: {e}")
                continue

        # Parse the raw text
        receipt_data = self._parse_receipt_text(raw_text)
        receipt_data.raw_text = raw_text
        receipt_data.provider = provider_used.value
        receipt_data.processing_time_ms = int((time.time() - start_time) * 1000)

        # Save to database
        if save_image:
            self._save_receipt(image_bytes, image_hash, receipt_data, user_id)

        return receipt_data

    async def _ocr_tesseract(self, image: Image.Image) -> str:
        """Run OCR using Tesseract"""
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract not available")

        # Configure Tesseract for receipt processing
        custom_config = r'--oem 3 --psm 4'
        text = pytesseract.image_to_string(image, config=custom_config)
        return text

    async def _ocr_google_vision(self, image_bytes: bytes) -> str:
        """Run OCR using Google Cloud Vision API"""
        import base64

        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://vision.googleapis.com/v1/images:annotate?key={self.google_api_key}",
                json={
                    "requests": [{
                        "image": {"content": image_base64},
                        "features": [{"type": "TEXT_DETECTION"}]
                    }]
                }
            )

            if response.status_code == 200:
                result = response.json()
                responses = result.get("responses", [])
                if responses and responses[0].get("textAnnotations"):
                    return responses[0]["textAnnotations"][0].get("description", "")

        return ""

    def _parse_receipt_text(self, text: str) -> ReceiptData:
        """Parse raw OCR text into structured receipt data"""
        lines = text.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]

        receipt = ReceiptData()
        receipt.confidence = 0.5  # Base confidence

        # Extract vendor name (usually first few lines)
        receipt.vendor_name = self._extract_vendor_name(lines[:5])
        if receipt.vendor_name:
            receipt.confidence += 0.1

        # Extract date
        receipt.receipt_date = self._extract_date(text)
        if receipt.receipt_date:
            receipt.confidence += 0.1

        # Extract amounts
        amounts = self._extract_amounts(text)
        receipt.total_amount = amounts.get('total')
        receipt.subtotal = amounts.get('subtotal')
        receipt.tax_amount = amounts.get('tax')
        if receipt.total_amount:
            receipt.confidence += 0.2

        # Extract receipt/invoice number
        receipt.receipt_number = self._extract_receipt_number(text)

        # Extract line items
        receipt.line_items = self._extract_line_items(lines)
        if receipt.line_items:
            receipt.confidence += 0.1

        # Cap confidence at 1.0
        receipt.confidence = min(receipt.confidence, 1.0)

        return receipt

    def _extract_vendor_name(self, top_lines: List[str]) -> Optional[str]:
        """Extract vendor name from top of receipt"""
        for line in top_lines:
            # Skip short lines
            if len(line) < 3:
                continue

            # Skip lines that are mostly numbers
            if sum(c.isdigit() for c in line) > len(line) * 0.5:
                continue

            # Skip common non-vendor lines
            skip_patterns = ['receipt', 'invoice', 'date', 'time', 'tel', 'phone', 'fax']
            if any(pat in line.lower() for pat in skip_patterns):
                continue

            # Check vendor patterns
            for pattern in self.VENDOR_INDICATORS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

            # If line looks like a business name (starts with capital, reasonable length)
            if line[0].isupper() and 3 <= len(line) <= 50:
                return line

        return None

    def _extract_date(self, text: str) -> Optional[date]:
        """Extract date from receipt text"""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)

                # Try various date formats
                formats = [
                    '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
                    '%Y-%m-%d', '%Y/%m/%d',
                    '%B %d, %Y', '%B %d %Y', '%b %d, %Y', '%b %d %Y',
                    '%d %B %Y', '%d %b %Y'
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except ValueError:
                        continue

        return None

    def _extract_amounts(self, text: str) -> Dict[str, Optional[Decimal]]:
        """Extract monetary amounts from receipt"""
        amounts = {
            'total': None,
            'subtotal': None,
            'tax': None
        }

        text_lower = text.lower()

        # Look for total
        total_patterns = [
            r'(?:grand\s+)?total[:\s]*\$?\s*(\d{1,6}[,.]?\d*\.?\d{0,2})',
            r'amount\s+due[:\s]*\$?\s*(\d{1,6}[,.]?\d*\.?\d{0,2})',
            r'balance[:\s]*\$?\s*(\d{1,6}[,.]?\d*\.?\d{0,2})',
        ]

        for pattern in total_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amounts['total'] = Decimal(amount_str)
                    break
                except (InvalidOperation, ValueError):
                    continue

        # Look for subtotal
        subtotal_patterns = [
            r'(?:sub\s*-?\s*total)[:\s]*\$?\s*(\d{1,6}[,.]?\d*\.?\d{0,2})',
        ]

        for pattern in subtotal_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amounts['subtotal'] = Decimal(amount_str)
                    break
                except (InvalidOperation, ValueError):
                    continue

        # Look for tax
        tax_patterns = [
            r'(?:sales\s+)?tax[:\s]*\$?\s*(\d{1,4}[,.]?\d*\.?\d{0,2})',
            r'(?:hst|gst|vat)[:\s]*\$?\s*(\d{1,4}[,.]?\d*\.?\d{0,2})',
        ]

        for pattern in tax_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amounts['tax'] = Decimal(amount_str)
                    break
                except (InvalidOperation, ValueError):
                    continue

        return amounts

    def _extract_receipt_number(self, text: str) -> Optional[str]:
        """Extract receipt/invoice number"""
        patterns = [
            r'(?:receipt|invoice|order|trans(?:action)?)\s*#?\s*:?\s*(\d{4,20})',
            r'#\s*(\d{6,20})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_line_items(self, lines: List[str]) -> List[ExtractedLineItem]:
        """Extract line items from receipt"""
        items = []

        for line in lines:
            # Skip very short lines
            if len(line) < 5:
                continue

            # Skip header/footer lines
            skip_keywords = ['total', 'subtotal', 'tax', 'change', 'cash', 'card',
                           'thank you', 'receipt', 'invoice', 'date', 'time']
            if any(kw in line.lower() for kw in skip_keywords):
                continue

            # Try to parse as line item
            for pattern in self.LINE_ITEM_PATTERNS:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    try:
                        if len(groups) == 4:  # desc qty price amount
                            item = ExtractedLineItem(
                                description=groups[0].strip(),
                                quantity=float(groups[1]),
                                unit_price=Decimal(groups[2]),
                                amount=Decimal(groups[3]),
                                confidence=0.8
                            )
                        elif len(groups) == 2:  # desc amount
                            item = ExtractedLineItem(
                                description=groups[0].strip(),
                                amount=Decimal(groups[1]),
                                confidence=0.6
                            )
                        elif len(groups) == 3:  # qty desc amount
                            item = ExtractedLineItem(
                                description=groups[1].strip(),
                                quantity=float(groups[0]),
                                amount=Decimal(groups[2]),
                                confidence=0.7
                            )
                        else:
                            continue

                        items.append(item)
                        break
                    except (ValueError, InvalidOperation):
                        continue

        return items

    def _save_receipt(
        self,
        image_bytes: bytes,
        image_hash: str,
        receipt_data: ReceiptData,
        user_id: Optional[int]
    ):
        """Save receipt image and data to database"""
        # Save image file
        image_path = self.uploads_dir / f"{image_hash}.jpg"
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(image_path, 'JPEG', quality=90)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO receipt_scans
                (image_hash, file_path, vendor_name, receipt_date, total_amount,
                 tax_amount, subtotal, receipt_number, raw_text, extracted_data,
                 provider, confidence, processing_time_ms, user_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                image_hash,
                str(image_path),
                receipt_data.vendor_name,
                receipt_data.receipt_date.isoformat() if receipt_data.receipt_date else None,
                float(receipt_data.total_amount) if receipt_data.total_amount else None,
                float(receipt_data.tax_amount) if receipt_data.tax_amount else None,
                float(receipt_data.subtotal) if receipt_data.subtotal else None,
                receipt_data.receipt_number,
                receipt_data.raw_text,
                json.dumps(receipt_data.to_dict()),
                receipt_data.provider,
                receipt_data.confidence,
                receipt_data.processing_time_ms,
                user_id,
                datetime.now().isoformat()
            ))

            receipt_id = cursor.lastrowid

            # Save line items
            for item in receipt_data.line_items:
                cursor.execute("""
                    INSERT INTO receipt_line_items
                    (receipt_id, description, quantity, unit_price, amount, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    receipt_id,
                    item.description,
                    item.quantity,
                    float(item.unit_price) if item.unit_price else None,
                    float(item.amount) if item.amount else None,
                    item.confidence
                ))

            conn.commit()
        finally:
            conn.close()

    def get_receipt_by_hash(self, image_hash: str) -> Optional[Dict]:
        """Get previously scanned receipt by image hash"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM receipt_scans WHERE image_hash = ?
        """, (image_hash,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def link_to_bill(self, receipt_id: int, bill_id: int) -> bool:
        """Link a receipt scan to a GenFin bill"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE receipt_scans SET linked_bill_id = ? WHERE id = ?
            """, (bill_id, receipt_id))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def get_recent_scans(self, user_id: Optional[int] = None, limit: int = 20) -> List[Dict]:
        """Get recent receipt scans"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if user_id:
            cursor.execute("""
                SELECT id, image_hash, vendor_name, receipt_date, total_amount,
                       confidence, created_at, linked_bill_id
                FROM receipt_scans
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
        else:
            cursor.execute("""
                SELECT id, image_hash, vendor_name, receipt_date, total_amount,
                       confidence, created_at, linked_bill_id
                FROM receipt_scans
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def list_scans(self, limit: int = 20, offset: int = 0) -> List[Dict]:
        """List receipt scans with pagination"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, image_hash, vendor_name, receipt_date, total_amount,
                   confidence, created_at, linked_bill_id, provider
            FROM receipt_scans
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_scan(self, scan_id: int) -> Optional[Dict]:
        """Get a specific receipt scan by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM receipt_scans WHERE id = ?
        """, (scan_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            result = dict(row)
            # Parse extracted_data JSON if present
            if result.get('extracted_data'):
                try:
                    result['extracted_data'] = json.loads(result['extracted_data'])
                except json.JSONDecodeError:
                    pass
            return result
        return None


class _LazyReceiptOCRService:
    """Lazy-loading wrapper for ReceiptOCRService to avoid initialization at import time"""
    _instance: Optional[ReceiptOCRService] = None

    def __getattr__(self, name):
        if self._instance is None:
            self._instance = ReceiptOCRService()
        return getattr(self._instance, name)


# Module-level singleton (lazy-loaded)
receipt_ocr_service = _LazyReceiptOCRService()


def get_receipt_ocr_service() -> ReceiptOCRService:
    """Get or create Receipt OCR service singleton"""
    if receipt_ocr_service._instance is None:
        receipt_ocr_service._instance = ReceiptOCRService()
    return receipt_ocr_service._instance
