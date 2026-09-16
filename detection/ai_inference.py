# """
# 🔸 PLACEHOLDER — file này dành cho người phụ trách AI.
# Sau khi train xong model (person detector + behavior classifier),
# copy file .pt vào thư mục weights/ và implement hàm bên dưới.

# Hàm này PHẢI trả về list dict theo đúng format:
# [
#     {"bbox": [xmin, ymin, xmax, ymax], "behaviour": "phone_use", "confidence": 0.95},
#     ...
# ]
# để views.py có thể lưu thẳng vào model Detection mà không cần sửa gì thêm.
# """

# def detect_cheating(image_path):
#     # TODO: load model YOLO/EfficientNet, chạy predict, trả kết quả đúng format trên
#     raise NotImplementedError("Chưa tích hợp model AI")

"""
Pipeline 2 giai đoạn: YOLOv8n pretrained (phát hiện người) -> ReXNet-150 (phân loại hành vi).
Model được load 1 lần duy nhất khi module này được import (lúc Django khởi động),
không load lại mỗi lần gọi detect_cheating() để tránh chậm.
"""
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms
from ultralytics import YOLO
import timm

BASE_DIR = Path(__file__).resolve().parent
WEIGHTS_DIR = BASE_DIR / "weights"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
EXPAND_RATIO = 0.2
IMG_SIZE = 224
CONF_THRESHOLD_PERSON = 0.4

# ---- Load model Stage 1: YOLOv8n pretrained COCO ----
_yolo_model = YOLO(str(WEIGHTS_DIR / "yolov8n.pt"))

# ---- Load model Stage 2: ReXNet-150 đã train ----
_checkpoint = torch.load(WEIGHTS_DIR / "rexnet_behavior_best.pt", map_location=DEVICE)
_class_names = _checkpoint["classes"]  # thứ tự lớp lúc train, vd ['looking_around', 'no_cheating', 'phone_use']
_classifier = timm.create_model(_checkpoint["model_name"], pretrained=False, num_classes=len(_class_names))
_classifier.load_state_dict(_checkpoint["model_state"])
_classifier.to(DEVICE)
_classifier.eval()

_val_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def _expand_and_clip(xmin, ymin, xmax, ymax, img_w, img_h, expand_ratio):
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    box_w = (xmax - xmin) * (1 + expand_ratio)
    box_h = (ymax - ymin) * (1 + expand_ratio)
    return (
        max(0, int(cx - box_w / 2)),
        max(0, int(cy - box_h / 2)),
        min(img_w, int(cx + box_w / 2)),
        min(img_h, int(cy + box_h / 2)),
    )


def detect_cheating(image_path):
    """
    Trả về list dict: [{"bbox": [xmin,ymin,xmax,ymax], "behaviour": "...", "confidence": 0.95}, ...]
    """
    image = Image.open(image_path).convert("RGB")
    img_w, img_h = image.size

    results = _yolo_model.predict(image_path, conf=CONF_THRESHOLD_PERSON, classes=[0], verbose=False)[0]

    detections = []
    for box in results.boxes:
        xmin, ymin, xmax, ymax = box.xyxy[0].tolist()
        xmin_e, ymin_e, xmax_e, ymax_e = _expand_and_clip(xmin, ymin, xmax, ymax, img_w, img_h, EXPAND_RATIO)
        if xmax_e <= xmin_e or ymax_e <= ymin_e:
            continue

        crop = image.crop((xmin_e, ymin_e, xmax_e, ymax_e))
        tensor = _val_tf(crop).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            probs = torch.softmax(_classifier(tensor), dim=1)[0]
            pred_idx = int(probs.argmax())

        
        detections.append({
            "bbox": [xmin_e, ymin_e, xmax_e, ymax_e],
            "behaviour": _class_names[pred_idx],
            "confidence": round(float(probs[pred_idx]), 4),
        })

    return detections