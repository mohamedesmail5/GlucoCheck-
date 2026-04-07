# DiabetesAI — Smart Diabetes Diagnosis Agent

**العام الدراسي:** 2025 / 2026

---

## فريق العمل

| العضو | الدور | المسؤوليات الرئيسية |
|-------|-------|----------------------|
| **Kareem Mohamed** | Frontend — Chat | Chat Interface + Streaming + رفع الصور + Landing + Login + Register |
| **Eslam Mohamed** | Frontend — Dashboard | Dashboard + سجل الجلسات + Notifications + React Query |
| **Mohamed Esmail** | Backend — AI Agent | LangChain Agent + System Prompt + CNN Integration + Session Isolation |
| **Ziad Mohamed** | Backend — Auth & DB | JWT + bcrypt + REST APIs + File Upload + Supabase Storage |
| **Abdelrahman Mohamed** | Data Engineer | جمع البيانات + بناء قاعدة البيانات + Data Pipeline + Seed Data |

---

## هيكل المشروع

```
DiabetesAI/
├── frontend/                    ← React 18 + Tailwind CSS (Kareem + Eslam)
│   └── src/
│       ├── pages/
│       │   ├── Landing.jsx      ← صفحة الترحيب
│       │   ├── Login.jsx        ← تسجيل الدخول (JWT)
│       │   ├── Register.jsx     ← إنشاء حساب
│       │   ├── Chat.jsx         ← واجهة المحادثة + Streaming + رفع الصور
│       │   ├── Dashboard.jsx    ← لوحة التحكم (Recharts)
│       │   ├── History.jsx      ← سجل الجلسات
│       │   └── Profile.jsx      ← الملف الشخصي
│       ├── components/
│       │   └── Layout.jsx       ← Sidebar + Navigation
│       └── lib/
│           ├── auth.js          ← Zustand store + JWT
│           └── api.js           ← React Query hooks
│
├── backend/                     ← FastAPI + Python (Mohamed + Ziad)
│   ├── main.py
│   ├── auth.py                  ← Register / Login / Profile / Delete
│   ├── ai_agent.py              ← LangChain AI Agent + SSE Streaming
│   ├── sessions.py              ← Sessions CRUD + File Upload + Stats
│   ├── database.py              ← Supabase client
│   ├── routes.py
│   └── requirements.txt
│
├── ml/                          ← Machine Learning 98%+ accuracy
│   ├── train_image_model.py     ← EfficientNetB0 CNN
│   ├── train_text_model.py      ← XGBoost Ensemble
│   └── requirements.txt
│
└── data_engineer/               ← Data Pipeline (Abdelrahman)
    ├── pipeline.py              ← جمع + تنظيف + رفع البيانات
    └── requirements.txt
```

---

## Supabase

```
URL:  https://hvarbaylkygctkindmsb.supabase.co
```

الجداول: `users` — `sessions` — `messages` — `diagnoses`

Storage bucket: `medical-images` (Public ON)

---

## تشغيل المشروع

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Data Pipeline (Abdelrahman)
cd data_engineer && pip install -r requirements.txt && python pipeline.py

# ML Training
cd ml && python train_text_model.py
cd ml && python train_image_model.py
```

---

## درجات السكري

| Grade | التصنيف | السكر الصائم | الإجراء |
|-------|---------|--------------|---------|
| 0 | طبيعي | < 125 mg/dL | وقاية |
| 1 | خفيف | 126-180 mg/dL | نظام غذائي |
| 2 | متوسط | 181-300 mg/dL | أدوية |
| 3 | حاد | > 300 mg/dL | إحالة فورية |

---

## دور عبدالرحمن — Data Engineer

1. تحميل PIMA Diabetes Dataset من Kaggle
2. تنظيف البيانات ومعالجة القيم المفقودة
3. تصنيف البيانات إلى 4 درجات
4. تصدير بيانات التدريب لنماذج ML
5. Seed Data على Supabase للاختبار
6. التحقق من سلامة قاعدة البيانات

---

DiabetesAI — 2024/2025
