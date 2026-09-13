from django.contrib import admin
from .models import Session, Detection


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_type', 'source_file_name', 'room_name', 'created_at')


@admin.register(Detection)
class DetectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'behaviour', 'confidence', 'detected_time')
    list_filter = ('behaviour',)