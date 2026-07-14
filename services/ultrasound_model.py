import cv2
import numpy as np
import tensorflow as tf
from keras.applications.mobilenet_v2 import preprocess_input

IMG_SIZE = 224
MODEL_PATH = "ml_models/best_model.h5"        # update path if needed
CLASS_NAMES = ["HCC", "Hemangioma", "Normal"]  # alphabetical — matches your generator's class_indices order

_model = None  # loaded once, reused across calls (important for hackathon demo speed)


def _load_model(model_path=MODEL_PATH):
    global _model
    if _model is None:
        _model = tf.keras.models.load_model(model_path)
    return _model


def _center_crop_resize(img, target_size=IMG_SIZE):
    """Same logic as your data-normalization step: center-crop to square, then resize.
    Keeps inference consistent with how the model was trained."""
    h, w = img.shape[:2]
    min_dim = min(h, w)
    y_start = (h - min_dim) // 2
    x_start = (w - min_dim) // 2
    cropped = img[y_start:y_start + min_dim, x_start:x_start + min_dim]
    resized = cv2.resize(cropped, (target_size, target_size), interpolation=cv2.INTER_AREA)
    return resized


def predict_liver_condition(image_input, model_path=MODEL_PATH):
    """
    Takes either:
      - a file path (str) to an uploaded image, OR
      - a numpy array (already-read image, e.g. from cv2.imread or an uploaded file buffer)

    Returns:
      predicted_class: str
    """
    model = _load_model(model_path)

    # Accept both a path string and an already-loaded image array
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            raise ValueError(f"Could not read image at path: {image_input}")
    else:
        img = image_input  # assume it's already a numpy array (BGR or RGB)

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_processed = _center_crop_resize(img, IMG_SIZE)
    img_array = img_processed.astype(np.float32)
    img_array = preprocess_input(img_array)          # same MobileNetV2 normalization as training
    img_array = np.expand_dims(img_array, axis=0)     # add batch dimension

    preds = model.predict(img_array, verbose=0)[0]
    pred_idx = int(np.argmax(preds))
    pred_class = CLASS_NAMES[pred_idx]

    return pred_class