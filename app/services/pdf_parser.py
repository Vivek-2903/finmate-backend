import io
from typing import List, Dict
import pdfplumber
import re
from datetime import datetime

# -------------------------
# Detect Bank
# -------------------------
def detect_bank(text: str) -> str:
    text_lower = text.lower()

    if "hdfc" in text_lower or "hdfc bank" in text_lower:
        return "HDFC"
    if "icici" in text_lower or "icici bank" in text_lower:
        return "ICICI"
    if "state bank of india" in text_lower or "sbi" in text_lower:
        return "SBI"

    return "UNKNOWN"

# -------------------------
# Extract all pages text
# -------------------------
def extract_text_pages(file_bytes: bytes) -> List[str]:
    pages = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return pages


# -------------------------
# Improved Line Parser
# -------------------------
def simple_line_parser(text: str) -> List[Dict]:
    results = []

    # Patterns for dates + amount
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    amount_pattern = r'(-?\d[\d,]*\.\d{2})'

    for line in text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue

        date_match = re.search(date_pattern, line_clean)
        amount_match = re.search(amount_pattern, line_clean.replace("₹", ""))

        if date_match and amount_match:
            # Extract date safely
            date_str = date_match.group(1)

            parsed_date = None
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date().isoformat()
                    break
                except:
                    continue

            # Extract amount
            amt_str = amount_match.group(1)
            amt_value = float(amt_str.replace(",", ""))

            results.append({
                "date": parsed_date or date_str,
                "description": line_clean,
                "amount": amt_value,
                "raw": line_clean,
            })

    return results


# -------------------------
# Main Extractor
# -------------------------
def extract_transactions_from_pdf_bytes(file_bytes: bytes) -> List[Dict]:
    pages = extract_text_pages(file_bytes)
    transactions = []

    for page in pages:
        transactions.extend(simple_line_parser(page))

    return transactions
