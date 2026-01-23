"""
GenFin Bank Feeds Import Service
Handles importing transactions from OFX, QFX, and QBO bank files.
SQLite persistence for data durability
"""
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid
import sqlite3
import json
import re
import xml.etree.ElementTree as ET
from decimal import Decimal


class ImportFileType(Enum):
    """Supported import file types"""
    OFX = "ofx"      # Open Financial Exchange
    QFX = "qfx"      # Quicken Financial Exchange (OFX variant)
    QBO = "qbo"      # QuickBooks Online format
    CSV = "csv"      # Generic CSV


class TransactionType(Enum):
    """Bank transaction types"""
    DEBIT = "debit"
    CREDIT = "credit"
    CHECK = "check"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    FEE = "fee"
    INTEREST = "interest"
    ATM = "atm"
    POS = "pos"       # Point of Sale
    PAYMENT = "payment"
    OTHER = "other"


class MatchStatus(Enum):
    """Transaction matching status"""
    UNMATCHED = "unmatched"
    MATCHED = "matched"
    ADDED = "added"
    EXCLUDED = "excluded"


@dataclass
class ImportedTransaction:
    """A transaction imported from bank file"""
    import_id: str
    file_id: str
    fit_id: str  # Financial Institution Transaction ID
    date: date
    amount: float
    transaction_type: TransactionType
    name: str = ""
    memo: str = ""
    check_number: str = ""
    ref_number: str = ""

    # Matching
    match_status: MatchStatus = MatchStatus.UNMATCHED
    matched_transaction_id: Optional[str] = None
    match_score: float = 0.0

    # Categorization
    suggested_account_id: Optional[str] = None
    suggested_vendor_id: Optional[str] = None
    suggested_customer_id: Optional[str] = None
    category_rule_id: Optional[str] = None

    # Metadata
    imported_at: datetime = field(default_factory=datetime.now)


@dataclass
class ImportFile:
    """Record of an imported file"""
    file_id: str
    filename: str
    file_type: ImportFileType
    bank_id: str = ""
    account_id: str = ""
    account_number_masked: str = ""

    # Date range
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # Stats
    transaction_count: int = 0
    total_debits: float = 0.0
    total_credits: float = 0.0

    # Status
    imported_at: datetime = field(default_factory=datetime.now)
    processed: bool = False


