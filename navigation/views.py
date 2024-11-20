from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import RoadStructure
from .function import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from backend.settings import TMAP
import requests
import os


class FindRouteView(APIView):
    @swagger_auto_schema(
        operation_summary="경로 탐색 요청",
        operation_description="Find route to the destination",
        manual_parameters=[
            openapi.Parameter(
                "startX",
                openapi.IN_QUERY,
                description="출발지 경도",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "startY",
                openapi.IN_QUERY,
                description="출발지 위도",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "endX",
                openapi.IN_QUERY,
                description="목적지 경도",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "endY",
                openapi.IN_QUERY,
                description="목적지 위도",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: "OK",
            400: "Invalid input arguments",
            404: "Route not found",
        },
    )
    def get(self, request, *args, **kwargs):
        startX = request.data.get("startX")
        startY = request.data.get("startY")
        endX = request.data.get("endX")
        endY = request.data.get("endY")
        if not all([startX, startY, endX, endY]):
            return Response(
                {"error": "Invalid input arguments"}, status=status.HTTP_400_BAD_REQUEST
            )

        route = self.find_route(startX, startY, endX, endY)
        if not route:
            return Response(
                {"error": "Route not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(route, status=status.HTTP_200_OK)

    def find_route(self, startX, startY, endX, endY):
        # 출발지와 목적지 좌표
        start = (startX, startY)
        end = (endX, endY)

        # PostgreSQL에서 후보 좌표들 가져오기
        locations = RoadStructure.objects.all()  # 전체 좌표를 가져옴
        candidates = [
            (loc.longitude, loc.latitude, loc.weight) for loc in locations
        ]  # safety_score는 weight에 해당

        # 출발점과 목적점을 포함하는 일정 크기의 원 내에서 경유지 후보 필터링
        midpoint, radius = calculate_midpoint_and_circle(start, end)
        filtered_candidates = points_within_circle(candidates, midpoint, radius)
        optimal_filtered_candidates = select_highest_safety_points(filtered_candidates)

        # 최적 경로 계산
        optimal_route = find_optimal_route(
            start, end, optimal_filtered_candidates, alpha=1.5
        )
        return optimal_route


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
            latitude = request.data["latitude"]
            longitude = request.data["longitude"]
        except KeyError:
            return Response(
                {"error": "Invalid input arguments"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 이미 존재하는 구조물이면 DB 업데이트(weight 증가), 없으면 새로 추가
        road_structure = RoadStructure.objects.filter(
            latitude=latitude, longitude=longitude
        )
        if road_structure.exists():
            road_structure.weight += 0.5
            road_structure.save()
        else:
            RoadStructure.objects.create(
                latitude=latitude, longitude=longitude, weight=0.5
            )

        return Response(status=status.HTTP_200_OK)
