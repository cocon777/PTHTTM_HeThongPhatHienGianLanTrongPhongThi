import os
import io
from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from PIL import Image
from .models import Session, Detection
from .ai_inference import detect_cheating
from django.utils import timezone
from django.utils.text import get_valid_filename
# from .cloud_storage import upload_to_cloudinary


def dashboard(request):
    session_id = request.GET.get('session_id')
    session = None
    media_url = None
    media_type = None
    detections = []

    if session_id:
        session = get_object_or_404(Session, id=session_id)
        media_type = session.source_type

        if session.source_type in ('image', 'video') and session.source_file_name:
            subfolder = 'images' if session.source_type == 'image' else 'videos'
            media_url = f"{settings.MEDIA_URL}uploads/{subfolder}/{session.source_file_name}"

        # 🆕 Mới nhất lên đầu danh sách
        detection_qs = session.detections.order_by('-detected_time')
        detections = [
            {
                "no": i + 1,
                "location_file": session.source_file_name or "webcam",
                "behaviour": d.get_behaviour_display(),   # tên hiển thị: "Phone use", "No cheating", "Looking around"
                "behaviour_code": d.behaviour,              # mã gốc: "phone_use", "no_cheating", "looking_around" -> dùng để tô màu
                "coordinate": f"[{d.bbox_xmin},{d.bbox_xmax},{d.bbox_ymin},{d.bbox_ymax}]",
                "snapshot_url": d.snapshot.url if d.snapshot else "",
                "detected_time_display": timezone.localtime(d.detected_time).strftime("%H:%M:%S %d/%m/%Y"),
                "confidence_display": f"{d.confidence * 100:.1f}%",
            }
            for i, d in enumerate(detection_qs)
        ]
        # Dữ liệu riêng cho bbox overlay vẽ đè lên ảnh chính — chỉ cần khi là ảnh
        detections_for_overlay = []
        if media_type == 'image':
            detections_for_overlay = [
                {
                    "bbox": [d.bbox_xmin, d.bbox_ymin, d.bbox_xmax, d.bbox_ymax],
                    "behaviour": d.get_behaviour_display(),
                    "behaviour_code": d.behaviour,
                }
                for d in detection_qs
            ]
    else:
        detections = [
            {"no": 1, "location_file": "D:/Downloads/Rob_Wolf.mp4", "behaviour": "Phone use", "behaviour_code": "phone_use",
             "coordinate": "[1236,1512,341,765]", "snapshot_url": "", "detected_time_display": "—", "confidence_display": "—"},
            {"no": 2, "location_file": "D:/Downloads/Rob_Wolf.mp4", "behaviour": "No cheating", "behaviour_code": "no_cheating",
             "coordinate": "[236,412,361,876]", "snapshot_url": "", "detected_time_display": "—", "confidence_display": "—"},
        ]
        detections_for_overlay = []

    context = {
        "session": session,
        "media_url": media_url,
        "media_type": media_type,
        "detections": detections,
        "detections_for_overlay": detections_for_overlay,
        "confidence_threshold": 0.25,
        "iou_threshold": 0.70,
        "total_target": len(detections),
        "fps": 30,
        "runtime": 0.072,
    }
    return render(request, 'detection/dashboard.html', context)


def classroom_map(request, session_id=None):
    return render(request, 'detection/classroom_map.html')


def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        file = request.FILES['image']
        safe_name = get_valid_filename(file.name)  # 🆕 làm sạch tên file
        save_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'images')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, safe_name)

        with open(save_path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        session = Session.objects.create(
            source_type='image',
            source_file_name=safe_name,  # 🆕 lưu tên đã làm sạch
        )

        results = detect_cheating(save_path)
        original_image = Image.open(save_path).convert("RGB")

        for r in results:
            xmin, ymin, xmax, ymax = r["bbox"]
            detection = Detection.objects.create(
                session=session,
                behaviour=r["behaviour"],
                confidence=r["confidence"],
                bbox_xmin=xmin, bbox_ymin=ymin, bbox_xmax=xmax, bbox_ymax=ymax,
            )
            crop = original_image.crop((xmin, ymin, xmax, ymax))
            buffer = io.BytesIO()
            crop.save(buffer, format='JPEG', quality=90)
            detection.snapshot.save(
                f"session{session.id}_det{detection.id}.jpg",
                ContentFile(buffer.getvalue()),
                save=True,
            )

        return redirect(f"/?session_id={session.id}")

    return redirect('dashboard')


def upload_video(request):
    # 🔸 Video xử lý frame-by-frame để sau, hôm nay chỉ làm luồng ảnh
    if request.method == 'POST' and request.FILES.get('video'):
        file = request.FILES['video']
        save_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'videos')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file.name)

        with open(save_path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        session = Session.objects.create(source_type='video', source_file_name=file.name)
        return redirect(f"/?session_id={session.id}")

    return redirect('dashboard')


def start_webcam(request):
    pass


def save_result(request):
    pass


def clear_result(request):
    return redirect('dashboard')