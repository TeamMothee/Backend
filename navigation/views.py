from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Detection, RoadStructure
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# Create your views here.
class FindPathView(APIView):
    @swagger_auto_schema(
        operation_summary="경로 탐색 요청",
        operation_description="Find the path to the destination",
        manual_parameters=[
            openapi.Parameter(
                "destination",
                openapi.IN_QUERY,
                description="사용자의 목적지",
                type=openapi.TYPE_STRING,
            )
        ],
        responses={
            200: "OK",
        },
    )
    def get(self, request, *args, **kwargs):
        destination = request.GET.get("destination")
        # path = find_path(destination)  # TODO: route finding algorithm
        path = {
            "destination": destination,
            "path": "찾은 경로",
        }
        return Response(path, status=status.HTTP_200_OK)


class ReportView(APIView):
    @swagger_auto_schema(
        operation_summary="위험 구조물 제보",
        operation_description="Report a dangerous structure",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "image": openapi.Schema(type=openapi.TYPE_STRING),
                "latitude": openapi.Schema(type=openapi.TYPE_NUMBER),
                "longitude": openapi.Schema(type=openapi.TYPE_NUMBER),
            },
        ),
        responses={
            200: "OK",
            400: "Invalid input arguments",
        },
    )
    def patch(self, request, *args, **kwargs):
        try:
            image = request.data["image"]
            latitude = request.data["latitude"]
            longitude = request.data["longitude"]
        except KeyError:
            return Response(
                {"error": "Invalid input arguments"}, status=status.HTTP_400_BAD_REQUEST
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
