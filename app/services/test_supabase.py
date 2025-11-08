from app.services.supabase_client import supabase

resp = supabase.table("bank_statements").select("*").execute()
print(resp)
