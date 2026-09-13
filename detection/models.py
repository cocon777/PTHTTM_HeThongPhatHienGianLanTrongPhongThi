from django.db import models


class Session(models.Model):
    """
    Đại diện cho 1 lần xử lý: 1 ảnh, 1 video, hoặc 1 phiên webcam.
    """
    SOURCE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('webcam', 'Webcam'),
    ]

    source_type = models.CharField(max_length=10, choices=SOURCE_TYPE_CHOICES, default='image')
    source_file_name = models.CharField(max_length=255, blank=True)  # tên file gốc, VD: Rob_Wolf.mp4

    # 🔸 Sẽ dùng để lưu link Cloudinary sau khi tích hợp (giai đoạn sau)
    cloud_url = models.URLField(blank=True, null=True)

    room_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session #{self.id} - {self.source_file_name}"


class Detection(models.Model):
    """
    Mỗi dòng = 1 người được phát hiện trong 1 session,
    khớp với các cột trong bảng log trên giao diện:
    No | Location File | Behaviour | Coordinate
    """
    BEHAVIOR_CHOICES = [
        ('looking_around', 'Looking around'),
        ('no_cheating', 'Normal'),
        ('phone_use', 'Cheating'),
    ]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='detections')
    behaviour = models.CharField(max_length=30, choices=BEHAVIOR_CHOICES)
    confidence = models.FloatField(default=0.0)  # % độ tin cậy, hiển thị ở "Behavior Analysis"

    # Tọa độ bounding box (theo pixel, giống ảnh minh họa: xmin, ymin, xmax, ymax)
    bbox_xmin = models.IntegerField()
    bbox_ymin = models.IntegerField()
    bbox_xmax = models.IntegerField()
    bbox_ymax = models.IntegerField()

    # 🔸 Dùng cho tính năng "sơ đồ lớp" sau này (giai đoạn sau, chưa cần điền)
    seat_label = models.CharField(max_length=20, blank=True, null=True)

    detected_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_behaviour_display()} - Session #{self.session_id}"