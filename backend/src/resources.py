import os
import traceback
from supabase import create_client, Client


def get_verified_directory():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("DEBUG: Missing SUPABASE_URL or SUPABASE_KEY in environment.")
        return []

    try:
        supabase: Client = create_client(url, key)

        response = supabase.table('resources').select('*').eq('is_active', True).execute()

        directory = response.data

        print(f"DEBUG: Successfully fetched {len(directory)} active resources from Supabase.")
        return directory

    except Exception as e:
        print(f"Directory Fetch Error: {repr(e)}")
        print("--- FULL TRACEBACK ---")
        traceback.print_exc()
        print("----------------------")
        return []