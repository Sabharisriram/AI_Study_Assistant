from dotenv import load_dotenv
load_dotenv()  # ✅ Must be FIRST before any os.getenv() calls

from supabase import create_client, Client
import os

SUPABASE_URL      = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

_supabase: Client = None


def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise ValueError(
                "SUPABASE_URL or SUPABASE_ANON_KEY is missing from .env — "
                "make sure the file is in your project root and load_dotenv() runs first."
            )
        _supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase


def sign_up(email: str, password: str) -> dict:
    res = get_supabase().auth.sign_up({"email": email, "password": password})
    if res.user is None:
        raise ValueError("Signup failed — check email/password")
    return {"user_id": res.user.id, "email": res.user.email}


def sign_in(email: str, password: str) -> dict:
    res = get_supabase().auth.sign_in_with_password({"email": email, "password": password})
    if res.user is None:
        raise ValueError("Invalid email or password")
    return {
        "user_id":      res.user.id,
        "email":        res.user.email,
        "access_token": res.session.access_token
    }


def sign_out(access_token: str):
    try:
        get_supabase().auth.sign_out()
    except Exception:
        pass


def get_user(access_token: str) -> dict | None:
    try:
        res = get_supabase().auth.get_user(access_token)
        if res.user:
            return {"user_id": res.user.id, "email": res.user.email}
    except Exception:
        pass
    return None