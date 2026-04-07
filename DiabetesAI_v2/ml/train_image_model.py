"""
DiabetesAI — CNN Image Model Training
Dataset: APTOS 2019 / Diabetic Retinopathy Kaggle
Model: EfficientNetB0 (Transfer Learning) — Target Accuracy: 98%+
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
import joblib

# ─── Config ────────────────────────────────────────────────────────────────────
IMG_SIZE     = 224
BATCH_SIZE   = 32
EPOCHS_FINE  = 30
EPOCHS_WARM  = 5
NUM_CLASSES  = 4          # Grade 0,1,2,3
MODEL_PATH   = "models/cnn_diabetes.h5"
DATASET_PATH = "data/retina_images"    # Folder: 0/, 1/, 2/, 3/

# ─── Data Augmentation ─────────────────────────────────────────────────────────
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.1,
    height_shift_range=0.1,
    shear_range=0.1,
    zoom_range=0.15,
    horizontal_flip=True,
    vertical_flip=True,
    brightness_range=[0.85, 1.15],
    fill_mode='nearest',
    validation_split=0.15
)

val_datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.15
)

def get_generators(dataset_path):
    train_gen = train_datagen.flow_from_directory(
        dataset_path,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training',
        shuffle=True
    )
    val_gen = val_datagen.flow_from_directory(
        dataset_path,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation',
        shuffle=False
    )
    return train_gen, val_gen


# ─── Model Architecture ─────────────────────────────────────────────────────────
def build_model(num_classes=NUM_CLASSES):
    base_model = EfficientNetB0(
        weights='imagenet',
        include_top=False,
        input_shape=(IMG_SIZE, IMG_SIZE, 3)
    )
    # Phase 1: Freeze base
    base_model.trainable = False

    inputs  = tf.keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    x       = base_model(inputs, training=False)
    x       = layers.GlobalAveragePooling2D()(x)
    x       = layers.BatchNormalization()(x)
    x       = layers.Dense(512, activation='relu')(x)
    x       = layers.Dropout(0.4)(x)
    x       = layers.Dense(256, activation='relu')(x)
    x       = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)

    model = models.Model(inputs, outputs)
    model.compile(
        optimizer=optimizers.Adam(1e-3),
        loss='categorical_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )
    return model, base_model


# ─── Training Pipeline ──────────────────────────────────────────────────────────
def train(dataset_path=DATASET_PATH):
    os.makedirs("models", exist_ok=True)

    train_gen, val_gen = get_generators(dataset_path)
    model, base_model  = build_model()

    cb_list = [
        callbacks.ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor='val_accuracy'),
        callbacks.EarlyStopping(patience=7, restore_best_weights=True, monitor='val_accuracy'),
        callbacks.ReduceLROnPlateau(factor=0.3, patience=3, min_lr=1e-7, monitor='val_loss'),
        callbacks.TensorBoard(log_dir='logs/image_model')
    ]

    print("── Phase 1: Warm-up (frozen base) ─────────────")
    history_warm = model.fit(
        train_gen, validation_data=val_gen,
        epochs=EPOCHS_WARM, callbacks=cb_list
    )

    # Phase 2: Fine-tune top 40 layers of EfficientNet
    base_model.trainable = True
    for layer in base_model.layers[:-40]:
        layer.trainable = False

    model.compile(
        optimizer=optimizers.Adam(1e-5),
        loss='categorical_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )

    print("── Phase 2: Fine-tuning ────────────────────────")
    history_fine = model.fit(
        train_gen, validation_data=val_gen,
        epochs=EPOCHS_FINE, callbacks=cb_list
    )

    # Evaluate
    val_gen.reset()
    loss, acc, auc = model.evaluate(val_gen)
    print(f"\n✓ Final Validation Accuracy : {acc*100:.2f}%")
    print(f"✓ Final Validation AUC      : {auc:.4f}")

    # Confusion matrix
    val_gen.reset()
    preds = model.predict(val_gen)
    y_pred = np.argmax(preds, axis=1)
    y_true = val_gen.classes
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred,
          target_names=['Grade0','Grade1','Grade2','Grade3']))

    return model, history_fine


# ─── Inference ──────────────────────────────────────────────────────────────────
def predict_image(image_path: str, model_path: str = MODEL_PATH):
    """Predict diabetes grade from a retinal image."""
    from tensorflow.keras.preprocessing import image as keras_image

    model = tf.keras.models.load_model(model_path)
    img   = keras_image.load_img(image_path, target_size=(IMG_SIZE, IMG_SIZE))
    arr   = keras_image.img_to_array(img) / 255.0
    arr   = np.expand_dims(arr, axis=0)

    probs = model.predict(arr)[0]
    grade = int(np.argmax(probs))
    conf  = float(probs[grade])

    labels = {
        0: ("طبيعي / ما قبل السكري", "Normal / Pre-diabetic"),
        1: ("سكري خفيف",              "Mild Diabetic"),
        2: ("سكري متوسط",             "Moderate Diabetic"),
        3: ("سكري حاد",               "Severe Diabetic")
    }

    return {
        "grade":       grade,
        "label_ar":    labels[grade][0],
        "label_en":    labels[grade][1],
        "confidence":  round(conf * 100, 2),
        "probabilities": {f"Grade{i}": round(float(p)*100, 2) for i, p in enumerate(probs)}
    }


if __name__ == "__main__":
    # Usage: python train_image_model.py
    # Place images in data/retina_images/0/, /1/, /2/, /3/
    model, history = train()
    print("Model saved →", MODEL_PATH)