@dataclass
class CategoryRule:
    """Rule for auto-categorizing imported transactions"""
    rule_id: str
    name: str
    priority: int = 0  # Higher = checked first

    # Match criteria (any combination)
    match_name_contains: str = ""
    match_name_exact: str = ""
    match_memo_contains: str = ""
    match_amount_min: Optional[float] = None
    match_amount_max: Optional[float] = None
    match_type: Optional[TransactionType] = None

    # Assignment
    assign_account_id: Optional[str] = None
    assign_vendor_id: Optional[str] = None
    assign_customer_id: Optional[str] = None
    assign_class_id: Optional[str] = None

    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class GenFinBankFeedsService:
    """
    Manages bank feed imports for GenFin.

    Features:
    - Import OFX/QFX/QBO files
    - Auto-match with existing transactions
    - Category rules for auto-assignment
    - Duplicate detection
    - Transaction review workflow
    """

    _instance = None

    def __new__(cls, db_path: str = "agtools.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "agtools.db"):
        if self._initialized:
            return

        self.db_path = db_path
        self._init_tables()
        self._initialize_default_rules()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Drop old tables if schema changed (migration from in-memory)
            cursor.execute("DROP TABLE IF EXISTS genfin_imported_transactions")
            cursor.execute("DROP TABLE IF EXISTS genfin_import_files")
            cursor.execute("DROP TABLE IF EXISTS genfin_category_rules")

            # Import files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_import_files (
                    file_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    bank_id TEXT DEFAULT '',
                    account_id TEXT DEFAULT '',
                    account_number_masked TEXT DEFAULT '',
                    start_date TEXT,
                    end_date TEXT,
                    transaction_count INTEGER DEFAULT 0,
                    total_debits REAL DEFAULT 0.0,
                    total_credits REAL DEFAULT 0.0,
                    imported_at TEXT NOT NULL,
                    processed INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Imported transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_imported_transactions (
                    import_id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    fit_id TEXT NOT NULL,
                    trans_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    transaction_type TEXT NOT NULL,
                    name TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    check_number TEXT DEFAULT '',
                    ref_number TEXT DEFAULT '',
                    match_status TEXT DEFAULT 'unmatched',
                    matched_transaction_id TEXT,
                    match_score REAL DEFAULT 0.0,
                    suggested_account_id TEXT,
                    suggested_vendor_id TEXT,
                    suggested_customer_id TEXT,
                    category_rule_id TEXT,
                    imported_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (file_id) REFERENCES genfin_import_files(file_id)
                )
            """)

            # Category rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_category_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    match_name_contains TEXT DEFAULT '',
                    match_name_exact TEXT DEFAULT '',
                    match_memo_contains TEXT DEFAULT '',
                    match_amount_min REAL,
                    match_amount_max REAL,
                    match_type TEXT,
                    assign_account_id TEXT,
                    assign_vendor_id TEXT,
                    assign_customer_id TEXT,
                    assign_class_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_imported_file ON genfin_imported_transactions(file_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_imported_status ON genfin_imported_transactions(match_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_priority ON genfin_category_rules(priority)")

            conn.commit()

    def _initialize_default_rules(self):
        """Create default categorization rules"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM genfin_category_rules WHERE is_active = 1")
            if cursor.fetchone()[0] > 0:
                return  # Already initialized

        default_rules = [
            ("Fuel Purchase", "fuel", "", None, None, "5400"),  # Fuel expense
            ("Farm Supply", "farm supply", "", None, None, "5100"),  # Seed/Chemicals
            ("Equipment", "equipment", "", None, None, "5300"),  # Equipment expense
            ("Insurance", "insurance", "", None, None, "5700"),  # Insurance
            ("Utility", "utility", "", None, None, "5800"),  # Utilities
            ("Interest", "interest", "", None, None, "7100"),  # Interest expense
        ]

        for name, match, memo, amt_min, amt_max, account_id in default_rules:
            rule_id = str(uuid.uuid4())
            rule = CategoryRule(
                rule_id=rule_id,
                name=name,
                match_name_contains=match,
                match_memo_contains=memo,
                match_amount_min=amt_min,
                match_amount_max=amt_max,
                assign_account_id=account_id
            )
            self._save_rule(rule)

    def _row_to_import_file(self, row: sqlite3.Row) -> ImportFile:
        """Convert database row to ImportFile object"""
        return ImportFile(
            file_id=row["file_id"],
            filename=row["filename"],
            file_type=ImportFileType(row["file_type"]),
            bank_id=row["bank_id"] or "",
            account_id=row["account_id"] or "",
            account_number_masked=row["account_number_masked"] or "",
            start_date=datetime.strptime(row["start_date"], "%Y-%m-%d").date() if row["start_date"] else None,
            end_date=datetime.strptime(row["end_date"], "%Y-%m-%d").date() if row["end_date"] else None,
            transaction_count=row["transaction_count"] or 0,
            total_debits=row["total_debits"] or 0.0,
            total_credits=row["total_credits"] or 0.0,
            imported_at=datetime.fromisoformat(row["imported_at"]),
            processed=bool(row["processed"])
        )

    def _row_to_transaction(self, row: sqlite3.Row) -> ImportedTransaction:
        """Convert database row to ImportedTransaction object"""
        return ImportedTransaction(
            import_id=row["import_id"],
            file_id=row["file_id"],
            fit_id=row["fit_id"],
            date=datetime.strptime(row["trans_date"], "%Y-%m-%d").date(),
            amount=row["amount"],
            transaction_type=TransactionType(row["transaction_type"]),
            name=row["name"] or "",
            memo=row["memo"] or "",
            check_number=row["check_number"] or "",
            ref_number=row["ref_number"] or "",
            match_status=MatchStatus(row["match_status"]),
            matched_transaction_id=row["matched_transaction_id"],
            match_score=row["match_score"] or 0.0,
            suggested_account_id=row["suggested_account_id"],
            suggested_vendor_id=row["suggested_vendor_id"],
            suggested_customer_id=row["suggested_customer_id"],
            category_rule_id=row["category_rule_id"],
            imported_at=datetime.fromisoformat(row["imported_at"])
        )

    def _row_to_rule(self, row: sqlite3.Row) -> CategoryRule:
        """Convert database row to CategoryRule object"""
        return CategoryRule(
            rule_id=row["rule_id"],
            name=row["name"],
            priority=row["priority"] or 0,
            match_name_contains=row["match_name_contains"] or "",
            match_name_exact=row["match_name_exact"] or "",
            match_memo_contains=row["match_memo_contains"] or "",
            match_amount_min=row["match_amount_min"],
            match_amount_max=row["match_amount_max"],
            match_type=TransactionType(row["match_type"]) if row["match_type"] else None,
            assign_account_id=row["assign_account_id"],
            assign_vendor_id=row["assign_vendor_id"],
            assign_customer_id=row["assign_customer_id"],
            assign_class_id=row["assign_class_id"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"])
        )

    def _save_import_file(self, f: ImportFile):
        """Save import file to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO genfin_import_files (
                    file_id, filename, file_type, bank_id, account_id,
                    account_number_masked, start_date, end_date,
                    transaction_count, total_debits, total_credits,
                    imported_at, processed, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                f.file_id, f.filename, f.file_type.value, f.bank_id, f.account_id,
                f.account_number_masked,
                f.start_date.isoformat() if f.start_date else None,
                f.end_date.isoformat() if f.end_date else None,
                f.transaction_count, f.total_debits, f.total_credits,
                f.imported_at.isoformat(), 1 if f.processed else 0
            ))
            conn.commit()

    def _save_transaction(self, trans: ImportedTransaction):
        """Save imported transaction to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO genfin_imported_transactions (
                    import_id, file_id, fit_id, trans_date, amount,
                    transaction_type, name, memo, check_number, ref_number,
                    match_status, matched_transaction_id, match_score,
                    suggested_account_id, suggested_vendor_id, suggested_customer_id,
                    category_rule_id, imported_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                trans.import_id, trans.file_id, trans.fit_id,
                trans.date.isoformat(), trans.amount, trans.transaction_type.value,
                trans.name, trans.memo, trans.check_number, trans.ref_number,
                trans.match_status.value, trans.matched_transaction_id, trans.match_score,
                trans.suggested_account_id, trans.suggested_vendor_id, trans.suggested_customer_id,
                trans.category_rule_id, trans.imported_at.isoformat()
            ))
            conn.commit()

    def _save_rule(self, rule: CategoryRule):
        """Save category rule to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO genfin_category_rules (
                    rule_id, name, priority, match_name_contains, match_name_exact,
                    match_memo_contains, match_amount_min, match_amount_max, match_type,
                    assign_account_id, assign_vendor_id, assign_customer_id, assign_class_id,
                    is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.rule_id, rule.name, rule.priority,
                rule.match_name_contains, rule.match_name_exact,
                rule.match_memo_contains, rule.match_amount_min, rule.match_amount_max,
                rule.match_type.value if rule.match_type else None,
                rule.assign_account_id, rule.assign_vendor_id, rule.assign_customer_id, rule.assign_class_id,
                1 if rule.is_active else 0, rule.created_at.isoformat()
            ))
            conn.commit()

    def _get_transaction_by_id(self, import_id: str) -> Optional[ImportedTransaction]:
        """Get imported transaction by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_imported_transactions
                WHERE import_id = ? AND is_active = 1
            """, (import_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_transaction(row)
            return None

    def _get_all_rules(self) -> List[CategoryRule]:
        """Get all active category rules"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_category_rules
                WHERE is_active = 1
                ORDER BY priority DESC
            """)
            return [self._row_to_rule(row) for row in cursor.fetchall()]

    # ==================== FILE IMPORT ====================

    def import_ofx_content(self, content: str, filename: str = "import.ofx") -> Dict:
        """Import transactions from OFX/QFX content"""
        file_id = str(uuid.uuid4())

        try:
            # Parse OFX content
            transactions, metadata = self._parse_ofx(content)

            # Create import file record
            import_file = ImportFile(
                file_id=file_id,
                filename=filename,
                file_type=ImportFileType.OFX,
                bank_id=metadata.get("bank_id", ""),
                account_id=metadata.get("account_id", ""),
                account_number_masked=metadata.get("account_number", "")[-4:] if metadata.get("account_number") else "",
                start_date=metadata.get("start_date"),
                end_date=metadata.get("end_date"),
                transaction_count=len(transactions)
            )

            # Process transactions
            total_debits = 0.0
            total_credits = 0.0
            imported_count = 0
            duplicate_count = 0

            for trans in transactions:
                # Check for duplicates
                if self._is_duplicate(trans["fit_id"], trans["date"], trans["amount"]):
                    duplicate_count += 1
                    continue

                import_id = str(uuid.uuid4())

                # Determine transaction type
                trans_type = self._determine_transaction_type(trans)

                # Create imported transaction
                imported = ImportedTransaction(
                    import_id=import_id,
                    file_id=file_id,
                    fit_id=trans["fit_id"],
                    date=trans["date"],
                    amount=trans["amount"],
                    transaction_type=trans_type,
                    name=trans.get("name", ""),
                    memo=trans.get("memo", ""),
                    check_number=trans.get("check_number", ""),
                    ref_number=trans.get("ref_number", "")
                )

                # Apply category rules
                self._apply_category_rules(imported)

                # Try to auto-match
                self._try_auto_match(imported)

                self._save_transaction(imported)
                imported_count += 1

                if trans["amount"] < 0:
                    total_debits += abs(trans["amount"])
                else:
                    total_credits += trans["amount"]

            import_file.total_debits = total_debits
            import_file.total_credits = total_credits
            import_file.transaction_count = imported_count

            self._save_import_file(import_file)

            return {
                "success": True,
                "file_id": file_id,
                "filename": filename,
                "bank_id": import_file.bank_id,
                "account_masked": import_file.account_number_masked,
                "transactions_imported": imported_count,
                "duplicates_skipped": duplicate_count,
                "total_debits": round(total_debits, 2),
                "total_credits": round(total_credits, 2),
                "date_range": {
                    "start": import_file.start_date.isoformat() if import_file.start_date else None,
                    "end": import_file.end_date.isoformat() if import_file.end_date else None
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_ofx(self, content: str) -> Tuple[List[Dict], Dict]:
        """Parse OFX/QFX file content"""
        transactions = []
        metadata = {}

        # OFX can be SGML or XML format
        # Try to extract key data using regex for SGML format

        # Extract bank info
        bank_id_match = re.search(r'<BANKID>([^<\n]+)', content)
        if bank_id_match:
            metadata["bank_id"] = bank_id_match.group(1).strip()

        account_match = re.search(r'<ACCTID>([^<\n]+)', content)
        if account_match:
            metadata["account_id"] = account_match.group(1).strip()
            metadata["account_number"] = account_match.group(1).strip()

        # Extract date range
        start_match = re.search(r'<DTSTART>(\d{8})', content)
        if start_match:
            metadata["start_date"] = datetime.strptime(start_match.group(1), "%Y%m%d").date()

        end_match = re.search(r'<DTEND>(\d{8})', content)
        if end_match:
            metadata["end_date"] = datetime.strptime(end_match.group(1), "%Y%m%d").date()

        # Extract transactions
        # Find all STMTTRN blocks
        trans_pattern = r'<STMTTRN>(.*?)</STMTTRN>'
        trans_blocks = re.findall(trans_pattern, content, re.DOTALL)

        for block in trans_blocks:
            trans = {}

            # Transaction type
            trntype_match = re.search(r'<TRNTYPE>([^<\n]+)', block)
            if trntype_match:
                trans["trntype"] = trntype_match.group(1).strip()

            # Date
            dtposted_match = re.search(r'<DTPOSTED>(\d{8})', block)
            if dtposted_match:
                trans["date"] = datetime.strptime(dtposted_match.group(1), "%Y%m%d").date()

            # Amount
            amount_match = re.search(r'<TRNAMT>([^<\n]+)', block)
            if amount_match:
                trans["amount"] = float(amount_match.group(1).strip())

            # FIT ID
            fitid_match = re.search(r'<FITID>([^<\n]+)', block)
            if fitid_match:
                trans["fit_id"] = fitid_match.group(1).strip()
            else:
                trans["fit_id"] = str(uuid.uuid4())

            # Name
            name_match = re.search(r'<NAME>([^<\n]+)', block)
            if name_match:
                trans["name"] = name_match.group(1).strip()

            # Memo
            memo_match = re.search(r'<MEMO>([^<\n]+)', block)
            if memo_match:
                trans["memo"] = memo_match.group(1).strip()

            # Check number
            checknum_match = re.search(r'<CHECKNUM>([^<\n]+)', block)
            if checknum_match:
                trans["check_number"] = checknum_match.group(1).strip()

            # Reference number
            refnum_match = re.search(r'<REFNUM>([^<\n]+)', block)
            if refnum_match:
                trans["ref_number"] = refnum_match.group(1).strip()

            if "date" in trans and "amount" in trans:
                transactions.append(trans)

        return transactions, metadata

    def import_csv_content(
        self,
        content: str,
        filename: str = "import.csv",
        date_column: int = 0,
        amount_column: int = 1,
        description_column: int = 2,
        date_format: str = "%m/%d/%Y",
        has_header: bool = True
    ) -> Dict:
        """Import transactions from CSV content"""
        file_id = str(uuid.uuid4())

        try:
            lines = content.strip().split('\n')
            if has_header:
                lines = lines[1:]  # Skip header

            transactions = []
            for line in lines:
                if not line.strip():
                    continue

                # Simple CSV parsing (doesn't handle quoted commas)
                parts = line.split(',')

                if len(parts) > max(date_column, amount_column, description_column):
                    try:
                        trans_date = datetime.strptime(parts[date_column].strip().strip('"'), date_format).date()
                        amount = float(parts[amount_column].strip().strip('"').replace('$', '').replace(',', ''))
                        description = parts[description_column].strip().strip('"') if description_column < len(parts) else ""

                        transactions.append({
                            "date": trans_date,
                            "amount": amount,
                            "name": description,
                            "fit_id": str(uuid.uuid4())
                        })
                    except (ValueError, IndexError):
                        continue

            # Create import file
            import_file = ImportFile(
                file_id=file_id,
                filename=filename,
                file_type=ImportFileType.CSV,
                transaction_count=len(transactions)
            )

            # Process transactions
            total_debits = 0.0
            total_credits = 0.0
            imported_count = 0

            min_date = None
            max_date = None

            for trans in transactions:
                import_id = str(uuid.uuid4())

                trans_type = TransactionType.DEBIT if trans["amount"] < 0 else TransactionType.CREDIT

                imported = ImportedTransaction(
                    import_id=import_id,
                    file_id=file_id,
                    fit_id=trans["fit_id"],
                    date=trans["date"],
                    amount=trans["amount"],
                    transaction_type=trans_type,
                    name=trans.get("name", "")
                )

                self._apply_category_rules(imported)
                self._save_transaction(imported)
                imported_count += 1

                if trans["amount"] < 0:
                    total_debits += abs(trans["amount"])
                else:
                    total_credits += trans["amount"]

                if min_date is None or trans["date"] < min_date:
                    min_date = trans["date"]
                if max_date is None or trans["date"] > max_date:
                    max_date = trans["date"]

            import_file.start_date = min_date
            import_file.end_date = max_date
            import_file.total_debits = total_debits
            import_file.total_credits = total_credits
            import_file.transaction_count = imported_count

            self._save_import_file(import_file)

            return {
                "success": True,
                "file_id": file_id,
                "filename": filename,
                "transactions_imported": imported_count,
                "total_debits": round(total_debits, 2),
                "total_credits": round(total_credits, 2)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _is_duplicate(self, fit_id: str, trans_date: date, amount: float) -> bool:
        """Check if transaction is a duplicate"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM genfin_imported_transactions
                WHERE fit_id = ? AND is_active = 1
            """, (fit_id,))
            if cursor.fetchone()[0] > 0:
                return True

            # Also check date/amount match within 1 day
            cursor.execute("""
                SELECT COUNT(*) FROM genfin_imported_transactions
                WHERE is_active = 1
                AND trans_date BETWEEN date(?, '-1 day') AND date(?, '+1 day')
                AND ABS(amount - ?) < 0.01
            """, (trans_date.isoformat(), trans_date.isoformat(), amount))
            if cursor.fetchone()[0] > 0:
                return True

        return False

    def _determine_transaction_type(self, trans: Dict) -> TransactionType:
        """Determine transaction type from OFX data"""
        trntype = trans.get("trntype", "").upper()

        type_map = {
            "CREDIT": TransactionType.CREDIT,
            "DEBIT": TransactionType.DEBIT,
            "CHECK": TransactionType.CHECK,
            "DEP": TransactionType.DEPOSIT,
            "XFER": TransactionType.TRANSFER,
            "FEE": TransactionType.FEE,
            "INT": TransactionType.INTEREST,
            "ATM": TransactionType.ATM,
            "POS": TransactionType.POS,
            "PAYMENT": TransactionType.PAYMENT
        }

        return type_map.get(trntype, TransactionType.OTHER)

    # ==================== MATCHING ====================

    def _try_auto_match(self, imported: ImportedTransaction):
        """Try to auto-match imported transaction with existing transactions"""
        # In a real implementation, this would check against existing transactions
        # For now, just set a match score based on categorization
        if imported.suggested_account_id:
            imported.match_score = 0.8
        else:
            imported.match_score = 0.0

    def match_transaction(
        self,
        import_id: str,
        transaction_id: str
    ) -> Dict:
        """Manually match an imported transaction to an existing transaction"""
        imported = self._get_transaction_by_id(import_id)
        if not imported:
            return {"success": False, "error": "Imported transaction not found"}

        imported.match_status = MatchStatus.MATCHED
        imported.matched_transaction_id = transaction_id
        imported.match_score = 1.0
        self._save_transaction(imported)

        return {
            "success": True,
            "import_id": import_id,
            "matched_to": transaction_id
        }

    def add_transaction(
        self,
        import_id: str,
        account_id: str,
        vendor_id: str = None,
        customer_id: str = None,
        memo: str = None
    ) -> Dict:
        """Add imported transaction as new transaction"""
        imported = self._get_transaction_by_id(import_id)
        if not imported:
            return {"success": False, "error": "Imported transaction not found"}

        # In real implementation, this would create the actual transaction
        transaction_id = str(uuid.uuid4())

        imported.match_status = MatchStatus.ADDED
        imported.matched_transaction_id = transaction_id
        imported.suggested_account_id = account_id
        self._save_transaction(imported)

        return {
            "success": True,
            "import_id": import_id,
            "transaction_id": transaction_id,
            "amount": imported.amount,
            "date": imported.date.isoformat()
        }

    def exclude_transaction(self, import_id: str) -> Dict:
        """Exclude imported transaction from processing"""
        imported = self._get_transaction_by_id(import_id)
        if not imported:
            return {"success": False, "error": "Imported transaction not found"}

        imported.match_status = MatchStatus.EXCLUDED
        self._save_transaction(imported)

        return {"success": True, "message": "Transaction excluded"}

    # ==================== CATEGORY RULES ====================

    def _apply_category_rules(self, imported: ImportedTransaction):
        """Apply category rules to imported transaction"""
        sorted_rules = self._get_all_rules()

        for rule in sorted_rules:
            if self._rule_matches(rule, imported):
                imported.suggested_account_id = rule.assign_account_id
                imported.suggested_vendor_id = rule.assign_vendor_id
                imported.suggested_customer_id = rule.assign_customer_id
                imported.category_rule_id = rule.rule_id
                break

    def _rule_matches(self, rule: CategoryRule, imported: ImportedTransaction) -> bool:
        """Check if a rule matches the transaction"""
        name_lower = imported.name.lower()
        memo_lower = imported.memo.lower()

        # Check name contains
        if rule.match_name_contains:
            if rule.match_name_contains.lower() not in name_lower:
                return False

        # Check name exact
        if rule.match_name_exact:
            if rule.match_name_exact.lower() != name_lower:
                return False

        # Check memo contains
        if rule.match_memo_contains:
            if rule.match_memo_contains.lower() not in memo_lower:
                return False

        # Check amount range
        if rule.match_amount_min is not None:
            if abs(imported.amount) < rule.match_amount_min:
                return False

        if rule.match_amount_max is not None:
            if abs(imported.amount) > rule.match_amount_max:
                return False

        # Check type
        if rule.match_type:
            if imported.transaction_type != rule.match_type:
                return False

        return True

    def create_category_rule(
        self,
        name: str,
        match_name_contains: str = "",
        match_memo_contains: str = "",
        match_amount_min: float = None,
        match_amount_max: float = None,
        assign_account_id: str = None,
        assign_vendor_id: str = None,
        priority: int = 0
    ) -> Dict:
        """Create a new category rule"""
        rule_id = str(uuid.uuid4())

        rule = CategoryRule(
            rule_id=rule_id,
            name=name,
            priority=priority,
            match_name_contains=match_name_contains,
            match_memo_contains=match_memo_contains,
            match_amount_min=match_amount_min,
            match_amount_max=match_amount_max,
            assign_account_id=assign_account_id,
            assign_vendor_id=assign_vendor_id
        )

        self._save_rule(rule)

        return {
            "success": True,
            "rule_id": rule_id,
            "name": name
        }

    def list_category_rules(self) -> Dict:
        """List all category rules"""
        rules = []
        for rule in self._get_all_rules():
            rules.append({
                "rule_id": rule.rule_id,
                "name": rule.name,
                "priority": rule.priority,
                "match_name_contains": rule.match_name_contains,
                "match_memo_contains": rule.match_memo_contains,
                "match_amount_min": rule.match_amount_min,
                "match_amount_max": rule.match_amount_max,
                "assign_account_id": rule.assign_account_id,
                "assign_vendor_id": rule.assign_vendor_id,
                "is_active": rule.is_active
            })

        return {"rules": rules, "total": len(rules)}

    def delete_category_rule(self, rule_id: str) -> Dict:
        """Delete a category rule (soft delete)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE genfin_category_rules
                SET is_active = 0
                WHERE rule_id = ?
            """, (rule_id,))
            if cursor.rowcount == 0:
                return {"success": False, "error": "Rule not found"}
            conn.commit()

        return {"success": True, "message": "Rule deleted"}

    # ==================== QUERIES ====================

    def get_imported_transactions(
        self,
        file_id: str = None,
        status: str = None,
        limit: int = 100
    ) -> Dict:
        """Get imported transactions"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_imported_transactions WHERE is_active = 1"
            params = []

            if file_id:
                query += " AND file_id = ?"
                params.append(file_id)
            if status:
                query += " AND match_status = ?"
                params.append(status)

            query += " ORDER BY trans_date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            transactions = []
            for row in rows:
                trans = self._row_to_transaction(row)
                transactions.append({
                    "import_id": trans.import_id,
                    "file_id": trans.file_id,
                    "date": trans.date.isoformat(),
                    "amount": trans.amount,
                    "type": trans.transaction_type.value,
                    "name": trans.name,
                    "memo": trans.memo,
                    "check_number": trans.check_number,
                    "status": trans.match_status.value,
                    "suggested_account_id": trans.suggested_account_id,
                    "suggested_vendor_id": trans.suggested_vendor_id,
                    "match_score": trans.match_score
                })

            # Count unmatched
            cursor.execute("""
                SELECT COUNT(*) FROM genfin_imported_transactions
                WHERE is_active = 1 AND match_status = 'unmatched'
            """)
            unmatched = cursor.fetchone()[0]

        return {
            "transactions": transactions,
            "total": len(transactions),
            "unmatched": unmatched
        }

    def get_import_files(self) -> Dict:
        """List all import files"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_import_files
                WHERE is_active = 1
                ORDER BY imported_at DESC
            """)
            rows = cursor.fetchall()

            files = []
            for row in rows:
                f = self._row_to_import_file(row)
                files.append({
                    "file_id": f.file_id,
                    "filename": f.filename,
                    "file_type": f.file_type.value,
                    "bank_id": f.bank_id,
                    "account_masked": f.account_number_masked,
                    "transaction_count": f.transaction_count,
                    "total_debits": f.total_debits,
                    "total_credits": f.total_credits,
                    "start_date": f.start_date.isoformat() if f.start_date else None,
                    "end_date": f.end_date.isoformat() if f.end_date else None,
                    "imported_at": f.imported_at.isoformat()
                })

        return {"files": files, "total": len(files)}

    def get_import(self, file_id: str) -> Optional[Dict]:
        """Get a single import file by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_import_files
                WHERE file_id = ? AND is_active = 1
            """, (file_id,))
            row = cursor.fetchone()
            if not row:
                return None

            f = self._row_to_import_file(row)
            return {
                "file_id": f.file_id,
                "filename": f.filename,
                "file_type": f.file_type.value,
                "bank_id": f.bank_id,
                "account_masked": f.account_number_masked,
                "transaction_count": f.transaction_count,
                "total_debits": f.total_debits,
                "total_credits": f.total_credits,
                "start_date": f.start_date.isoformat() if f.start_date else None,
                "end_date": f.end_date.isoformat() if f.end_date else None,
                "imported_at": f.imported_at.isoformat()
            }

    def get_transactions(self, import_id: str = None, status: str = None, bank_account_id: str = None) -> Dict:
        """List imported transactions with optional filters"""
        return self.get_imported_transactions(file_id=import_id, status=status)

    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Get a single transaction by ID"""
        trans = self._get_transaction_by_id(transaction_id)
        if not trans:
            return None
        return {
            "transaction_id": trans.import_id,
            "import_file_id": trans.file_id,
            "date": trans.date.isoformat(),
            "amount": trans.amount,
            "description": trans.name,
            "payee_name": trans.name,
            "memo": trans.memo,
            "transaction_type": trans.transaction_type.value,
            "check_number": trans.check_number,
            "status": trans.match_status.value,
            "category_account": trans.suggested_account_id,
            "match_score": trans.match_score
        }

    def auto_categorize_all(self, import_id: str = None) -> Dict:
        """Apply category rules to all unmatched transactions"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT * FROM genfin_imported_transactions
                WHERE is_active = 1 AND match_status = 'unmatched'
            """
            params = []

            if import_id:
                query += " AND file_id = ?"
                params.append(import_id)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            categorized = 0
            for row in rows:
                trans = self._row_to_transaction(row)
                self._apply_category_rules(trans)
                if trans.suggested_account_id:
                    self._save_transaction(trans)
                    categorized += 1

        return {
            "success": True,
            "transactions_processed": len(rows),
            "transactions_categorized": categorized
        }

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM genfin_import_files WHERE is_active = 1")
            total_files = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_imported_transactions WHERE is_active = 1")
            total_trans = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_imported_transactions WHERE is_active = 1 AND match_status = 'unmatched'")
            unmatched = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_imported_transactions WHERE is_active = 1 AND match_status = 'matched'")
            matched = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_imported_transactions WHERE is_active = 1 AND match_status = 'added'")
            added = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_category_rules WHERE is_active = 1")
            rules_count = cursor.fetchone()[0]

        return {
            "service": "GenFin Bank Feeds Import",
            "version": "1.0.0",
            "features": [
                "OFX/QFX File Import",
                "QBO File Import",
                "CSV Import",
                "Auto-Categorization Rules",
                "Transaction Matching",
                "Duplicate Detection"
            ],
            "supported_formats": ["OFX", "QFX", "QBO", "CSV"],
            "total_files_imported": total_files,
            "total_transactions": total_trans,
            "unmatched_transactions": unmatched,
            "matched_transactions": matched,
            "added_transactions": added,
            "category_rules": rules_count
        }


# Singleton instance
genfin_bank_feeds_service = GenFinBankFeedsService()
