from fastapi import FastAPI
from app.services.supabase_client import supabase

app = FastAPI()

@app.get("/")
def home():
    data = supabase.table("test_table").select("*").execute()
    return {"message": "FinMate Backend Connected ✅", "data": data.data}
