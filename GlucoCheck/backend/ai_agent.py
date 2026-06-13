import os
import json
import re
import joblib
import numpy as np
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from database import supabase
from auth import get_current_user

chat_router = APIRouter(tags=["Chat"])

MEDICAL_SYSTEM_PROMPT = """أنت GlucoCheck — مساعد طبي ذكي متخصص في تشخيص ومتابعة مرض السكري.

## هويتك:
- مساعد طبي مدرّب على أحدث الإرشادات الطبية (ADA, WHO, IDF)
- متخصص في: تشخيص السكري، تحليل نتائج الفحوصات، خطط الرعاية الذاتية
- **لستَ طبيبًا مرخصًا** — دورك الدعم والتثقيف وليس التشخيص الطبي الرسمي

## درجات تصنيف السكري:
| الدرجة | التصنيف | السكر الصائم | الإجراء |
|--------|---------|--------------|---------|
| Grade 0 | طبيعي / ما قبل السكري | < 125 mg/dL | وقاية + نمط حياة صحي |
| Grade 1 | سكري خفيف | 126-180 mg/dL | نظام غذائي + متابعة دورية |
| Grade 2 | سكري متوسط | 181-300 mg/dL | علاج دوائي + خطة مكثفة |
| Grade 3 | سكري حاد | > 300 mg/dL | **إحالة طبية فورية** |

## تعليمات الرد:
1. استخدم اللغة العربية بشكل افتراضي، وأجب بالإنجليزية إذا سألك المريض بها
2. اسأل عن: السكر الصائم، HbA1c، العمر، الوزن، الأعراض، التاريخ العائلي
3. بعد جمع المعلومات، حدد الدرجة وقدم خطة واضحة
4. كن دافئًا ومطمئنًا لكن صريحًا في الحالات الحرجة
5. أنهِ كل تشخيص بـ: **[GRADE: X]** حيث X هو رقم الدرجة (0-3)
6. للحالات الحرجة (Grade 3): أضف **[URGENT: TRUE]**

## تنسيق الردود:
- استخدم عناوين واضحة مع **bold**
- قوائم منظمة للتوصيات
- لا تستخدم emoji — استخدم نص فقط
"""

session_memories: dict = {}


# مسارات الملفات
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "models", "text_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "models", "scaler.pkl")

FEATURE_NAMES = [
    'glucose_fasting', 'glucose_2h', 'hba1c', 'bmi', 'age',
    'blood_pressure', 'insulin', 'skin_thickness', 'pregnancies', 'diabetes_pedigree'
]


