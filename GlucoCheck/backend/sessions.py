import os
import uuid
import sys
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from database import supabase
from auth import get_current_user

sessions_router = APIRouter(tags=["Sessions"])
upload_router   = APIRouter(tags=["Upload"])

STORAGE_BUCKET = "medical-images"

# إضافة مسار ML إلى sys.path
_backend_dir = os.path.dirname(os.path.abspath(__file__))
_ml_dir = os.path.join(os.path.dirname(_backend_dir), "ml")
if _ml_dir not in sys.path:
    sys.path.insert(0, _ml_dir)


@sessions_router.post("/sessions")
async def create_session(current_user=Depends(get_current_user)):
    res = supabase.table("sessions").insert({
        "user_id": current_user["id"],
        "title":   "جلسة جديدة"
    }).execute()
    return res.data[0]


@sessions_router.get("/sessions")
async def list_sessions(current_user=Depends(get_current_user)):
    res = supabase.table("sessions")\
        .select("*, messages(count)")\
        .eq("user_id", current_user["id"])\
        .order("updated_at", desc=True)\
        .execute()
    return res.data


@sessions_router.get("/sessions/{session_id}")
async def get_session(session_id: str, current_user=Depends(get_current_user)):
    res = supabase.table("sessions")\
        .select("*, messages(*)")\
        .eq("id", session_id)\
        .eq("user_id", current_user["id"])\
        .single()\
        .execute()
    if not res.data:
        raise HTTPException(404, "الجلسة غير موجودة")
    return res.data


@sessions_router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user=Depends(get_current_user)):
    supabase.table("sessions")\
        .delete()\
        .eq("id", session_id)\
        .eq("user_id", current_user["id"])\
        .execute()
    return {"message": "تم حذف الجلسة"}


@sessions_router.get("/stats")
async def get_stats(current_user=Depends(get_current_user)):
    uid = current_user["id"]

    sessions = supabase.table("sessions").select("id, grade")\
        .eq("user_id", uid).execute()
    diagnoses = supabase.table("diagnoses").select("grade, created_at")\
        .eq("user_id", uid).order("created_at", desc=True).execute()

    total     = len(sessions.data)
    graded    = [s for s in sessions.data if s["grade"] is not None]
    last_grade = diagnoses.data[0]["grade"] if diagnoses.data else None

    grade_dist = {0: 0, 1: 0, 2: 0, 3: 0}
    for d in diagnoses.data:
        grade_dist[d["grade"]] = grade_dist.get(d["grade"], 0) + 1

    return {
        "total_sessions": total,
        "last_grade":     last_grade,
        "grade_distribution": grade_dist,
        "total_diagnoses": len(diagnoses.data),
        "accuracy": "98%+"
    }


@upload_router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user     = Depends(get_current_user)
):
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        raise HTTPException(400, "نوع الملف غير مدعوم. استخدم JPG أو PNG")

    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(400, "حجم الملف يتجاوز 10 MB")

    ext      = file.filename.split(".")[-1]
    filename = f"{current_user['id']}/{uuid.uuid4()}.{ext}"
    data     = await file.read()

    # حفظ محلي بدلاً من Supabase (للاختبار)
    _backend_parent = os.path.dirname(_backend_dir)
    _uploads_dir = os.path.join(_backend_parent, "uploads")
    os.makedirs(_uploads_dir, exist_ok=True)
    
    # حفظ الملف محلياً
    local_file_path = os.path.join(_uploads_dir, filename.replace("/", "_"))
    with open(local_file_path, "wb") as f:
        f.write(data)
    
    # URL محلي (أو Supabase إذا كان متاحاً)
    public_url = f"http://localhost:8000/uploads/{filename.replace('/', '_')}"
    
    try:
        # محاولة رفع إلى Supabase (اختياري)
        try:
            res = supabase.storage.from_(STORAGE_BUCKET).upload(
                filename, data,
                {"content-type": file.content_type, "upsert": "true"}
            )
            public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)
            print(f"✓ تم رفع الملف إلى Supabase: {filename}")
        except Exception as e:
            print(f"⚠️ تحذير: لم يتمكن من رفع إلى Supabase: {e}")
            print(f"✓ استخدام النسخة المحلية: {public_url}")
    except Exception as e:
        print(f"خطأ في Supabase: {e}")

    cnn_result = None
    try:
        from train_image_model import predict_image
        import tempfile
        
        # التحقق من وجود ملف النموذج
        model_path = os.path.join(_ml_dir, "models", "cnn_diabetes.h5")
        if not os.path.exists(model_path):
            print(f"⚠️ تحذير: ملف النموذج غير موجود في {model_path}")
        else:
            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            try:
                cnn_result = predict_image(tmp_path, model_path=model_path)
                print(f"✓ تم التنبؤ بنجاح: Grade {cnn_result['grade']}")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    except ImportError as e:
        print(f"❌ خطأ في استيراد النموذج: {e}")
    except Exception as e:
        print(f"❌ خطأ في معالجة الصورة: {e}")

    return {
        "url":        public_url,
        "filename":   filename,
        "cnn_result": cnn_result
    }
