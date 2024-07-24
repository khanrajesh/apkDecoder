from django.urls import path

from apkmanager.view import UploadAPKView, APKInfoView

urlpatterns = [
    path('upload/', UploadAPKView.as_view(), name='upload_apk'),
    path('apk-info/<str:package_name>/', APKInfoView.as_view(), name='apk_info'),
]