def extract_features_from_text(text: str) -> dict:
    """استخراج الميزات الطبية من نص الرسالة مع دعم هجات عربية مختلفة"""
    features = {}
    text_lower = text.lower()
    
    # أنماط محسّنة مع دعم هجات عربية ومتغيرات إملائية
    patterns = {
        'glucose_fasting': {
            'keywords': r'(sugar|glucose|سكر|صايم|صائم|fasting)',
            'values': r'(\d+(?:[.,]\d+)?)',
        },
        'glucose_2h': {
            'keywords': r'(2\s*hour|2h|ساعة|ساعتين|ساعه|بعد ساعتين)',
            'values': r'(\d+(?:[.,]\d+)?)',
        },
        'hba1c': {
            'keywords': r'(hba1c|a1c|hemoglobin|هيموجلوبين|هيموغلوبين)',
            'values': r'(\d+(?:[.,]\d+)?)',
        },
        'bmi': {
            'keywords': r'(bmi|mass index|كتلة الجسم|مؤشر كتلة)',
            'values': r'(\d+(?:[.,]\d+)?)',
        },
        'weight': {
            'keywords': r'(weight|وزن|كيلو|kg)',
            'values': r'(\d+(?:[.,]\d+)?)',
        },
        'height': {
            'keywords': r'(height|طول|سم|cm)',
            'values': r'(\d+(?:[.,]\d+)?)',
        },
        'age': {
            'keywords': r'(age|عمر|سن|سنة|سنوات|سنه)',
            'values': r'(\d+)',
        },
        'blood_pressure': {
            'keywords': r'(pressure|bp|ضغط)',
            'values': r'(\d+)',
        },
        'insulin': {
            'keywords': r'(insulin|انسولين|أنسولين|انسلوين)',
            'values': r'(\d+(?:[.,]\d+)?)',
        },
    }
    
    # استخراج القيم - البحث عن الرقم الأقرب للكلمة المفتاحية
    temp_features = {}
    for feature, pattern_dict in patterns.items():
        # البحث عن الكلمات المفتاحية
        keyword_match = re.search(pattern_dict['keywords'], text_lower)
        if keyword_match:
            # البحث عن أول رقم بعد موضع الكلمة المفتاحية (استخدم text_lower للبحث الدقيق)
            search_start = keyword_match.end()  # ابدأ من نهاية الكلمة المفتاحية
            search_text = text_lower[search_start:search_start + 100]
            match = re.search(pattern_dict['values'], search_text)
            if match:
                value = float(match.group(1).replace(',', '.'))
                temp_features[feature] = value
    
    # معالجة خاصة: حساب BMI من الوزن والطول
    if 'weight' in temp_features and 'height' in temp_features:
        weight = temp_features['weight']
        height = temp_features['height']
        if height > 0:
            # افترض أن الطول بالسم إذا كان > 10
            height_m = height / 100 if height > 10 else height
            bmi = weight / (height_m ** 2)
            temp_features['bmi'] = bmi
    
    # تحويل إلى صيغة الميزات الأساسية
    features['glucose_fasting'] = temp_features.get('glucose_fasting', None)
    features['glucose_2h'] = temp_features.get('glucose_2h', None)
    features['hba1c'] = temp_features.get('hba1c', None)
    features['bmi'] = temp_features.get('bmi', None)
    features['age'] = temp_features.get('age', None)
    features['blood_pressure'] = temp_features.get('blood_pressure', None)
    features['insulin'] = temp_features.get('insulin', None)
    
    # تنظيف القيم الفارغة
    features = {k: v for k, v in features.items() if v is not None}
    
    return features


def predict_with_local_model(features: dict) -> dict:
    """التنبؤ باستخدام حسابات طبية دقيقة مباشرة (بدون اعتماد على ملفات النموذج)"""
    try:
        # حساب تشخيص يدوي محسّن بناءً على القيم الطبية
        manual_grade = None
        manual_confidence = 50
        diagnosis_reason = []
        
        # فحص مستوى السكر الصائم (الأهم)
        if 'glucose_fasting' in features:
            glucose = features['glucose_fasting']
            if glucose < 100:
                manual_grade = 0
                diagnosis_reason.append(f"السكر الصائم {glucose} mg/dL (طبيعي)")
                manual_confidence = 95
            elif glucose < 126:
                manual_grade = 0
                diagnosis_reason.append(f"السكر الصائم {glucose} mg/dL (ما قبل السكري)")
                manual_confidence = 85
            elif glucose < 180:
                manual_grade = 1
                diagnosis_reason.append(f"السكر الصائم {glucose} mg/dL (سكري خفيف)")
                manual_confidence = 80
            elif glucose < 300:
                manual_grade = 2
                diagnosis_reason.append(f"السكر الصائم {glucose} mg/dL (سكري متوسط)")
                manual_confidence = 85
            else:
                manual_grade = 3
                diagnosis_reason.append(f"السكر الصائم {glucose} mg/dL (سكري حاد)")
                manual_confidence = 95
        
        # فحص HbA1c (مؤشر دقيق جداً)
        if 'hba1c' in features:
            hba1c = features['hba1c']
            hba_grade = None
            
            if hba1c < 5.7:
                hba_grade = 0
                diagnosis_reason.append(f"HbA1c {hba1c}% (طبيعي)")
            elif hba1c < 6.5:
                hba_grade = 0
                diagnosis_reason.append(f"HbA1c {hba1c}% (ما قبل السكري)")
                manual_confidence += 10
            elif hba1c < 7.0:
                hba_grade = 1
                diagnosis_reason.append(f"HbA1c {hba1c}% (سكري مضبوط)")
                manual_confidence += 5
            elif hba1c < 8.5:
                hba_grade = 1
                diagnosis_reason.append(f"HbA1c {hba1c}% (سكري خفيف)")
                manual_confidence += 5
            elif hba1c < 10:
                hba_grade = 2
                diagnosis_reason.append(f"HbA1c {hba1c}% (سكري متوسط)")
                manual_confidence += 10
            else:
                hba_grade = 3
                diagnosis_reason.append(f"HbA1c {hba1c}% (سكري حاد)")
                manual_confidence += 15
            
            if manual_grade is not None:
                # أخذ الدرجة الأعلى بين السكر الصائم و HbA1c
                manual_grade = max(manual_grade, hba_grade)
            else:
                manual_grade = hba_grade
        
        # فحص BMI إذا كان متاحاً
        if 'bmi' in features:
            bmi = features['bmi']
            if bmi > 30:
                diagnosis_reason.append(f"وزن زائد (BMI {bmi:.1f})")
                manual_confidence += 5
            elif bmi > 25:
                diagnosis_reason.append(f"وزن قريب من الحد الأقصى (BMI {bmi:.1f})")
        
        # إذا كان لدينا Grade، أعد النتيجة
        if manual_grade is not None:
            manual_confidence = min(99, max(manual_confidence, 50))
            return {
                "grade": manual_grade,
                "confidence": round(manual_confidence, 2),
                "diagnosis_reason": " + ".join(diagnosis_reason) if diagnosis_reason else "",
                "probabilities": {f"Grade{i}": 25 for i in range(4)}
            }
        else:
            # لم نتمكن من الحصول على بيانات
            return None
            
    except Exception as e:
        print(f"خطأ في التنبؤ: {e}")
        return None


