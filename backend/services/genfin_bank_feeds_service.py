"""
GenFin Bank Feeds Import Service
Handles importing transactions from OFX, QFX, and QBO bank files.
"""
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid
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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.import_files: Dict[str, ImportFile] = {}
        self.imported_transactions: Dict[str, ImportedTransaction] = {}
        self.category_rules: Dict[str, CategoryRule] = {}

        # Initialize default rules
        self._initialize_default_rules()

        self._initialized = True

    def _initialize_default_rules(self):
        """Create default categorization rules"""
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
            self.category_rules[rule_id] = CategoryRule(
                rule_id=rule_id,
                name=name,
                match_name_contains=match,
                match_memo_contains=memo,
                match_amount_min=amt_min,
                match_amount_max=amt_max,
                assign_account_id=account_id
            )

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

                self.imported_transactions[import_id] = imported
                imported_count += 1

                if trans["amount"] < 0:
                    total_debits += abs(trans["amount"])
                else:
                    total_credits += trans["amount"]

            import_file.total_debits = total_debits
            import_file.total_credits = total_credits
            import_file.transaction_count = imported_count

            self.import_files[file_id] = import_file

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
                self.imported_transactions[import_id] = imported
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

            self.import_files[file_id] = import_file

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
        for trans in self.imported_transactions.values():
            if trans.fit_id == fit_id:
                return True
            # Also check date/amount match within 1 day
            if abs((trans.date - trans_date).days) <= 1 and abs(trans.amount - amount) < 0.01:
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
        if import_id not in self.imported_transactions:
            return {"success": False, "error": "Imported transaction not found"}

        imported = self.imported_transactions[import_id]
        imported.match_status = MatchStatus.MATCHED
        imported.matched_transaction_id = transaction_id
        imported.match_score = 1.0

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
        if import_id not in self.imported_transactions:
            return {"success": False, "error": "Imported transaction not found"}

        imported = self.imported_transactions[import_id]

        # In real implementation, this would create the actual transaction
        transaction_id = str(uuid.uuid4())

        imported.match_status = MatchStatus.ADDED
        imported.matched_transaction_id = transaction_id
        imported.suggested_account_id = account_id

        return {
            "success": True,
            "import_id": import_id,
            "transaction_id": transaction_id,
            "amount": imported.amount,
            "date": imported.date.isoformat()
        }

    def exclude_transaction(self, import_id: str) -> Dict:
        """Exclude imported transaction from processing"""
        if import_id not in self.imported_transactions:
            return {"success": False, "error": "Imported transaction not found"}

        self.imported_transactions[import_id].match_status = MatchStatus.EXCLUDED

        return {"success": True, "message": "Transaction excluded"}

    # ==================== CATEGORY RULES ====================

    def _apply_category_rules(self, imported: ImportedTransaction):
        """Apply category rules to imported transaction"""
        # Sort rules by priority (highest first)
        sorted_rules = sorted(
            [r for r in self.category_rules.values() if r.is_active],
            key=lambda x: x.priority,
            reverse=True
        )

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

        self.category_rules[rule_id] = rule

        return {
            "success": True,
            "rule_id": rule_id,
            "name": name
        }

    def list_category_rules(self) -> Dict:
        """List all category rules"""
        rules = []
        for rule in sorted(self.category_rules.values(), key=lambda x: x.priority, reverse=True):
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
        """Delete a category rule"""
        if rule_id not in self.category_rules:
            return {"success": False, "error": "Rule not found"}

        del self.category_rules[rule_id]
        return {"success": True, "message": "Rule deleted"}

    # ==================== QUERIES ====================

    def get_imported_transactions(
        self,
        file_id: str = None,
        status: str = None,
        limit: int = 100
    ) -> Dict:
        """Get imported transactions"""
        transactions = []

        for trans in self.imported_transactions.values():
            if file_id and trans.file_id != file_id:
                continue
            if status and trans.match_status.value != status:
                continue

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

        # Sort by date descending
        transactions.sort(key=lambda x: x["date"], reverse=True)

        return {
            "transactions": transactions[:limit],
            "total": len(transactions),
            "unmatched": sum(1 for t in transactions if t["status"] == "unmatched")
        }

    def get_import_files(self) -> Dict:
        """List all import files"""
        files = []
        for f in self.import_files.values():
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

        files.sort(key=lambda x: x["imported_at"], reverse=True)

        return {"files": files, "total": len(files)}

    def get_import(self, file_id: str) -> Optional[Dict]:
        """Get a single import file by ID"""
        if file_id not in self.import_files:
            return None
        f = self.import_files[file_id]
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
        transactions = []
        for trans in self.imported_transactions.values():
            if import_id and trans.import_file_id != import_id:
                continue
            if status and trans.match_status.value != status:
                continue
            transactions.append({
                "transaction_id": trans.import_id,
                "import_file_id": trans.import_file_id,
                "date": trans.trans_date.isoformat(),
                "amount": trans.amount,
                "description": trans.description,
                "payee_name": trans.payee_name,
                "memo": trans.memo,
                "transaction_type": trans.trans_type.value,
                "check_number": trans.check_number,
                "status": trans.match_status.value,
                "category_account": trans.suggested_account_id,
                "match_score": trans.match_score
            })

        transactions.sort(key=lambda x: x["date"], reverse=True)

        return {
            "transactions": transactions,
            "total": len(transactions),
            "unmatched": sum(1 for t in transactions if t["status"] == "unmatched")
        }

    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Get a single transaction by ID"""
        if transaction_id not in self.imported_transactions:
            return None
        trans = self.imported_transactions[transaction_id]
        return {
            "transaction_id": trans.import_id,
            "import_file_id": trans.import_file_id,
            "date": trans.trans_date.isoformat(),
            "amount": trans.amount,
            "description": trans.description,
            "payee_name": trans.payee_name,
            "memo": trans.memo,
            "transaction_type": trans.trans_type.value,
            "check_number": trans.check_number,
            "status": trans.match_status.value,
            "category_account": trans.suggested_account_id,
            "match_score": trans.match_score
        }

    def auto_categorize_all(self, import_id: str = None) -> Dict:
        """Apply category rules to all unmatched transactions"""
        categorized = 0
        for trans in self.imported_transactions.values():
            if import_id and trans.import_file_id != import_id:
                continue
            if trans.match_status == MatchStatus.UNMATCHED:
                self._apply_category_rules(trans)
                if trans.suggested_account_id:
                    categorized += 1

        return {
            "success": True,
            "transactions_processed": len(self.imported_transactions),
            "transactions_categorized": categorized
        }

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        unmatched = sum(1 for t in self.imported_transactions.values()
                       if t.match_status == MatchStatus.UNMATCHED)
        matched = sum(1 for t in self.imported_transactions.values()
                     if t.match_status == MatchStatus.MATCHED)
        added = sum(1 for t in self.imported_transactions.values()
                   if t.match_status == MatchStatus.ADDED)

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
            "total_files_imported": len(self.import_files),
            "total_transactions": len(self.imported_transactions),
            "unmatched_transactions": unmatched,
            "matched_transactions": matched,
            "added_transactions": added,
            "category_rules": len(self.category_rules)
        }


# Singleton instance
genfin_bank_feeds_service = GenFinBankFeedsService()
