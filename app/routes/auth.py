from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from app.services.auth_service import sign_up, sign_in, sign_out, get_user

router = APIRouter()


class AuthRequest(BaseModel):
    email:    EmailStr
    password: str


@router.post("/signup")
def signup(body: AuthRequest):
    try:
        user = sign_up(body.email, body.password)
        return {"message": "Account created successfully", **user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(body: AuthRequest):
    try:
        data = sign_in(body.email, body.password)
        return data
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
def logout(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else ""
    sign_out(token)
    return {"message": "Logged out"}


@router.get("/me")
def me(authorization: str = Header(None)):
    """Verify token and return current user — used by Streamlit on page load."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    token = authorization.replace("Bearer ", "")
    user  = get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user