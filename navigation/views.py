from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Detection, RoadStructure


# Create your views here.
class FindPathView(APIView):
    def get(self, request, *args, **kwargs):
        destination = request.GET.get("destination")
        # path = find_path(destination)  # TODO: route finding algorithm
        path = {
            "destination": destination,
            "path": "찾은 경로",
        }
        return Response(path, status=status.HTTP_200_OK)


class NavigateView(APIView):
    def patch(self, request, *args, **kwargs):
        try:
            image = request.data["image"]
            latitude = request.data["latitude"]
            longitude = request.data["longitude"]
        except KeyError:
            return Response(
                {"error": "Invalid arguments"}, status=status.HTTP_400_BAD_REQUEST
            )
        Detection.create_table(image, latitude, longitude)
        # AI 모델로 위험 구조물 탐지
        # road_structure = detect_danger(image)
        road_structure = {
            "braille_block": 0,
            "audio_signal": 1,
            "bollard": 2,
            "weight": 10,
            "latitude": latitude,
            "longitude": longitude,
        }
        RoadStructure.create_table(**road_structure)
        Detection.delete_table(latitude, longitude)

        return Response(status=status.HTTP_200_OK)
