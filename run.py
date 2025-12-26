#!/usr/bin/env python3
"""
Main entry point for credit statement to sheets tool.

CLI Usage:
    python run.py --pdf path/to/statement.pdf --month "December 2025" --sheet-id <GOOGLE_SHEET_ID>
"""
import argparse
import sys
import yaml
from pathlib import Path

from parser.pdf_parser import PDFParser
from classifier.classify import aggregate_by_category
from sheets.writer import SheetsWriter


def load_config(config_path: str = 'config.yaml') -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description='Parse RBC credit card statement and append category totals to Google Sheet'
    )
    parser.add_argument(
        '--pdf',
        required=True,
        help='Path to PDF statement file'
    )
    parser.add_argument(
        '--month',
        required=True,
        help='Statement month (e.g., "December 2025")'
    )
    parser.add_argument(
        '--sheet-id',
        required=True,
        help='Google Sheet ID'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to config file (default: config.yaml)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode to see PDF parsing details'
    )
    
    args = parser.parse_args()
    
    # Validate PDF file exists
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {args.pdf}")
        sys.exit(1)
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)
    
    credentials_file = config.get('google', {}).get('credentials_file', 'credentials.json')
    if not Path(credentials_file).exists():
        print(f"Error: Credentials file not found: {credentials_file}")
        print("Please create a service account and download credentials.json")
        sys.exit(1)
    
    # Parse PDF
    print(f"Parsing PDF: {args.pdf}")
    pdf_parser = PDFParser(str(pdf_path))
    try:
        transactions = pdf_parser.parse(debug=args.debug)
        print(f"Found {len(transactions)} transactions")
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        sys.exit(1)
    
    if not transactions:
        print("Warning: No transactions found in PDF")
        sys.exit(1)
    
    # Classify and aggregate
    print("Classifying transactions...")
    category_totals, skipped_count = aggregate_by_category(transactions, debug=args.debug)
    
    if skipped_count > 0:
        print(f"Skipped {skipped_count} transactions (payments, fees, etc.)")
    
    # Print summary
    print("\nCategory Totals:")
    print("-" * 40)
    total = 0.0
    for category, amount in sorted(category_totals.items()):
        print(f"{category:20s} ${amount:10.2f}")
        total += amount
    
    print("-" * 40)
    print(f"{'Total':20s} ${total:10.2f}")
    
    # Validate totals match
    pdf_total = pdf_parser.get_total_purchases()
    print(f"\nPDF total purchases: ${pdf_total:.2f}")
    print(f"Classified total: ${total:.2f}")
    
    if abs(pdf_total - total) > 0.01:  # Allow small floating point differences
        print("Warning: Totals don't match exactly. This may be due to skipped transactions.")
    
    # Write to Google Sheets
    print(f"\nWriting to Google Sheet: {args.sheet_id}")
    writer = SheetsWriter(credentials_file, args.sheet_id)
    
    if not writer.validate_connection():
        print("Error: Could not connect to Google Sheet")
        print("Make sure:")
        print("  1. credentials.json is valid")
        print("  2. The sheet is shared with the service account email")
        sys.exit(1)
    
    try:
        writer.append_category_totals(args.month, category_totals)
        print("Successfully appended category totals to Google Sheet!")
    except Exception as e:
        print(f"Error writing to Google Sheet: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

