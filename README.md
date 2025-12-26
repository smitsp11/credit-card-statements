# Credit Statement to Sheets

A deterministic, offline-first Python tool that parses RBC credit card PDF statements, classifies transactions into personal categories, and appends category totals to a Google Sheet.

## Features

- Parses RBC credit card PDF statements
- Classifies transactions using deterministic rules
- Aggregates totals by category
- Appends results to Google Sheets (one row per category)
- Runs locally, no cloud hosting required

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Sheets API and Google Drive API
   - Create a Service Account
   - Download the credentials JSON file
   - Save it as `credentials.json` in the project root

3. **Share your Google Sheet:**
   - Open your Google Sheet
   - Click "Share" and add the service account email (found in credentials.json)
   - Give it "Editor" permissions

## Usage

```bash
python run.py \
  --pdf path/to/statement.pdf \
  --month "December 2025" \
  --sheet-id <GOOGLE_SHEET_ID>
```

### Arguments

- `--pdf`: Path to the RBC credit card PDF statement
- `--month`: Statement month (e.g., "December 2025")
- `--sheet-id`: Google Sheet ID (found in the sheet URL)
- `--config`: Optional path to config file (default: config.yaml)

## Categories

The tool classifies transactions into these categories:

- school meals
- food
- groceries
- presto
- school
- personal
- mom stuff
- other

## Classification Rules

1. **Ignore Rules**: Transactions containing PAYMENT, THANK YOU, PAIEMENT, BALANCE, INTEREST, or FEE are skipped
2. **Hard Merchant Overrides**: Specific merchants are mapped to categories (e.g., PRESTO → presto, WALMART → groceries)
3. **Food-Type Detection**: Detects restaurants and food delivery services
4. **Weekday/Weekend Rule**: Food-type merchants on weekdays → school meals, weekends → food
5. **Amount-Based Fallback**: Large amounts (≥$100) → school, small amounts (≤$10) → groceries, else → other

## Output

The tool appends rows to your Google Sheet with the format:

| Month | Category | Amount |
|-------|----------|--------|
| December 2025 | food | 45.67 |
| December 2025 | groceries | 123.45 |
| ... | ... | ... |

Only categories with non-zero totals are written.

## Project Structure

```
credit-statement-to-sheets/
├── run.py                 # CLI entry point
├── parser/
│   └── pdf_parser.py      # PDF parsing logic
├── classifier/
│   ├── rules.py           # Classification rules
│   ├── food_detector.py   # Food-type detection
│   └── classify.py        # Main classification logic
├── sheets/
│   └── writer.py          # Google Sheets writer
├── config.yaml            # Configuration file
└── requirements.txt       # Python dependencies
```

## Notes

- The tool is deterministic: same input always produces same output
- No transaction-level data is written to Sheets, only category totals
- The tool does not modify existing spreadsheet formulas
- Re-running with the same data will append duplicate rows (intentional)

