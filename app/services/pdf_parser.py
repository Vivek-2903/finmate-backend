import io
from typing import List, Dict, Optional
import pdfplumber
import re
from datetime import datetime

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def detect_bank(text: str) -> str:
    text_lower = text.lower()
    if "hdfc" in text_lower:
        return "HDFC"
    if "icici" in text_lower:
        return "ICICI"
    if "sbi" in text_lower:
        return "SBI"
    return "UNKNOWN"


def clean_amount(amount_str: str) -> float:
    if not amount_str:
        return 0.0
    cleaned = re.sub(r'[^\d.-]', '', str(amount_str).replace(',', ''))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def parse_date(date_str: str) -> Optional[str]:
    if not date_str or len(date_str.strip()) < 6:
        return None
    date_str = date_str.strip()
    formats = ["%d/%m/%y", "%d/%m/%Y", "%d-%m-%y", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date().isoformat()
        except:
            continue
    return None


def merge_multiline_rows(table: List[List[str]]) -> List[List[str]]:
    if not table:
        return table
    merged = []
    i = 0
    date_regex = r'^\d{2}[/\-\.]\d{2}[/\-\.]\d{2,4}$'
    
    while i < len(table):
        current_row = table[i]
        if current_row and len(current_row) > 0:
            first_cell = str(current_row[0]).strip()
            if re.match(date_regex, first_cell):
                j = i + 1
                while j < len(table):
                    next_row = table[j]
                    if not next_row or not next_row[0] or not str(next_row[0]).strip():
                        if len(next_row) > 1 and next_row[1]:
                            current_row[1] = str(current_row[1]) + " " + str(next_row[1])
                        j += 1
                    elif not re.match(date_regex, str(next_row[0]).strip()):
                        if len(next_row) > 0 and next_row[0]:
                            current_row[1] = str(current_row[1]) + " " + str(next_row[0])
                        if len(next_row) > 1 and next_row[1]:
                            current_row[1] = str(current_row[1]) + " " + str(next_row[1])
                        j += 1
                    else:
                        break
                merged.append(current_row)
                i = j
            else:
                i += 1
        else:
            i += 1
    return merged


def extract_with_pdfplumber(file_bytes: bytes) -> List[Dict]:
    transactions = []
    seen_transactions = set()
    
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        print(f"Processing {len(pdf.pages)} pages")
        
        for page_num, page in enumerate(pdf.pages, start=1):
            table = None
            strategies = [
                {"vertical_strategy": "lines", "horizontal_strategy": "lines", "snap_tolerance": 3},
                {"vertical_strategy": "lines", "horizontal_strategy": "lines", "snap_tolerance": 5},
                {"vertical_strategy": "text", "horizontal_strategy": "text"},
            ]
            
            for i, settings in enumerate(strategies):
                try:
                    table = page.extract_table(settings)
                    if table and len(table) > 1:
                        break
                except:
                    continue
            
            if table and len(table) > 1:
                table = merge_multiline_rows(table)
                
                for row in table:
                    if not row or len(row) < 6:
                        continue
                    
                    row = [str(c).strip() if c else "" for c in row]
                    
                    date_regex = r'^\d{2}[/\-\.]\d{2}[/\-\.]\d{2,4}$'
                    if not row[0] or not re.match(date_regex, row[0]):
                        continue
                    
                    row_text = " ".join(row).lower()
                    if any(kw in row_text for kw in ['date', 'narration', 'withdrawal', 'deposit']):
                        continue
                    
                    date_str = row[0]
                    narration = row[1]
                    
                    col2 = str(row[2]).strip() if len(row) > 2 else ""
                    col3 = str(row[3]).strip() if len(row) > 3 else ""
                    date_pattern = r'^\d{2}[/\-\.]\d{2}[/\-\.]\d{2,4}$'
                    
                    chq_ref = ""
                    value_date = ""
                    withdrawal = ""
                    deposit = ""
                    balance = ""
                    
                    if col2 and col2.isdigit() and col3 and col3.isdigit() and not re.match(date_pattern, col3):
                        chq_ref = col2 + col3
                        value_date = row[4] if len(row) > 4 else ""
                        withdrawal = row[5] if len(row) > 5 else ""
                        deposit = row[6] if len(row) > 6 else ""
                        balance = row[7] if len(row) > 7 else ""
                    elif col2 and col2.isdigit() and col3 and re.match(date_pattern, col3):
                        chq_ref = col2
                        value_date = col3
                        withdrawal = row[4] if len(row) > 4 else ""
                        deposit = row[5] if len(row) > 5 else ""
                        balance = row[6] if len(row) > 6 else ""
                    else:
                        chq_ref = row[2] if len(row) > 2 else ""
                        value_date = row[3] if len(row) > 3 else ""
                        withdrawal = row[4] if len(row) > 4 else ""
                        deposit = row[5] if len(row) > 5 else ""
                        balance = row[6] if len(row) > 6 else ""
                    
                    parsed_date = parse_date(date_str)
                    if not parsed_date or not narration or len(narration) < 3:
                        continue
                    
                    withdrawal_raw = withdrawal.strip() if withdrawal else ""
                    deposit_raw = deposit.strip() if deposit else ""
                    
                    withdrawal_amt = clean_amount(withdrawal_raw)
                    deposit_amt = clean_amount(deposit_raw)
                    balance_amt = clean_amount(balance)
                    
                    narration = re.sub(r'\s+', ' ', narration).strip()
                    
                    has_withdrawal = withdrawal_raw and withdrawal_amt > 0
                    has_deposit = deposit_raw and deposit_amt > 0
                    
                    if has_withdrawal and not has_deposit:
                        withdrawal_amt = withdrawal_amt
                        deposit_amt = 0.0
                    elif has_deposit and not has_withdrawal:
                        deposit_amt = deposit_amt
                        withdrawal_amt = 0.0
                    elif not has_withdrawal and not has_deposit:
                        continue
                    
                    transaction_key = f"{parsed_date}|{narration[:50]}|{withdrawal_amt}|{deposit_amt}|{balance_amt}"
                    if transaction_key in seen_transactions:
                        continue
                    seen_transactions.add(transaction_key)
                    
                    transaction = {
                        "date": parsed_date,
                        "narration": narration,
                        "chq_ref_no": chq_ref,
                        "value_date": parse_date(value_date) or value_date,
                        "withdrawal": withdrawal_amt,
                        "deposit": deposit_amt,
                        "balance": balance_amt,
                        "raw": " | ".join(row)
                    }
                    
                    transactions.append(transaction)
    
    return transactions


def extract_transactions_from_pdf_bytes(file_bytes: bytes, use_ocr: bool = False) -> List[Dict]:
    print("Starting PDF extraction")
    transactions = extract_with_pdfplumber(file_bytes)
    transactions = sorted(transactions, key=lambda x: x.get("date", ""))
    print(f"Extracted {len(transactions)} transactions")
    return transactions


def extract_text_pages(file_bytes: bytes) -> List[str]:
    pages = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return pages


def export_to_csv(transactions: List[Dict], filename: str = "transactions.csv"):
    import csv
    if not transactions:
        return
    headers = ["date", "narration", "chq_ref_no", "value_date", "withdrawal", "deposit", "balance"]
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(transactions)
    print(f"Exported to {filename}")