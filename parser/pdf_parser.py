"""
PDF Parser for RBC Credit Card Statements.

Extracts transaction data from PDF statements.
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
import pdfplumber


class Transaction:
    """Represents a single credit card transaction."""
    
    def __init__(self, merchant_description: str, transaction_date: datetime, amount: float):
        self.merchant_description = merchant_description.strip()
        self.transaction_date = transaction_date
        self.amount = amount
    
    def __repr__(self):
        return f"Transaction({self.merchant_description}, {self.transaction_date.date()}, ${self.amount:.2f})"


class PDFParser:
    """Parses RBC credit card PDF statements."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.transactions: List[Transaction] = []
    
    def parse(self, debug: bool = False) -> List[Transaction]:
        """
        Parse the PDF and extract all transactions.
        
        Args:
            debug: If True, print debug information about extracted content
        
        Returns:
            List of Transaction objects
        """
        transactions = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                if debug:
                    print(f"\n--- Page {page_num} ---")
                
                # Try table extraction first (more reliable for structured data)
                tables = page.extract_tables()
                if debug:
                    print(f"Found {len(tables) if tables else 0} tables")
                
                table_transactions = []
                if tables:
                    for table_num, table in enumerate(tables):
                        if debug:
                            print(f"\nTable {table_num + 1} (first 3 rows):")
                            for i, row in enumerate(table[:3]):
                                print(f"  Row {i}: {row}")
                        
                        page_transactions = self._extract_transactions_from_table(table)
                        table_transactions.extend(page_transactions)
                        if debug:
                            print(f"  Extracted {len(page_transactions)} transactions from this table")
                
                # Always try text extraction as well (RBC statements may have mixed formats)
                text = page.extract_text()
                if text:
                    if debug:
                        print(f"\nText extraction (first 500 chars):")
                        print(text[:500])
                        print("...")
                    
                    text_transactions = self._extract_transactions_from_text(text)
                    if debug:
                        print(f"Extracted {len(text_transactions)} transactions from text")
                    
                    # Combine transactions, avoiding duplicates
                    # (prefer table extraction if both found the same transaction)
                    if table_transactions:
                        # Use table transactions, add text transactions that aren't duplicates
                        transactions.extend(table_transactions)
                        # Simple deduplication: check if merchant+amount+date match
                        existing = {(t.merchant_description, t.amount, t.transaction_date.date()) 
                                   for t in table_transactions}
                        for t in text_transactions:
                            key = (t.merchant_description, t.amount, t.transaction_date.date())
                            if key not in existing:
                                transactions.append(t)
                                existing.add(key)
                    else:
                        transactions.extend(text_transactions)
        
        self.transactions = transactions
        return transactions
    
    def _extract_transactions_from_table(self, table: List[List]) -> List[Transaction]:
        """
        Extract transactions from a table structure.
        
        RBC statements often have tables with columns: Date, Description, Amount
        """
        transactions = []
        
        for row in table:
            if not row or len(row) < 2:
                continue
            
            # Try to find date, merchant, and amount in the row
            date_str = None
            merchant = None
            amount = None
            
            for cell in row:
                if not cell:
                    continue
                
                cell_str = str(cell).strip()
                
                # Check for date pattern (MM/DD or MM/DD/YY)
                date_match = re.match(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', cell_str)
                if date_match and not date_str:
                    date_str = cell_str
                    continue
                
                # Check for amount pattern ($XX.XX or XX.XX)
                amount_match = re.search(r'[\$]?([\d,]+\.\d{2})', cell_str)
                if amount_match and amount is None:
                    amount_str = amount_match.group(1).replace(',', '')
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        continue
                    continue
                
                # If not date or amount, likely merchant name
                if not date_str and not amount and len(cell_str) > 3:
                    if merchant:
                        merchant += ' ' + cell_str
                    else:
                        merchant = cell_str
            
            # Create transaction if we have all required fields
            if date_str and merchant and amount is not None:
                # Only process purchases (positive amounts)
                if amount > 0:
                    try:
                        transaction_date = self._parse_date(date_str)
                        if transaction_date:
                            transaction = Transaction(merchant, transaction_date, amount)
                            transactions.append(transaction)
                    except (ValueError, IndexError):
                        pass
        
        return transactions
    
    def _extract_transactions_from_text(self, text: str) -> List[Transaction]:
        """
        Extract transactions from page text.
        
        RBC statements have transactions in format:
        MON DD MON DD MERCHANT NAME                    $XX.XX
        e.g., "NOV 25 NOV 27 MCDONALD'S #40392 BRAMPTON ON $3.38"
        """
        transactions = []
        lines = text.split('\n')
        
        # Month abbreviations
        months = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        
        # Pattern for RBC format: MON DD MON DD (two dates - posting and transaction)
        # We'll use the second date (transaction date)
        rbc_date_pattern = r'([A-Z]{3})\s+(\d{1,2})\s+([A-Z]{3})\s+(\d{1,2})'
        # Also handle single date format: MON DD
        single_date_pattern = r'([A-Z]{3})\s+(\d{1,2})'
        # Amount pattern: $XX.XX at end of line
        amount_pattern = r'\$\s*([\d,]+\.\d{2})\s*$'
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Skip header lines
            if any(header in line.upper() for header in ['TRANSACTION', 'POSTING', 'ACTIVITY', 'DESCRIPTION', 'AMOUNT', 'DATE']):
                i += 1
                continue
            
            # Try RBC double date format first (MON DD MON DD)
            date_match = re.search(rbc_date_pattern, line)
            transaction_date = None
            date_end = 0
            
            if date_match:
                # Use the second date (transaction date, not posting date)
                month_str = date_match.group(3)
                day = int(date_match.group(4))
                date_end = date_match.end()
                
                if month_str in months:
                    month = months[month_str]
                    year = datetime.now().year
                    # If month is > current month, it's probably last year
                    if month > datetime.now().month:
                        year = datetime.now().year - 1
                    transaction_date = datetime(year, month, day)
            else:
                # Try single date format
                single_match = re.search(single_date_pattern, line)
                if single_match:
                    month_str = single_match.group(1)
                    day = int(single_match.group(2))
                    date_end = single_match.end()
                    
                    if month_str in months:
                        month = months[month_str]
                        year = datetime.now().year
                        if month > datetime.now().month:
                            year = datetime.now().year - 1
                        transaction_date = datetime(year, month, day)
            
            if transaction_date:
                # Look for amount at end of line
                amount_match = re.search(amount_pattern, line)
                
                if amount_match:
                    # Extract text between date and amount
                    amount_start = amount_match.start()
                    text_between = line[date_end:amount_start].strip()
                    
                    # Skip long numeric IDs (transaction IDs, account numbers, etc.)
                    # These are typically 15+ digits
                    parts = text_between.split()
                    merchant_parts = []
                    
                    for part in parts:
                        # Skip parts that are just long numbers (likely transaction IDs)
                        if part.isdigit() and len(part) >= 15:
                            continue
                        # Skip parts that are just numbers with dashes (account numbers)
                        if re.match(r'^\d+-\d+$', part):
                            continue
                        merchant_parts.append(part)
                    
                    merchant = ' '.join(merchant_parts).strip()
                    
                    # Clean up merchant name
                    merchant = re.sub(r'\s+', ' ', merchant)
                    
                    # Skip if merchant is too short or empty
                    if len(merchant) < 2:
                        i += 1
                        continue
                    
                    # Parse amount
                    amount_str = amount_match.group(1).replace(',', '')
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        i += 1
                        continue
                    
                    # Only process purchases (positive amounts)
                    if amount > 0:
                        transaction = Transaction(merchant, transaction_date, amount)
                        transactions.append(transaction)
            
            i += 1
        
        return transactions
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string into datetime object.
        
        Handles formats: MM/DD, MM/DD/YY, MM/DD/YYYY
        """
        try:
            parts = date_str.split('/')
            if len(parts) == 2:
                month, day = map(int, parts)
                year = datetime.now().year
                # If month is > current month, it's probably last year
                if month > datetime.now().month:
                    year = datetime.now().year - 1
            elif len(parts) == 3:
                month, day, year_part = parts
                month, day = int(month), int(day)
                if len(year_part) == 2:
                    year = 2000 + int(year_part)
                else:
                    year = int(year_part)
            else:
                return None
            
            return datetime(year, month, day)
        except (ValueError, IndexError):
            return None
    
    def get_total_purchases(self) -> float:
        """Calculate total of all transactions."""
        return sum(t.amount for t in self.transactions)

