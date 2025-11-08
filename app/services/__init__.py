from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()  # loads ../.env when run from root with -m
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
