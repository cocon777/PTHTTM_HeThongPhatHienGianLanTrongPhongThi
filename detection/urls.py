from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('classroom-map/', views.classroom_map, name='classroom_map'),

    # 🔸 Các route placeholder — chưa xử lý logic thật
    path('upload/image/', views.upload_image, name='upload_image'),
    path('upload/video/', views.upload_video, name='upload_video'),
    path('webcam/start/', views.start_webcam, name='start_webcam'),
    path('save/', views.save_result, name='save_result'),
    path('clear/', views.clear_result, name='clear_result'),
]