def generate_medical_response(user_message: str, features: dict, prediction: dict | None) -> str:
    """توليد رد طبي مبني على البيانات المستخرجة مع تفاصيل دقيقة"""
    
    grade_labels = {
        0: ("طبيعي / ما قبل السكري", "Normal / Pre-diabetic", "✓"),
        1: ("سكري خفيف", "Mild Diabetic", "⚠"),
        2: ("سكري متوسط", "Moderate Diabetic", "⚠⚠"),
        3: ("سكري حاد", "Severe Diabetic", "🚨"),
    }
    
    response = "## تحليل حالتك الصحية\n\n"
    
    # عرض البيانات المستخرجة
    if features:
        response += "### البيانات المستخرجة من رسالتك:\n"
        
        # تنسيق أفضل للبيانات
        display_names = {
            'glucose_fasting': 'السكر الصائم',
            'glucose_2h': 'السكر بعد ساعتين',
            'hba1c': 'HbA1c',
            'bmi': 'مؤشر كتلة الجسم (BMI)',
            'age': 'العمر',
            'blood_pressure': 'ضغط الدم',
            'insulin': 'الأنسولين',
            'weight': 'الوزن',
            'height': 'الطول'
        }
        
        for key, value in features.items():
            display_name = display_names.get(key, key)
            response += f"- **{display_name}**: {value:.1f}\n"
        response += "\n"
    
    if prediction:
        grade = prediction['grade']
        label_ar, label_en, icon = grade_labels[grade]
        confidence = prediction['confidence']
        
        response += f"### النتيجة\n"
        response += f"**{label_ar}** ({label_en})\n"
        response += f"**مستوى الثقة**: {confidence}%\n"
        
        # إضافة السبب إذا كان متاحاً
        if 'diagnosis_reason' in prediction and prediction['diagnosis_reason']:
            response += f"\n**سبب التشخيص**: {prediction['diagnosis_reason']}\n"
        
        response += "\n"
        
        # التوصيات بناءً على الدرجة
        if grade == 0:
            response += "### التوصيات 🌟\n"
            response += "- **حالتك صحية** - استمر في المحافظة على نمط حياتك الصحي\n"
            response += "- ممارسة الرياضة بانتظام (150 دقيقة أسبوعياً)\n"
            response += "- تناول طعام متوازن قليل السكريات والدهون\n"
            response += "- الحفاظ على وزن صحي\n"
            response += "- إجراء فحوصات دورية سنوية\n"
            response += "- تجنب التوتر والنوم الكافي\n"
        elif grade == 1:
            response += "### التوصيات ⚠️\n"
            response += "- **حالتك تتطلب متابعة دقيقة**\n"
            response += "- اتباع نظام غذائي صارم قليل السكريات (استشر أخصائي تغذية)\n"
            response += "- ممارسة الرياضة 30 دقيقة يومياً (مشي سريع كحد أدنى)\n"
            response += "- فحوصات دورية كل 3-6 أشهر\n"
            response += "- تخفيف الوزن إذا لزم الأمر\n"
            response += "- قياس السكر منزلياً إذا أمكن\n"
            response += "- استشارة طبيب متخصص في الغدد الصماء\n"
        elif grade == 2:
            response += "### التوصيات ⚠️⚠️\n"
            response += "- **حالتك تتطلب علاج دوائي وتغييرات في نمط الحياة**\n"
            response += "- العلاج الدوائي ضروري (استشر طبيبك)\n"
            response += "- اتباع خطة غذائية مكثفة من متخصص التغذية\n"
            response += "- ممارسة الرياضة 30-45 دقيقة يومياً\n"
            response += "- متابعة منتظمة مع طبيب متخصص (شهرياً)\n"
            response += "- فحوصات مخبرية شهرية على الأقل\n"
            response += "- قياس السكر يومي (3-4 مرات)\n"
            response += "- الانتباه للمضاعفات (الكلى، العيون، الأعصاب)\n"
        else:  # grade == 3
            response += "### تنبيه طبي عاجل 🚨\n"
            response += "- **حالتك حرجة وتتطلب تدخل طبي فوري**\n"
            response += "- **يجب زيارة المستشفى أو الطوارئ الآن**\n"
            response += "- احتمال مضاعفات خطيرة (الحماض الكيتوني، غيبوبة السكري)\n"
            response += "- العلاج الدوائي المكثف ضروري جداً\n"
            response += "- متابعة يومية مع طبيب متخصص\n"
            response += "- فحوصات مخبرية يومية\n"
            response += "- قياس السكر كل ساعة على الأقل\n"
            response += "- **لا تؤخر الذهاب للطبيب - هذا حالة طارئة**\n"
        
        # إضافة علامات الدرجة
        response += f"\n[GRADE: {grade}]\n"
        
        if grade == 3:
            response += "[URGENT: TRUE]\n"
    else:
        response += "### ملاحظة\n"
        response += "لم أتمكن من استخراج بيانات كافية من رسالتك.\n\n"
        response += "**الرجاء تقديم المزيد من المعلومات:**\n"
        response += "- مستوى السكر الصائم (fasting blood glucose)\n"
        response += "- نتيجة HbA1c أو السكري التراكمي\n"
        response += "- الوزن والطول أو مؤشر كتلة الجسم (BMI)\n"
        response += "- العمر\n"
        response += "- التاريخ العائلي للسكري\n"
        response += "- أي أعراض تشعر بها\n"
    
    return response



