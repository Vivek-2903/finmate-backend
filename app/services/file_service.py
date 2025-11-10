from app.services.supabase_client import supabase

def download_pdf_from_supabase(filename: str) -> bytes:
    """
    Download a PDF from the STATEMENTS bucket and return it as bytes.
    """
    try:
        response = supabase.storage.from_("STATEMENTS").download(filename)
        return response
    except Exception as e:
        raise Exception(f"Failed to download PDF: {e}")
