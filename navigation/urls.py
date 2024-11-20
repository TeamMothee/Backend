from django.urls import path
from .views import FindRouteView, ReportView

app_name = "navigation"

urlpatterns = [
    path("find_path/", FindRouteView.as_view(), name="find_path"),
    path("report/", ReportView.as_view(), name="report"),
]
