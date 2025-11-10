from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.supabase_client import supabase
from app.services.pdf_parser import extract_transactions_from_pdf_bytes
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/upload-statement")
async def upload_statement(file: UploadFile = File(...)):
    # 1. Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # 2. Read file bytes
    file_bytes = await file.read()

    # 3. Create unique filename
    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}.pdf"

    # 4. Upload to Supabase bucket
    try:
        supabase.storage.from_("STATEMENTS").upload(
            path=filename,
            file=file_bytes,
            file_options={"content-type": "application/pdf", "upsert": False}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    # ✅ 5. Parse transactions from PDF (fallback parser)
    try:
        transactions = extract_transactions_from_pdf_bytes(file_bytes)
    except Exception as e:
        transactions = []
        print(f"Parsing failed: {e}")

    # ✅ 6. Return everything
    return {
        "message": "Upload successful",
        "file_name": filename,
        "size": len(file_bytes),
        "uploaded_at": datetime.now().isoformat(),
        "parsed_preview": transactions[:10],   # show first 10 parsed lines
        "total_detected_lines": len(transactions)
    }
