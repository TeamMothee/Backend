from django.urls import path
from .views import FindRouteView, ReportView, CallImageCaptionView

app_name = "navigation"

urlpatterns = [
    path("find_path/", FindRouteView.as_view(), name="find_path"),
    path("report/", ReportView.as_view(), name="report"),
    path("call_image_caption/", CallImageCaptionView.as_view(), name="call_image_caption"),
]
