from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Detection, RoadStructure
from .function import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from backend.settings import TMAP
import requests
import os

class FindPathView(APIView):
    @swagger_auto_schema(
        operation_summary="경로 탐색 요청",
        operation_description="Find the path to the destination",
        manual_parameters=[
            openapi.Parameter(
                "origin",
                openapi.IN_QUERY,
                description="사용자의 출발지 (경도, 위도 형식)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "destination",
                openapi.IN_QUERY,
                description="사용자의 목적지 (경도, 위도 형식)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: "OK",
            400: "Invalid input arguments",
        },
    )
    def get(self, request, *args, **kwargs):
        # 입력 파라미터 확인
        origin = request.query_params.get("origin")
        destination = request.query_params.get("destination")

        if not origin:
            return Response({"error": "출발지를 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST)
        if not destination:
            return Response({"error": "도착지를 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 출발지 및 도착지 좌표 파싱
            startX, startY = map(float, origin.split(","))
            endX, endY = map(float, destination.split(","))
        except ValueError:
            return Response({"error": "출발지와 도착지는 '경도,위도' 형식으로 입력하세요."}, status=status.HTTP_400_BAD_REQUEST)

        # 경로 탐색 실행
        path = self.find_path(startX, startY, endX, endY)

        if not path:
            return Response({"error": "경로를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        return Response(path, status=status.HTTP_200_OK)

    def find_path(self, startX, startY, endX, endY):
        # 출발지와 목적지 좌표
        start = (startX, startY)
        end = (endX, endY)

        # PostgreSQL에서 후보 좌표들 가져오기
        locations = RoadStructure.objects.all()  # 전체 좌표를 가져옴
        candidates = [(loc.longitude, loc.latitude, loc.weight) for loc in locations]  # weight는 safety_score로 사용

        # 중간점과 반지름 계산
        midpoint, radius = calculate_midpoint_and_circle(start, end)

        # 경유지 후보 필터링
        filtered_candidates = points_within_circle(candidates, midpoint, radius)

        # 안전 점수 기반 최적 경유지 선택
        optimal_filtered_candidates = select_highest_safety_points(filtered_candidates)

        # 최적 경로 계산
        optimal_route_response = find_optimal_route(start, end, optimal_filtered_candidates, alpha=1.5)

        # 경로 계산 결과 반환
        if not optimal_route_response:
            return None

        return optimal_route_response


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


class PedestrianRouteView(APIView):
    @swagger_auto_schema(
        operation_summary="보행자 경로 탐색",
        operation_description="출발지, 목적지, 경유지를 기반으로 보행자 경로를 계산합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "startX": openapi.Schema(type=openapi.TYPE_NUMBER, description="출발지 경도"),
                "startY": openapi.Schema(type=openapi.TYPE_NUMBER, description="출발지 위도"),
                "endX": openapi.Schema(type=openapi.TYPE_NUMBER, description="목적지 경도"),
                "endY": openapi.Schema(type=openapi.TYPE_NUMBER, description="목적지 위도"),
                "passList": openapi.Schema(type=openapi.TYPE_STRING, description="경유지 리스트 (Optional)"),
                "angle": openapi.Schema(type=openapi.TYPE_NUMBER, description="각도 (Optional)", default=0),
                "speed": openapi.Schema(type=openapi.TYPE_NUMBER, description="속도 (Optional)", default=0),
                "endPoiId": openapi.Schema(type=openapi.TYPE_STRING, description="목적지 POI ID (Optional)", default=""),
            },
            required=["startX", "startY", "endX", "endY"]
        ),
        responses={
            200: openapi.Response(
                description="경로 계산 성공",
                examples={
                    "application/json": {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [126.92365493654832, 37.556770374096615]
                                },
                                "properties": {
                                    "totalDistance": 1000,
                                    "totalTime": 600,
                                    "description": "경로 설명"
                                }
                            }
                        ]
                    }
                }
            ),
            400: "잘못된 요청입니다. (출발지와 목적지를 입력하세요.)",
            500: "서버 내부 오류"
        }
    )
    def post(self, request, *args, **kwargs):
        # 요청 데이터 가져오기
        startX = request.data.get("startX")
        startY = request.data.get("startY")
        endX = request.data.get("endX")
        endY = request.data.get("endY")

        # 필수 데이터 검증
        if not all([startX, startY, endX, endY]):
            return Response({"error": "출발지와 목적지를 입력하세요."}, status=status.HTTP_400_BAD_REQUEST)

        # 출발지와 목적지 좌표
        start = (startX, startY)
        end = (endX, endY)

        # PostgreSQL에서 후보 좌표들 가져오기 (예시로 Location 테이블에서 가져옴)
        locations = RoadStructure.objects.all()  # 전체 좌표를 가져옴
        candidates = [(loc.longitude, loc.latitude, loc.weight) for loc in locations]  # safety_score는 weight에 해당

        # 출발점과 목적점 사이의 원 내에서 경유지 후보 필터링
        midpoint, radius = calculate_midpoint_and_circle(start, end)
        filtered_candidates = points_within_circle(candidates, midpoint, radius)
        optimal_filtered_candidates=select_highest_safety_points(filtered_candidates)

        optimal_route_response = find_optimal_route(start, end, optimal_filtered_candidates, alpha=1.5)

        if not optimal_route_response:
            return Response({"error": "최적 경로를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # TMap API 응답 그대로 반환
        return Response(optimal_route_response, status=status.HTTP_200_OK)