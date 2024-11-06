from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Detection, RoadStructure
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from backend.settings import TMAP
import requests


# Create your views here.
class FindPathView(APIView):
    @swagger_auto_schema(
        operation_summary="경로 탐색 요청",
        operation_description="Find the path to the destination",
        manual_parameters=[
            openapi.Parameter(
                "origin",
                openapi.IN_QUERY,
                description="사용자의 출발지",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "destination",
                openapi.IN_QUERY,
                description="사용자의 목적지",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: "OK",
            400: "Invalid input arguments",
        },
    )
    def get(self, request, *args, **kwargs):
        origin = request.query_params.get("origin")
        if not origin:
            Response(
                {"error": "출발지를 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST
            )
        destination = request.query_params.get("destination")
        if not destination:
            Response(
                {"error": "도착지를 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST
            )

        # path = find_path(destination)  # TODO: route finding algorithm
        path = {  # 임시로 작성함
            "origin": origin,
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
        road_structure = {  # 임시로 작성함
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


class CallTmapView(APIView):
    @swagger_auto_schema(
        operation_summary="Tmap API 호출",
        operation_description="Call Tmap API",
        responses={
            200: "OK",
        },
    )
    def get(self, request, *args, **kwargs):
        url = TMAP["API_URL"]
        headers = {
            "appKey": TMAP["APP_KEY"],
            "Accept-Language": "ko",
            "Content-Type": "application/json",
        }
        payload = {
            "startX": 126.92365493654832,
            "startY": 37.556770374096615,
            "angle": 20,
            "speed": 30,
            "endPoiId": "10001",
            "endX": 126.92432158129688,
            "endY": 37.55279861528311,
            "passList": "126.92774822,37.55395475_126.92577620,37.55337145",
            "reqCoordType": "WGS84GEO",
            "startName": "%EC%B6%9C%EB%B0%9C",
            "endName": "%EB%8F%84%EC%B0%A9",
            "searchOption": "0",
            "resCoordType": "WGS84GEO",
            "sort": "index",
        }
        response = requests.post(url, headers=headers, json=payload).json()
        print(response)
        return Response(status=status.HTTP_200_OK)
