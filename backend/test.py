from dotenv import load_dotenv
import os

load_dotenv()

    # for key, value in sorted(os.environ.items()):
    #     print(f"{key}={value}")


supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
bucket_name = os.getenv("SUPABASE_BUCKET", "images")

from supabase import create_client, Client

supabase: Client = create_client(supabase_url, supabase_key)
print(supabase)