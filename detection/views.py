import os
import io
import tempfile
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.text import get_valid_filename
from PIL import Image
from .models import Session, Detection
from .ai_inference import detect_cheating

DEFAULT_THRESHOLD = 0.25


def _parse_threshold(raw_value):
    try:
        value = float(raw_value)
        return min(max(value, 0.0), 1.0)
    except (TypeError, ValueError):
        return DEFAULT_THRESHOLD


def _save_detections(session, results, original_image, threshold):
    saved = []
    for r in results:
        if r["confidence"] < threshold:
            continue

        xmin, ymin, xmax, ymax = r["bbox"]
        detection = Detection.objects.create(
            session=session,
            behaviour=r["behaviour"],
            confidence=r["confidence"],
            bbox_xmin=xmin, bbox_ymin=ymin, bbox_xmax=xmax, bbox_ymax=ymax,
        )
        crop = original_image.crop((xmin, ymin, xmax, ymax))
        buffer = io.BytesIO()
        crop.save(buffer, format="JPEG", quality=90)
        detection.snapshot.save(
            f"session{session.id}_det{detection.id}.jpg",
            ContentFile(buffer.getvalue()),
            save=True,
        )
        saved.append(detection)
    return saved


def dashboard(request):
    session_id = request.GET.get("session_id")
    threshold = _parse_threshold(request.GET.get("threshold", DEFAULT_THRESHOLD))
    session = None
    media_url = None
    media_type = None
    detections = []
    detections_for_overlay = []

    if session_id:
        session = get_object_or_404(Session, id=session_id)
        media_type = session.source_type

        if session.source_type in ("image", "video") and session.source_file_name:
            subfolder = "images" if session.source_type == "image" else "videos"
            media_url = f"{settings.MEDIA_URL}uploads/{subfolder}/{session.source_file_name}"

        detection_qs = session.detections.order_by("-detected_time")
        detections = [
            {
                "no": i + 1,
                "location_file": session.source_file_name or "webcam",
                "behaviour": d.get_behaviour_display(),
                "behaviour_code": d.behaviour,
                "coordinate": f"[{d.bbox_xmin},{d.bbox_xmax},{d.bbox_ymin},{d.bbox_ymax}]",
                "snapshot_url": d.snapshot.url if d.snapshot else "",
                "detected_time_display": timezone.localtime(d.detected_time).strftime("%H:%M:%S %d/%m/%Y"),
                "confidence_display": f"{d.confidence * 100:.1f}%",
            }
            for i, d in enumerate(detection_qs)
        ]

        if media_type == "image":
            detections_for_overlay = [
                {
                    "no": i + 1,
                    "bbox": [d.bbox_xmin, d.bbox_ymin, d.bbox_xmax, d.bbox_ymax],
                    "behaviour": d.get_behaviour_display(),
                    "behaviour_code": d.behaviour,
                }
                for i, d in enumerate(detection_qs)
            ]

    context = {
        "session": session,
        "media_url": media_url,
        "media_type": media_type,
        "detections": detections,
        "detections_for_overlay": detections_for_overlay,
        "confidence_threshold": threshold,
        "iou_threshold": 0.70,
        "total_target": len(detections),
        "fps": 30,
        "runtime": 0.072,
    }
    return render(request, "detection/dashboard.html", context)


def classroom_map(request, session_id=None):
    return render(request, "detection/classroom_map.html")


def upload_image(request):
    if request.method == "POST" and request.FILES.get("image"):
        file = request.FILES["image"]
        safe_name = get_valid_filename(file.name)
        save_dir = os.path.join(settings.MEDIA_ROOT, "uploads", "images")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, safe_name)

        with open(save_path, "wb+") as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        threshold = _parse_threshold(request.POST.get("confidence_threshold"))
        session = Session.objects.create(source_type="image", source_file_name=safe_name)

        results = detect_cheating(save_path)
        original_image = Image.open(save_path).convert("RGB")
        _save_detections(session, results, original_image, threshold)

        return redirect(f"/?session_id={session.id}&threshold={threshold}")

    return redirect("dashboard")


def upload_video(request):
    if request.method == "POST" and request.FILES.get("video"):
        file = request.FILES["video"]
        safe_name = get_valid_filename(file.name)
        save_dir = os.path.join(settings.MEDIA_ROOT, "uploads", "videos")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, safe_name)

        with open(save_path, "wb+") as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        session = Session.objects.create(source_type="video", source_file_name=safe_name)
        return redirect(f"/?session_id={session.id}")

    return redirect("dashboard")


def start_webcam(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    session = Session.objects.create(source_type="webcam")
    return JsonResponse({"session_id": session.id})


def webcam_frame(request):
    if request.method != "POST" or not request.FILES.get("frame"):
        return JsonResponse({"error": "invalid request"}, status=400)

    session_id = request.POST.get("session_id")
    session = get_object_or_404(Session, id=session_id, source_type="webcam")
    threshold = _parse_threshold(request.POST.get("confidence_threshold"))

    frame_file = request.FILES["frame"]
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        for chunk in frame_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        results = detect_cheating(tmp_path)
        original_image = Image.open(tmp_path).convert("RGB")
        saved = _save_detections(session, results, original_image, threshold)
    finally:
        os.remove(tmp_path)

    return JsonResponse({
        "detections": [
            {
                "bbox": [d.bbox_xmin, d.bbox_ymin, d.bbox_xmax, d.bbox_ymax],
                "behaviour": d.get_behaviour_display(),
                "behaviour_code": d.behaviour,
                "confidence_display": f"{d.confidence * 100:.1f}%",
                "detected_time_display": timezone.localtime(d.detected_time).strftime("%H:%M:%S %d/%m/%Y"),
                "snapshot_url": d.snapshot.url if d.snapshot else "",
                "coordinate": f"[{d.bbox_xmin},{d.bbox_xmax},{d.bbox_ymin},{d.bbox_ymax}]",
            }
            for d in saved
        ]
    })


def save_result(request):
    pass


def clear_result(request):
    return redirect("dashboard")