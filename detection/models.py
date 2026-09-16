from django.db import models


class Session(models.Model):
    SOURCE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('webcam', 'Webcam'),
    ]

    source_type = models.CharField(max_length=10, choices=SOURCE_TYPE_CHOICES, default='image')
    source_file_name = models.CharField(max_length=255, blank=True)
    cloud_url = models.URLField(blank=True, null=True)
    room_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session #{self.id} - {self.source_file_name}"


class Detection(models.Model):
    BEHAVIOR_CHOICES = [
        ('looking_around', 'Looking around'),
        ('no_cheating', 'No cheating'),
        ('phone_use', 'Phone use'),
    ]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='detections')
    behaviour = models.CharField(max_length=30, choices=BEHAVIOR_CHOICES)
    confidence = models.FloatField(default=0.0)

    bbox_xmin = models.IntegerField()
    bbox_ymin = models.IntegerField()
    bbox_xmax = models.IntegerField()
    bbox_ymax = models.IntegerField()

    seat_label = models.CharField(max_length=20, blank=True, null=True)

    # 🆕 Ảnh crop chụp lại đúng lúc phát hiện - dùng cho popup "Xem chi tiết"
    snapshot = models.ImageField(upload_to='detections/', blank=True, null=True)

    detected_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_behaviour_display()} - Session #{self.session_id}"