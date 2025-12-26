"""
Google Sheets writer.

Appends category totals to a Google Sheet.
"""
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict
import yaml
import os


class SheetsWriter:
    """Handles writing to Google Sheets."""
    
    def __init__(self, credentials_file: str, sheet_id: str):
        """
        Initialize the Sheets writer.
        
        Args:
            credentials_file: Path to Google service account credentials JSON
            sheet_id: Google Sheet ID
        """
        self.credentials_file = credentials_file
        self.sheet_id = sheet_id
        self.client = None
        self.sheet = None
    
    def _connect(self):
        """Connect to Google Sheets using service account."""
        if self.client is None:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scope
            )
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(self.sheet_id).sheet1
    
    def append_category_totals(self, month: str, category_totals: Dict[str, float]):
        """
        Append category totals to the sheet.
        
        Args:
            month: Month string (e.g., "December 2025")
            category_totals: Dictionary mapping category names to amounts
        """
        self._connect()
        
        # Prepare rows: one per category
        rows = []
        for category, amount in sorted(category_totals.items()):
            rows.append([month, category, amount])
        
        # Append all rows at once
        if rows:
            self.sheet.append_rows(rows)
    
    def validate_connection(self) -> bool:
        """
        Validate that we can connect to the sheet.
        
        Returns:
            True if connection successful
        """
        try:
            self._connect()
            # Try to read first row to verify access
            self.sheet.row_values(1)
            return True
        except Exception as e:
            print(f"Error connecting to Google Sheet: {e}")
            return False