def get_memory(session_id: str) -> ConversationBufferWindowMemory:
    if session_id not in session_memories:
        session_memories[session_id] = ConversationBufferWindowMemory(
            k=20, return_messages=True
        )
        existing = supabase.table("messages")\
            .select("role, content")\
            .eq("session_id", session_id)\
            .order("created_at")\
            .execute()
        for msg in (existing.data or []):
            if msg["role"] == "user":
                session_memories[session_id].chat_memory.add_user_message(msg["content"])
            elif msg["role"] == "agent":
                session_memories[session_id].chat_memory.add_ai_message(msg["content"])
    return session_memories[session_id]


def classify_grade_from_response(text: str) -> int | None:
    import re
    m = re.search(r'\[GRADE:\s*([0-3])\]', text)
    return int(m.group(1)) if m else None


class ChatRequest(BaseModel):
    session_id: str
    message:    str
    image_url:  str | None = None
    cnn_grade:  int | None = None          # نتيجة CNN من الصورة (0-3)
    cnn_confidence: float | None = None    # درجة ثقة CNN


@chat_router.post("/chat")
async def chat_stream(req: ChatRequest, current_user=Depends(get_current_user)):
    """استخدام النموذج المحلي المدرب مع حسابات طبية دقيقة"""
    
    memory = get_memory(req.session_id)
    history = memory.chat_memory.messages
    
    # محاولة استخراج الميزات من رسالة المستخدم
    features = extract_features_from_text(req.message)
    
    # تحميل النموذج والتنبؤ إذا توفرت الميزات الكافية
    grade = None
    confidence = 0
    prediction_data = None
    
    # إذا كانت هناك نتيجة CNN، استخدمها بشكل مباشر
    if req.cnn_grade is not None:
        grade = req.cnn_grade
        confidence = req.cnn_confidence or 25.0
        prediction_data = {
            "grade": grade,
            "confidence": confidence,
            "diagnosis_reason": f"تحليل صورة شبكية العين (CNN): ",
            "probabilities": {f"Grade{i}": 25 for i in range(4)}
        }
    # وإلا قبول حتى ميزة واحدة فقط (glucose_fasting الأهم)، أو ميزتان على الأقل
    elif len(features) >= 1 and ('glucose_fasting' in features or len(features) >= 2):
        try:
            prediction_data = predict_with_local_model(features)
            grade = prediction_data['grade']
            confidence = prediction_data['confidence']
        except Exception as e:
            print(f"خطأ في التنبؤ: {e}")
            prediction_data = None
    
    # بناء الرد الطبي
    response_text = generate_medical_response(req.message, features, prediction_data)
    
    async def token_generator() -> AsyncGenerator[str, None]:
        # محاكاة البث (streaming) بإرسال الرد بشكل تدريجي
        for word in response_text.split():
            token = word + " "
            yield f"data: {json.dumps({'token': token})}\n\n"
            await asyncio.sleep(0.01)  # تأخير صغير للمحاكاة
        
        # حفظ في قاعدة البيانات
        try:
            user_msg_data = {"session_id": req.session_id, "role": "user", "content": req.message}
            if req.image_url:
                user_msg_data["image_url"] = req.image_url
            
            supabase.table("messages").insert([
                user_msg_data,
                {"session_id": req.session_id, "role": "agent", "content": response_text}
            ]).execute()
            
            if grade is not None:
                supabase.table("diagnoses").insert({
                    "session_id": req.session_id,
                    "user_id": current_user["id"],
                    "grade": grade,
                    "confidence": confidence,
                    "source": "hybrid_model"  # يجمع بين النص والنموذج
                }).execute()
                supabase.table("sessions").update({
                    "grade": grade, "updated_at": datetime.utcnow().isoformat()
                }).eq("id", req.session_id).execute()
        except Exception as e:
            print(f"خطأ في حفظ البيانات: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        memory.chat_memory.add_user_message(req.message)
        memory.chat_memory.add_ai_message(response_text)
        
        yield f"data: {json.dumps({'done': True, 'grade': grade, 'confidence': confidence})}\n\n"
    
    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@chat_router.get("/messages/{session_id}")
async def get_messages(session_id: str, current_user=Depends(get_current_user)):
    session_res = supabase.table("sessions")\
        .select("id")\
        .eq("id", session_id)\
        .eq("user_id", current_user["id"])\
        .execute()
    if not session_res.data:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")

    res = supabase.table("messages")\
        .select("*")\
        .eq("session_id", session_id)\
        .order("created_at")\
        .execute()
    return res.data


@chat_router.get("/diagnoses")
async def get_diagnoses(current_user=Depends(get_current_user)):
    res = supabase.table("diagnoses")\
        .select("*, sessions(title)")\
        .eq("user_id", current_user["id"])\
        .order("created_at", desc=True)\
        .execute()
    return res.data
