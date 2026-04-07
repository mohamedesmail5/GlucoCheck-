"""
DiabetesAI — Data Engineer Layer
عضو: Abdelrahman (عبدالرحمن)
المهمة: جمع البيانات + بناء قاعدة البيانات + Data Pipeline

المسؤوليات:
  1. جمع بيانات المرضى (PIMA, APTOS, Kaggle Diabetic Retinopathy)
  2. تنظيف البيانات وتوحيد الصيغة
  3. رفع البيانات على Supabase
  4. إنشاء الجداول والعلاقات
  5. إعداد بيانات تدريب النماذج
"""

import os
import json
import uuid
import pandas as pd
import numpy as np
from supabase import create_client, Client
from datetime import datetime, timedelta
import random

# ─── Supabase Config ─────────────────────────────────────────────────────────
SUPABASE_URL = "https://hvarbaylkygctkindmsb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2YXJiYXlsa3lnY3RraW5kbXNiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTU1OTk4NSwiZXhwIjoyMDkxMTM1OTg1fQ.uHXUezhElPKP5uxE8_Bxy2Lp_76LFIjhnfR9kTTMhjc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: VERIFY CONNECTION
# ═══════════════════════════════════════════════════════════════════════════════
def verify_connection():
    try:
        res = supabase.table("users").select("id").limit(1).execute()
        print("✓ Supabase connected successfully")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: LOAD CLINICAL DATASET (PIMA Indians Diabetes)
# ═══════════════════════════════════════════════════════════════════════════════
def load_pima_dataset(csv_path: str = "data/diabetes.csv") -> pd.DataFrame:
    """
    Load and clean PIMA Indians Diabetes Dataset.
    Download from: https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database
    Columns: Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin,
             BMI, DiabetesPedigreeFunction, Age, Outcome
    """
    if not os.path.exists(csv_path):
        print(f"⚠ Dataset not found at {csv_path} — generating synthetic data")
        return generate_synthetic_clinical_data()

    df = pd.read_csv(csv_path)

    # Replace 0s with NaN for medical columns (can't be 0)
    zero_not_allowed = ['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI']
    df[zero_not_allowed] = df[zero_not_allowed].replace(0, np.nan)

    # Fill NaN with median
    df.fillna(df.median(numeric_only=True), inplace=True)

    # Map binary Outcome → 4-grade system
    def map_grade(row):
        g = row['Glucose']
        if g < 125:  return 0
        if g < 181:  return 1
        if g < 301:  return 2
        return 3

    df['grade'] = df.apply(map_grade, axis=1)
    df = df.rename(columns={
        'Pregnancies':              'pregnancies',
        'Glucose':                  'glucose_fasting',
        'BloodPressure':            'blood_pressure',
        'SkinThickness':            'skin_thickness',
        'Insulin':                  'insulin',
        'BMI':                      'bmi',
        'DiabetesPedigreeFunction': 'diabetes_pedigree',
        'Age':                      'age',
    })

    print(f"✓ Loaded PIMA dataset: {len(df)} records")
    print(f"  Grade distribution:\n{df['grade'].value_counts().sort_index()}")
    return df


def generate_synthetic_clinical_data(n: int = 5000) -> pd.DataFrame:
    """Generate realistic synthetic clinical data if no real dataset available."""
    np.random.seed(42)
    rows = []
    grade_configs = [
        (0, 80,  125, 5.0, 5.5),
        (1, 126, 180, 6.5, 7.5),
        (2, 181, 300, 7.5, 9.5),
        (3, 300, 450, 9.5, 14.0),
    ]
    for grade, glu_lo, glu_hi, hba1c_lo, hba1c_hi in grade_configs:
        n_g = n // 4
        glucose = np.random.uniform(glu_lo, glu_hi, n_g)
        rows.append(pd.DataFrame({
            'glucose_fasting':  glucose,
            'blood_pressure':   np.random.normal(75 + grade*8, 10, n_g).clip(50, 130),
            'skin_thickness':   np.random.normal(20 + grade*5, 8, n_g).clip(5, 60),
            'insulin':          np.random.exponential(80 + grade*30, n_g).clip(10, 500),
            'bmi':              np.random.normal(23 + grade*4, 5, n_g).clip(15, 55),
            'diabetes_pedigree':np.random.exponential(0.3 + grade*0.15, n_g).clip(0.05, 2.5),
            'age':              np.random.normal(35 + grade*6, 12, n_g).clip(18, 90).astype(int),
            'pregnancies':      np.random.poisson(grade + 1, n_g),
            'hba1c':            np.random.uniform(hba1c_lo, hba1c_hi, n_g),
            'grade':            grade
        }))
    df = pd.concat(rows, ignore_index=True).sample(frac=1, random_state=42)
    print(f"✓ Generated synthetic dataset: {len(df)} records")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: EXPORT CLEAN TRAINING DATA
