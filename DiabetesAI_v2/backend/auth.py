"""
DiabetesAI — Authentication (JWT + bcrypt)
"""
import os
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from database import supabase

SECRET_KEY      = os.environ.get("SECRET_KEY", "diabetes_ai_super_secret_2025")
ALGORITHM       = "HS256"
ACCESS_EXPIRE   = 60 * 24        # 24 hours in minutes
REFRESH_EXPIRE  = 60 * 24 * 30  # 30 days

bearer = HTTPBearer()


# ─── Pydantic Models ───────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email:     EmailStr
    password:  str
    full_name: str

class LoginForm(BaseModel):
    email:    EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user: dict


# ─── Token Helpers ─────────────────────────────────────────────────────────────
def create_token(user_id: str, expires_minutes: int) -> str:
    exp = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode({"sub": user_id, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="توكن غير صالح أو منتهي الصلاحية")


async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    user_id = verify_token(creds.credentials)
    res = supabase.table("users").select("*").eq("id", user_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="المستخدم غير موجود")
    return res.data


# ─── Route Handlers ────────────────────────────────────────────────────────────
from fastapi import APIRouter

auth_router = APIRouter(tags=["Auth"])


@auth_router.post("/register", response_model=TokenResponse)
async def register(user: UserCreate):
    # Check if email exists
    existing = supabase.table("users").select("id").eq("email", user.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مسجل مسبقاً")

    # Hash password
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()

    # Insert user
    new = supabase.table("users").insert({
        "email":         user.email,
        "password_hash": hashed,
        "full_name":     user.full_name
    }).execute()

    uid = new.data[0]["id"]
    return TokenResponse(
        access_token  = create_token(uid, ACCESS_EXPIRE),
        refresh_token = create_token(uid, REFRESH_EXPIRE),
        user          = {"id": uid, "email": user.email, "full_name": user.full_name}
    )


@auth_router.post("/login", response_model=TokenResponse)
async def login(creds: LoginForm):
    res = supabase.table("users").select("*").eq("email", creds.email).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

    user = res.data[0]
    if not bcrypt.checkpw(creds.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

    return TokenResponse(
        access_token  = create_token(user["id"], ACCESS_EXPIRE),
        refresh_token = create_token(user["id"], REFRESH_EXPIRE),
        user          = {"id": user["id"], "email": user["email"], "full_name": user["full_name"]}
    )


@auth_router.get("/me")
async def me(current_user=Depends(get_current_user)):
    return {k: v for k, v in current_user.items() if k != "password_hash"}


@auth_router.put("/profile")
async def update_profile(data: dict, current_user=Depends(get_current_user)):
    allowed = {k: v for k, v in data.items() if k in ("full_name",)}
    if "password" in data:
        allowed["password_hash"] = bcrypt.hashpw(
            data["password"].encode(), bcrypt.gensalt()
        ).decode()
    supabase.table("users").update(allowed).eq("id", current_user["id"]).execute()
    return {"message": "تم التحديث بنجاح"}


@auth_router.delete("/account")
async def delete_account(current_user=Depends(get_current_user)):
    uid = current_user["id"]
    # Cascade: sessions → messages → diagnoses deleted via FK ON DELETE CASCADE
    supabase.table("users").delete().eq("id", uid).execute()
    return {"message": "تم حذف الحساب بنجاح"}
