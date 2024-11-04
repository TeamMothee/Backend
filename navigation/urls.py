from django.urls import path
from .views import FindPathView, ReportView

app_name = "navigation"

urlpatterns = [
    path("find_path/", FindPathView.as_view(), name="find_path"),
    path("report/", ReportView.as_view(), name="navigate"),
]
