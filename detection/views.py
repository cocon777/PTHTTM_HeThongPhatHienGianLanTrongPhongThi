import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .models import Session, Detection
# from .cloud_storage import upload_to_cloudinary


def dashboard(request):
    """
    Trang chính: vùng video + bảng log + các panel bên phải.
    Nếu có ?session_id=X trên URL -> hiển thị đúng file/kết quả của session đó.
    Nếu không có -> hiển thị dữ liệu mẫu (mock) để demo giao diện.
    """
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

        detection_qs = session.detections.all()
        detections = [
            {
                "no": i + 1,
                "location_file": session.source_file_name or "webcam",
                "behaviour": d.get_behaviour_display(),
                "coordinate": f"[{d.bbox_xmin},{d.bbox_xmax},{d.bbox_ymin},{d.bbox_ymax}]",
            }
            for i, d in enumerate(detection_qs)
        ]
    else:
        # ------ MOCK DATA (chỉ hiện khi chưa upload gì, để demo giao diện) ------
        detections = [
            {"no": 1, "location_file": "D:/Downloads/Rob_Wolf.mp4", "behaviour": "Cheating", "coordinate": "[1236,1512,341,765]"},
            {"no": 2, "location_file": "D:/Downloads/Rob_Wolf.mp4", "behaviour": "Cheating", "coordinate": "[146,112,341,765]"},
            {"no": 3, "location_file": "D:/Downloads/Rob_Wolf.mp4", "behaviour": "Normal", "coordinate": "[236,412,361,876]"},
            {"no": 4, "location_file": "D:/Downloads/Rob_Wolf.mp4", "behaviour": "Normal", "coordinate": "[479,617,381,576]"},
            {"no": 5, "location_file": "D:/Downloads/Rob_Wolf.mp4", "behaviour": "Looking around", "coordinate": "[579,457,241,719]"},
        ]

    context = {
        "session": session,
        "media_url": media_url,
        "media_type": media_type,
        "detections": detections,
        "confidence_threshold": 0.25,
        "iou_threshold": 0.70,
        "total_target": len(detections),
        "fps": 30,
        "runtime": 0.072,
        "current_behavior": "Looking Around",
        "current_confidence": 95,
        "bbox": {"xmin": 1236, "ymin": 341, "xmax": 1512, "ymax": 765},
    }
    return render(request, 'detection/dashboard.html', context)


def classroom_map(request, session_id=None):
    # 🔸 PLACEHOLDER — giữ nguyên, làm ở giai đoạn sau
    return render(request, 'detection/classroom_map.html')


def upload_image(request):
    """Nhận ảnh upload, lưu vào media/uploads/images/, tạo Session mới."""
    if request.method == 'POST' and request.FILES.get('image'):
        file = request.FILES['image']
        save_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'images')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file.name)

        with open(save_path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        session = Session.objects.create(
            source_type='image',
            source_file_name=file.name,
        )

        # TODO (người AI): gọi detect_cheating(save_path) ở đây,
        # rồi lưu từng kết quả vào Detection.objects.create(session=session, ...)

        return redirect(f"/?session_id={session.id}")

    return redirect('dashboard')


def upload_video(request):
    """Nhận video upload, lưu vào media/uploads/videos/, tạo Session mới."""
    if request.method == 'POST' and request.FILES.get('video'):
        file = request.FILES['video']
        save_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'videos')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file.name)

        with open(save_path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        session = Session.objects.create(
            source_type='video',
            source_file_name=file.name,
        )

        # TODO (người AI): xử lý video frame-by-frame bằng detect_cheating(),
        # lưu từng kết quả vào Detection.objects.create(session=session, ...)

        return redirect(f"/?session_id={session.id}")

    return redirect('dashboard')


def start_webcam(request):
    # 🔸 PLACEHOLDER — hiện tại webcam/IP camera chỉ hiển thị preview bằng JS
    # phía trình duyệt (xem dashboard.html), CHƯA gửi frame về backend để chạy AI.
    # Sẽ hoàn thiện ở giai đoạn tích hợp AI real-time (cần thêm AJAX/WebSocket).
    pass


def save_result(request):
    # TODO: đẩy video/ảnh kết quả lên Cloudinary, lưu link vào Session.cloud_url
    # 🔸 Tạm thời chưa làm — sẽ tích hợp ở giai đoạn sau khi các phần khác ổn định
    pass

# def save_result(request):
#     """Upload file hiện tại lên Cloudinary, lưu link vào Session.cloud_url."""
#     if request.method == 'POST':
#         session_id = request.POST.get('session_id')
#         if not session_id:
#             return redirect('dashboard')

#         session = get_object_or_404(Session, id=session_id)

#         if session.source_type in ('image', 'video') and session.source_file_name:
#             subfolder = 'images' if session.source_type == 'image' else 'videos'
#             file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', subfolder, session.source_file_name)

#             cloud_url = upload_to_cloudinary(file_path)
#             if cloud_url:
#                 session.cloud_url = cloud_url
#                 session.save()

#         return redirect(f"/?session_id={session.id}")

#     return redirect('dashboard')


def clear_result(request):
    """Chỉ bỏ hiển thị hiện tại (quay về dashboard trống), KHÔNG xóa lịch sử trong DB."""
    return redirect('dashboard')