"""
🔸 PLACEHOLDER — file này dành cho người phụ trách AI.
Sau khi train xong model (person detector + behavior classifier),
copy file .pt vào thư mục weights/ và implement hàm bên dưới.

Hàm này PHẢI trả về list dict theo đúng format:
[
    {"bbox": [xmin, ymin, xmax, ymax], "behaviour": "phone_use", "confidence": 0.95},
    ...
]
để views.py có thể lưu thẳng vào model Detection mà không cần sửa gì thêm.
"""

def detect_cheating(image_path):
    # TODO: load model YOLO/EfficientNet, chạy predict, trả kết quả đúng format trên
    raise NotImplementedError("Chưa tích hợp model AI")