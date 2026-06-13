"""
اختبار وظيفة رفع الصور
Test script to verify image upload and CNN prediction functionality
"""
import os
import sys
import numpy as np
from PIL import Image
import tempfile

# Add ML directory to path
_current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _current_dir)

from train_image_model import predict_image

def test_image_prediction():
    """اختبار التنبؤ بالصور"""
    
    print("=" * 60)
    print("اختبار نموذج التنبؤ بالصور")
    print("Testing Image Prediction Model")
    print("=" * 60)
    
    # إنشاء صورة اختبار وهمية
    img_array = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
    img = Image.fromarray(img_array)
    
    # حفظ الصورة مؤقتاً
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp_path = tmp.name
        img.save(tmp_path)
    
    try:
        model_path = os.path.join(_current_dir, "models", "cnn_diabetes.h5")
        
        print(f"\nمسار النموذج: {model_path}")
        print(f"Model path: {model_path}")
        
        if not os.path.exists(model_path):
            print(f"❌ ملف النموذج غير موجود: {model_path}")
            print(f"❌ Model file not found: {model_path}")
            return False
        
        print(f"✓ تم العثور على ملف النموذج")
        print(f"✓ Model file found")
        
        # اختبار التنبؤ
        print("\nجاري التنبؤ...")
        print("Making prediction...")
        
        result = predict_image(tmp_path, model_path=model_path)
        
        print("\n✓ نتيجة التنبؤ:")
        print("✓ Prediction result:")
        print(f"  - الدرجة / Grade: {result['grade']}")
        print(f"  - التصنيف العربي / Arabic Label: {result['label_ar']}")
        print(f"  - التصنيف الإنجليزي / English Label: {result['label_en']}")
        print(f"  - الثقة / Confidence: {result['confidence']}%")
        print(f"  - الاحتماليات / Probabilities: {result['probabilities']}")
        
        print("\n" + "=" * 60)
        print("✓ النموذج يعمل بنجاح!")
        print("✓ Model works successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ في التنبؤ: {e}")
        print(f"❌ Prediction error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # حذف الملف المؤقت
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

if __name__ == "__main__":
    success = test_image_prediction()
    sys.exit(0 if success else 1)
