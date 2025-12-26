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
    
    def parse(self) -> List[Transaction]:
        """
        Parse the PDF and extract all transactions.
        
        Returns:
            List of Transaction objects
        """
        transactions = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                # Try table extraction first (more reliable for structured data)
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        page_transactions = self._extract_transactions_from_table(table)
                        transactions.extend(page_transactions)
                
                # Fallback to text extraction if no tables found
                if not tables:
                    text = page.extract_text()
                    if text:
                        page_transactions = self._extract_transactions_from_text(text)
                        transactions.extend(page_transactions)
        
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
        
        RBC statements typically have transactions in a format like:
        MM/DD MERCHANT NAME                    $XX.XX
        """
        transactions = []
        lines = text.split('\n')
        
        # Pattern to match date, merchant, and amount
        date_pattern = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)'
        amount_pattern = r'[\$]?([\d,]+\.\d{2})'
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for date pattern
            date_match = re.search(date_pattern, line)
            if date_match:
                date_str = date_match.group(1)
                
                # Try to extract amount from the same line or next lines
                amount_match = re.search(amount_pattern, line)
                
                if amount_match:
                    # Extract merchant name (between date and amount)
                    date_end = date_match.end()
                    amount_start = amount_match.start()
                    merchant = line[date_end:amount_start].strip()
                    
                    # Parse amount
                    amount_str = amount_match.group(1).replace(',', '')
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        i += 1
                        continue
                    
                    # Only process purchases (positive amounts)
                    if amount > 0:
                        transaction_date = self._parse_date(date_str)
                        if transaction_date:
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

