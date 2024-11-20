from django.urls import path
from .views import FindPathView, CallTmapView, PedestrianRouteView, ReportView

app_name = "navigation"

urlpatterns = [
    path("find_path/", FindPathView.as_view(), name="find_path"),
    path("call_tmap/", CallTmapView.as_view(), name="call_tmap"),
    path("pedestrian-route/", PedestrianRouteView.as_view(), name="pedestrian-route"),
    path("report/", ReportView.as_view(), name = "report")
]