# ═══════════════════════════════════════════════════════════════════════════════
def export_training_data(df: pd.DataFrame, output_path: str = "data/training_data.csv"):
    os.makedirs("data", exist_ok=True)
    features = ['glucose_fasting','blood_pressure','skin_thickness',
                'insulin','bmi','diabetes_pedigree','age','pregnancies','grade']
    available = [c for c in features if c in df.columns]
    df[available].to_csv(output_path, index=False)
    print(f"✓ Training data exported → {output_path} ({len(df)} rows)")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: SEED DEMO DATA INTO SUPABASE
# ═══════════════════════════════════════════════════════════════════════════════
def seed_demo_users():
    """Insert demo users for testing."""
    import bcrypt

    demo_users = [
        {"email": "demo@diabetesai.com",  "full_name": "مريض تجريبي",   "password": "demo1234"},
        {"email": "ahmed@diabetesai.com", "full_name": "أحمد محمد",     "password": "test1234"},
        {"email": "sara@diabetesai.com",  "full_name": "سارة أحمد",     "password": "test1234"},
    ]

    inserted = []
    for u in demo_users:
        # Check if exists
        existing = supabase.table("users").select("id").eq("email", u["email"]).execute()
        if existing.data:
            print(f"  Skip (exists): {u['email']}")
            continue

        hashed = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt()).decode()
        res = supabase.table("users").insert({
            "email":         u["email"],
            "password_hash": hashed,
            "full_name":     u["full_name"]
        }).execute()
        inserted.append(res.data[0])
        print(f"  ✓ Inserted user: {u['email']}")

    return inserted


def seed_demo_sessions(user_ids: list):
    """Insert demo sessions and diagnoses for dashboard testing."""
    grades = [0, 1, 2, 1, 3, 0, 2, 1]
    messages_samples = [
        ("سكر الصائم 95 mg/dL، كل شيء طبيعي", "ممتاز! مستوى السكر طبيعي جداً. [GRADE: 0]"),
        ("سكر الصائم 150 mg/dL", "مستوى السكر مرتفع قليلاً. تحتاج متابعة. [GRADE: 1]"),
        ("HbA1c 9.2%, سكر 250 mg/dL", "سكري متوسط — تحتاج علاجاً دوائياً. [GRADE: 2]"),
        ("سكر 340 mg/dL وأعراض شديدة", "حالة حرجة — راجع طبيباً فوراً! [GRADE: 3] [URGENT: TRUE]"),
    ]

    for uid in user_ids[:2]:
        for i, grade in enumerate(grades[:4]):
            # Create session
            created_at = (datetime.now() - timedelta(days=i*3)).isoformat()
            session_res = supabase.table("sessions").insert({
                "user_id":    uid,
                "title":      f"جلسة فحص #{i+1}",
                "grade":      grade,
                "created_at": created_at,
                "updated_at": created_at,
            }).execute()
            sid = session_res.data[0]["id"]

            # Add messages
            user_msg, agent_msg = messages_samples[i % len(messages_samples)]
            supabase.table("messages").insert([
                {"session_id": sid, "role": "user",  "content": user_msg,  "created_at": created_at},
                {"session_id": sid, "role": "agent", "content": agent_msg, "created_at": created_at},
            ]).execute()

            # Add diagnosis
            supabase.table("diagnoses").insert({
                "session_id": sid,
                "user_id":    uid,
                "grade":      grade,
                "confidence": round(random.uniform(88, 99), 2),
                "source":     "text",
                "created_at": created_at,
            }).execute()

            print(f"  ✓ Session #{i+1} → Grade {grade} for user {uid[:8]}...")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5: VERIFY ALL TABLES
# ═══════════════════════════════════════════════════════════════════════════════
def verify_tables():
    tables = ["users", "sessions", "messages", "diagnoses"]
    print("\n=== Table Verification ===")
    for t in tables:
        try:
            res = supabase.table(t).select("*", count="exact").limit(0).execute()
            count = res.count if hasattr(res, 'count') else '?'
            print(f"  ✓ {t:<12} — OK")
        except Exception as e:
            print(f"  ✗ {t:<12} — MISSING: {e}")
            print(f"      → Run schema.sql in Supabase SQL Editor first!")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("DiabetesAI — Data Engineer Pipeline")
    print("Engineer: Abdelrahman")
    print("=" * 60)

    # 1. Verify connection
    if not verify_connection():
        print("\n✗ Fix connection before proceeding.")
        exit(1)

    # 2. Verify tables exist
    verify_tables()

    # 3. Load + clean dataset
    print("\n── Step 3: Load Clinical Dataset ──────────────────────────")
    df = load_pima_dataset("data/diabetes.csv")

    # 4. Export training data
    print("\n── Step 4: Export Training Data ───────────────────────────")
    export_training_data(df)

    # 5. Seed demo data
    print("\n── Step 5: Seed Demo Data ─────────────────────────────────")
    demo_users = seed_demo_users()
    if demo_users:
        user_ids = [u["id"] for u in demo_users]
        seed_demo_sessions(user_ids)

    print("\n" + "=" * 60)
    print("✓ Data pipeline complete!")
    print("  → Training data: data/training_data.csv")
    print("  → Demo users seeded in Supabase")
    print("  → Run: python ../ml/train_text_model.py --data data/training_data.csv")
    print("=" * 60)
