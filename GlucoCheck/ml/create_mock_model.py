"""
نموذج تجريبي للاختبار
This script creates a simple mock model for testing purposes
until the real dataset is available.
"""
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models

_current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(_current_dir, "models", "cnn_diabetes.h5")

def create_mock_model():
    """إنشاء نموذج بسيط للاختبار"""
    IMG_SIZE = 224
    NUM_CLASSES = 4
    
    model = models.Sequential([
        layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3)),
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(NUM_CLASSES, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # إنشاء بيانات وهمية للتدريب
    X = np.random.rand(100, IMG_SIZE, IMG_SIZE, 3).astype('float32')
    y = np.random.randint(0, NUM_CLASSES, 100)
    y = tf.keras.utils.to_categorical(y, NUM_CLASSES)
    
    print("تدريب النموذج التجريبي...")
    model.fit(X, y, epochs=5, verbose=1, batch_size=32)
    
    # حفظ النموذج
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save(MODEL_PATH)
    print(f"✓ تم حفظ النموذج في: {MODEL_PATH}")
    
    return model

if __name__ == "__main__":
    create_mock_model()
