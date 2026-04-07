"""
DiabetesAI — Text / Clinical Data Model
Input : Patient clinical features (glucose, HbA1c, BMI, age, etc.)
Model : XGBoost Ensemble — Target Accuracy: 98%+
Output: Grade 0-3 + probability scores
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import joblib
import os

# ─── Config ────────────────────────────────────────────────────────────────────
MODEL_PATH  = "models/text_model.pkl"
SCALER_PATH = "models/scaler.pkl"

# ─── Feature Definitions ────────────────────────────────────────────────────────
FEATURES = [
    'glucose_fasting',      # mg/dL  (fasting blood glucose)
    'glucose_2h',           # mg/dL  (2-hour post-load glucose)
    'hba1c',                # %      (HbA1c)
    'bmi',                  # kg/m²
    'age',                  # years
    'blood_pressure',       # mmHg (systolic)
    'insulin',              # µU/mL
    'skin_thickness',       # mm
    'pregnancies',          # count (0 for males)
    'diabetes_pedigree',    # function score
]

GRADE_RULES = {
    # Grade based on fasting glucose (WHO criteria) — used for synthetic data
    0: (0, 125),     # Normal
    1: (126, 180),   # Mild
    2: (181, 300),   # Moderate
    3: (301, 9999),  # Severe
}


# ─── Synthetic Dataset (fallback if no real CSV) ────────────────────────────────
def generate_synthetic_data(n=10000, seed=42):
    """Generate realistic synthetic clinical data for 4-class diabetes grading."""
    np.random.seed(seed)
    rows = []

    for grade in range(4):
        n_per = n // 4
        glu_lo, glu_hi = list(GRADE_RULES.values())[grade]
        glu_hi = min(glu_hi, 500)

        glucose_f = np.random.uniform(max(60, glu_lo), glu_hi, n_per)
        rows.append(pd.DataFrame({
            'glucose_fasting' : glucose_f,
            'glucose_2h'      : glucose_f * np.random.uniform(1.1, 1.4, n_per),
            'hba1c'           : 4.5 + (grade * 1.8) + np.random.normal(0, 0.4, n_per),
            'bmi'             : np.random.normal(22 + grade*4, 4, n_per).clip(15, 50),
            'age'             : np.random.normal(35 + grade*5, 12, n_per).clip(18, 90),
            'blood_pressure'  : np.random.normal(70 + grade*8, 10, n_per).clip(50, 130),
            'insulin'         : np.random.exponential(80 + grade*30, n_per).clip(10, 500),
            'skin_thickness'  : np.random.normal(20 + grade*5, 8, n_per).clip(5, 60),
            'pregnancies'     : np.random.poisson(grade + 1, n_per),
            'diabetes_pedigree': np.random.exponential(0.3 + grade*0.15, n_per).clip(0.05, 2.5),
            'grade'           : grade
        }))

    df = pd.concat(rows, ignore_index=True).sample(frac=1, random_state=seed)
    return df


# ─── Preprocessing ──────────────────────────────────────────────────────────────
def load_and_preprocess(csv_path=None):
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        print("No CSV found — using synthetic data")
        df = generate_synthetic_data()

    df = df.dropna()
    X  = df[FEATURES].values
    y  = df['grade'].values.astype(int)
    return X, y


# ─── Model Training ─────────────────────────────────────────────────────────────
def train(csv_path=None):
    os.makedirs("models", exist_ok=True)

    X, y = load_and_preprocess(csv_path)

    # SMOTE to balance classes
    smote = SMOTE(random_state=42)
    X, y  = smote.fit_resample(X, y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )

    # Scale features
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)
    joblib.dump(scaler, SCALER_PATH)

    # ── XGBoost (Primary) ───────────────────────────────────────────────────────
    xgb = XGBClassifier(
        n_estimators     = 800,
        max_depth        = 7,
        learning_rate    = 0.03,
        subsample        = 0.85,
        colsample_bytree = 0.85,
        min_child_weight = 2,
        gamma            = 0.1,
        reg_alpha        = 0.05,
        reg_lambda       = 1.5,
        use_label_encoder= False,
        eval_metric      = 'mlogloss',
        random_state     = 42,
        n_jobs           = -1
    )

    # ── Random Forest (Ensemble member) ─────────────────────────────────────────
    rf = RandomForestClassifier(
        n_estimators = 500,
        max_depth    = 15,
        min_samples_split = 4,
        random_state = 42,
        n_jobs       = -1
    )

    # ── Gradient Boosting ────────────────────────────────────────────────────────
    gb = GradientBoostingClassifier(
        n_estimators    = 400,
        max_depth       = 6,
        learning_rate   = 0.05,
        subsample       = 0.85,
        random_state    = 42
    )

    # ── Voting Ensemble ──────────────────────────────────────────────────────────
    ensemble = VotingClassifier(
        estimators=[('xgb', xgb), ('rf', rf), ('gb', gb)],
        voting='soft',
        weights=[3, 2, 2]
    )

    print("Training ensemble model…")
    ensemble.fit(X_train, y_train)

    # ── Evaluate ─────────────────────────────────────────────────────────────────
    y_pred = ensemble.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    print(f"\n✓ Test Accuracy : {acc*100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred,
          target_names=['Grade0','Grade1','Grade2','Grade3']))

    # Cross-validation
    cv_scores = cross_val_score(ensemble, X, y, cv=5, scoring='accuracy', n_jobs=-1)
    print(f"\n5-Fold CV Accuracy : {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")

    joblib.dump(ensemble, MODEL_PATH)
    print(f"\nModel saved → {MODEL_PATH}")
    return ensemble


# ─── Inference ──────────────────────────────────────────────────────────────────
def predict_clinical(features: dict):
    """
    features dict keys: glucose_fasting, glucose_2h, hba1c, bmi, age,
                        blood_pressure, insulin, skin_thickness,
                        pregnancies, diabetes_pedigree
    """
    ensemble = joblib.load(MODEL_PATH)
    scaler   = joblib.load(SCALER_PATH)

    x = np.array([[features.get(f, 0) for f in FEATURES]])
    x = scaler.transform(x)

    grade    = int(ensemble.predict(x)[0])
    probs    = ensemble.predict_proba(x)[0]

    labels = {
        0: ("طبيعي / ما قبل السكري",  "Normal / Pre-diabetic",  "#22c55e"),
        1: ("سكري خفيف",               "Mild Diabetic",           "#eab308"),
        2: ("سكري متوسط",              "Moderate Diabetic",       "#f97316"),
        3: ("سكري حاد",                "Severe Diabetic",         "#ef4444"),
    }

    return {
        "grade"        : grade,
        "label_ar"     : labels[grade][0],
        "label_en"     : labels[grade][1],
        "color"        : labels[grade][2],
        "confidence"   : round(float(probs[grade]) * 100, 2),
        "probabilities": {f"Grade{i}": round(float(p)*100, 2) for i, p in enumerate(probs)}
    }


if __name__ == "__main__":
    model = train()
