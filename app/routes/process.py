from fastapi import APIRouter, HTTPException
from app.services.file_service import download_pdf_from_supabase
from app.services.pdf_parser import extract_transactions_from_pdf_bytes

router = APIRouter()

@router.post("/process-statement")
async def process_statement(file_name: str):
    try:
        # 1. Download PDF
        pdf_bytes = download_pdf_from_supabase(file_name)
        if not pdf_bytes:
            raise HTTPException(status_code=404, detail="File not found in Supabase.")

        # 2. Extract transactions
        transactions = extract_transactions_from_pdf_bytes(pdf_bytes)

        # 3. Build preview
        preview = transactions[:10]

        return {
            "message": "Processing successful",
            "total_detected_lines": len(transactions),
            "preview": preview
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
